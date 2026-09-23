"""狀態後綴擋契約測試（AIR-100 S-B——TC-2/3/4；air-90 決策 P3 承接）。

凍結枚舉（air-90 卡 :20，TC-4）：`-pending`／`-inflight`／`-in-flight`／
`-landed`／`-done`／`-closed` 六後綴。規則：**新建**（檔不存在）條目 stem
命中後綴 → exit 2 硬擋；既有條目收斂編輯（含改名退役流程暫時寫入）放行
——S-D 存量處置不被迫走 --no-verify 逃生口。

對應 hook＝hooks/block-memory-index-write.py（suffix 檢查插在 is_entry_file
通過後、desc 檢查前）。crash 面（AC-B7）＝載體 fail-open 語義的特性刻畫
測試——crash 不產生 deny，偵測兜底＝reconcile porcelain delta（detected）。
"""

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import load_module

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block-memory-index-write.py"

SUFFIXES = ["pending", "inflight", "in-flight", "landed", "done", "closed"]


def make_pool(tmp_path):
    pool = tmp_path / "pool"
    pool.mkdir()
    (pool / "_generate_index.py").write_text("# generator stub\n")
    return pool


def _write_payload(
    path: str, desc: str = "觸發詞：一句鉤子", content: str | None = None
) -> str:
    body = (
        content
        if content is not None
        else (f"---\nname: entry\ndescription: {desc}\ntype: project\n---\n\nbody\n")
    )
    return json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": path, "content": body}}
    )


def run_hook(payload: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("sfx", SUFFIXES)
def test_new_entry_with_suffix_blocked(tmp_path, sfx):
    """TC-4 P4-1：六後綴各一 case 全擋（exit 2＋後綴指引）。"""
    pool = make_pool(tmp_path)
    r = run_hook(_write_payload(str(pool / f"entry-{sfx}.md")))
    assert r.returncode == 2, f"suffix -{sfx} not blocked: {r.stderr}"
    assert "弧狀態" in r.stderr
    assert "六問" in r.stderr


def test_valid_new_entry_allowed(tmp_path):
    """TC-3 P3-1 positive control：無後綴合規新建 → exit 0（不得過擋）。"""
    pool = make_pool(tmp_path)
    r = run_hook(_write_payload(str(pool / "entry.md")))
    assert r.returncode == 0, r.stderr


@pytest.mark.parametrize("name", ["done-entry.md", "done-requested.md", "pending.md"])
def test_suffix_requires_trailing_boundary(tmp_path, name):
    """stem 邊界：前綴含 done/pending（非尾碼）不誤傷。"""
    pool = make_pool(tmp_path)
    r = run_hook(_write_payload(str(pool / name)))
    assert r.returncode == 0, f"{name} false-positive: {r.stderr}"


@pytest.mark.parametrize("sfx", ["DONE", "Inflight"])
def test_suffix_case_insensitive_blocked(tmp_path, sfx):
    """F-6：混合/大寫後綴同擋（STEM_SUFFIX_RE 帶 re.IGNORECASE）——`e-DONE.md`
    新建 → exit 2（修前小寫枚舉精確匹配 → 誤放行）。"""
    pool = make_pool(tmp_path)
    r = run_hook(_write_payload(str(pool / f"entry-{sfx}.md")))
    assert r.returncode == 2, f"suffix -{sfx} not blocked: {r.stderr}"
    assert "弧狀態" in r.stderr


def test_existing_entry_with_suffix_edit_allowed(tmp_path):
    """TC-3 P3-2＋「只擋新建」：既有 -inflight 條目收斂覆寫 → exit 0。"""
    pool = make_pool(tmp_path)
    target = pool / "arc-inflight.md"
    target.write_text("---\nname: arc\ndescription: 舊 desc\n---\n\nbody\n")
    r = run_hook(_write_payload(str(target), desc="新 desc：收斂後"))
    assert r.returncode == 0, r.stderr


def test_existing_suffix_file_overwrite_via_write_allowed(tmp_path):
    """F-8：Write 覆寫既有後綴檔（改名退役流程的暫時寫入形）→ exit 0——
    後綴擋只看「檔不存在」（新建），既有檔不受大小寫收緊影響。"""
    pool = make_pool(tmp_path)
    target = pool / "arc-landed.md"
    target.write_text("---\nname: arc\ndescription: 舊 desc\n---\n\nbody\n")
    r = run_hook(_write_payload(str(target), desc="新 desc：退役改名暫存"))
    assert r.returncode == 0, r.stderr


def test_suffix_blocked_before_desc_checks(tmp_path):
    """後綴檔在 desc 檢查前就擋（更上游）——帶違規 desc 的後綴新建報後綴而非 desc。"""
    pool = make_pool(tmp_path)
    r = run_hook(
        _write_payload(
            str(pool / "entry-done.md"),
            desc="x" * 120,
            content="---\nname: e\ndescription: "
            + "x" * 120
            + "\n---\n\n"
            + "y" * 5000,
        )
    )
    assert r.returncode == 2
    assert "弧狀態" in r.stderr
    assert "description" not in r.stderr


class TestCrashPaths:
    """AC-B7（D3 分級記錄）：admission 意圖門；載體 crash 語義 fail-open
    （hook 協定事實，block-memory-index-write.py docstring 自載）＝已知缺口，
    偵測兜底＝reconcile porcelain delta（detected）。本組刻畫現實行為。"""

    def test_malformed_stdin_loud_error(self):
        """非 JSON stdin → exit 1 loud error（非 0 非 2＝CC/ZCode 語義非阻斷）。"""
        r = run_hook("not json {")
        assert r.returncode == 1
        assert "parse error" in r.stderr

    def test_stem_crash_does_not_deny(self, monkeypatch, tmp_path):
        """Path.stem 注入 crash → 不產生 exit 2 deny（例外傳播＝fail-open）。"""
        pool = make_pool(tmp_path)
        mod = load_module("hooks/block-memory-index-write.py")

        def boom(self):
            raise RuntimeError("injected crash")

        monkeypatch.setattr(Path, "stem", property(boom))
        payload = _write_payload(str(pool / "entry-done.md"))
        code = None
        try:
            monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
            mod.main()
            code = 0  # main 正常返回＝放行（main 結尾 sys.exit(0) 不會到，防禦值）
        except SystemExit as exc:
            code = exc.code
        except RuntimeError:
            code = "crash"  # 未捕獲例外→hook runtime 給非 0/2 exit＝非阻斷
        assert code != 2, "crash 面不得偽裝成 deny（fail-open 語義刻畫）"


@pytest.mark.parametrize(
    ("desc", "old", "new", "replace_all", "expected"),
    [
        ("short", "short", "x" * 101, False, 2),
        ("commit token", "token", "47aa89d", False, 2),
        ("reference token", "token", "93715b60a", False, 2),
        ("release 09-DD", "DD", "09", False, 2),
        ("source sess_token", "token", "ABC123", False, 2),
        ("a a", "a", "x" * 50, True, 2),
        ("a a", "a", "x" * 49, True, 0),
        ("short", "short", "x" * 100, False, 0),
        ("x" * 101, "x" * 101, "short", False, 0),
    ],
)
def test_edit_candidate_description(tmp_path, desc, old, new, replace_all, expected):
    """S: accepted H2 validates the final changed description, not replacement fragments."""
    pool = make_pool(tmp_path)
    target = pool / "entry.md"
    original = f"---\nname: entry\ndescription: {desc}\n---\nbody\n"
    target.write_text(original)
    result = run_hook(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(target),
                    "old_string": old,
                    "new_string": new,
                    "replace_all": replace_all,
                },
            }
        )
    )
    assert result.returncode == expected, result.stderr
    if expected == 2:
        assert "description" in result.stderr
    assert target.read_text() == original


@pytest.mark.parametrize("legacy", ["x" * 101, "commit 47aa89d", "09-09 sess_ABC123"])
@pytest.mark.parametrize(
    "kind", ["body", "whole-file", "body-description-example", "shrink"]
)
def test_edit_preserves_legacy_desc_body_allowance(tmp_path, legacy, kind):
    """S: H2 exempts unchanged legacy descriptions and permits oversized body shrinkage."""
    pool = make_pool(tmp_path)
    target = pool / "entry.md"
    body = "body\n"
    if kind == "shrink":
        body = "begin" + "x" * 13_000 + "end"
    original = f"---\nname: entry\ndescription: {legacy}\n---\n{body}"
    target.write_text(original)
    old, new = body, "shorter body\n"
    if kind == "whole-file":
        old, new = original, original.replace(body, new)
    elif kind == "body-description-example":
        new = "description: " + "z" * 101 + "\n"
    result = run_hook(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(target),
                    "old_string": old,
                    "new_string": new,
                },
            }
        )
    )
    assert result.returncode == 0, result.stderr
    assert target.read_text() == original


@pytest.mark.parametrize(
    "edit",
    [
        {"new_string": "updated"},
        {"old_string": "short"},
        {"old_string": "", "new_string": "updated"},
        {"old_string": None, "new_string": "updated"},
        {"old_string": "short", "new_string": None},
        {"old_string": "absent", "new_string": "updated"},
        {"old_string": "short", "new_string": "updated", "replace_all": "false"},
        {"old_string": "short", "new_string": "updated"},
    ],
)
def test_edit_ambiguous_description_is_not_approved(tmp_path, edit):
    """S: H2 conservatively refuses malformed/stale or ambiguous description edits."""
    pool = make_pool(tmp_path)
    target = pool / "entry.md"
    original = "---\ndescription: short\n---\nshort body\n"
    target.write_text(original)
    result = run_hook(
        json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(target),
                    **edit,
                },
            }
        )
    )
    assert result.returncode == 2, result.stderr
    assert "Edit" in result.stderr
    assert target.read_text() == original


if __name__ == "__main__":
    pytest.main([__file__])
