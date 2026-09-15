"""generate_pending 契約測試（AIR-63 S1/S5——pending 讀取覆層生成器）。

釘住的 invariant：
- 三層語義固定優先序 canonical > pending——輸出必帶優先序文字，pending 永不冒充 canonical。
- 生命週期收斂：候選只從 inbox new（root *.json／new/*.json）＋processing 掃描；
  done/rejected 不掃——條目離開待治理區後重跑，pending 該條必然消失（ghost 零容忍）。
- context tax bound：excerpt 前 300 字＋單檔 4K 上限，超量只列條目不貼文。
- crash semantics：候選損壞＝fail loud 不發布；既有視圖可 stale（本身標 provisional）、
  禁 falsely canonical。
- 確定性：同 inbox＋池狀態 → 同 bytes（禁牆鐘入輸出）。
- 禁碰 MEMORY.md／_inventory.md（`_` 前綴檔不進正式索引由池 generator 既有遍歷保證）。

Fixture 一律 tmp_path（測試自帶 fake pool＋fake inbox——路徑參數可注入）。
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("skills/memory-audit/scripts/generate_pending.py")
SCRIPT = REPO_ROOT / "skills" / "memory-audit" / "scripts" / "generate_pending.py"


# ---- fixture builders ----


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed(repo: Path) -> tuple[Path, Path]:
    """fake 池（含 sentinel MEMORY.md/_inventory.md＋一筆 canonical）＋fake inbox。"""
    pool = repo / ".agents" / "memory"
    inbox = repo / ".agents" / "memory-inbox"
    pool.mkdir(parents=True)
    inbox.mkdir(parents=True)
    (pool / "MEMORY.md").write_text("SENTINEL-MEMORY\n", encoding="utf-8")
    (pool / "_inventory.md").write_text("SENTINEL-INVENTORY\n", encoding="utf-8")
    (pool / "entry-a.md").write_text(
        "---\nname: entry-a\ndescription: canonical body v1\ntype: feedback\n---\nbody v1\n",
        encoding="utf-8",
    )
    return pool, inbox


def _payload(
    operation: str = "add_memory",
    path: str = "new-entry.md",
    content: str = "candidate body",
    base_sha: str | None = None,
    base_path: str | None = None,
) -> dict:
    tool_input: dict = {"scope": "project", "path": path}
    if operation == "edit_memory":
        tool_input |= {"old_str": "old text", "new_str": content}
    else:
        tool_input["content"] = content
    p: dict = {
        "hook_event_name": "PreToolUse",
        "tool_name": operation,
        "tool_input": tool_input,
        "session_id": "sess-fixture",
    }
    if base_sha is not None:
        p["_inbox_meta"] = {
            "base_path": base_path if base_path is not None else path,
            "base_sha256": base_sha,
        }
    return p


_SUBDIR = {
    "new-sub": "new",
    "processing": "processing",
    "done": "done",
    "rejected": "rejected",
}


def _drop(inbox: Path, name: str, payload: dict, state: str = "new") -> Path:
    sub = _SUBDIR.get(state)
    d = inbox / sub if sub else inbox
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    f.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return f


def _run_generate(pool: Path, inbox: Path) -> str:
    _mod.generate(pool=pool, inbox=inbox)
    return (pool / _mod.PENDING_NAME).read_text(encoding="utf-8")


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


# ---- markings：edit vs add 標記正確 ----


def test_markings_edit_vs_add(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload("edit_memory", "entry-a.md"))
    _drop(inbox, "20260914-100001-2-bbb.json", _payload("add_memory", "fresh.md"))
    out = _run_generate(pool, inbox)
    assert "### ⚠ Pending correction to canonical — entry-a.md" in out
    assert "### Pending candidate — fresh.md" in out


def test_priority_text_present(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload())
    out = _run_generate(pool, inbox)
    assert "canonical > pending" in out
    assert "canonical 仍為 Y" in out
    assert "不得據" in out


# ---- ghost lifecycle：done/rejected 後 pending 消失 ----


def test_ghost_lifecycle_entry_moved_to_done_disappears(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    f = _drop(
        inbox, "20260914-100000-1-aaa.json", _payload("edit_memory", "entry-a.md")
    )
    out = _run_generate(pool, inbox)
    assert "entry-a.md" in out
    done = inbox / "done"
    done.mkdir()
    f.rename(done / f.name)
    out2 = _run_generate(pool, inbox)
    assert "entry-a.md" not in out2
    assert "候選數：0" in out2


def test_done_and_rejected_not_scanned(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    for state in ("done", "rejected"):
        _drop(
            inbox,
            f"20260914-100000-1-{state}.json",
            _payload(path=f"{state}.md"),
            state,
        )
    out = _run_generate(pool, inbox)
    assert "候選數：0" in out


# ---- excerpt bound：300 字截斷＋4K 單檔上限只列條目 ----


def test_excerpt_truncated_at_300_chars(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    long_body = "x" * 400 + "TAILMARK"
    _drop(inbox, "20260914-100000-1-aaa.json", _payload(content=long_body))
    out = _run_generate(pool, inbox)
    assert "x" * 300 in out
    assert "TAILMARK" not in out
    assert "截斷" in out


def test_short_content_not_truncated(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload(content="short body 完整在場"))
    out = _run_generate(pool, inbox)
    assert "short body 完整在場" in out
    assert "截斷" not in out


def test_file_char_limit_compact_lists_entries_only(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    for i in range(10):
        body = f"UNIQUE-BODY-{i}-" + "y" * 300
        _drop(inbox, f"20260914-1000{i:02d}-{i}-h{i}.json", _payload(content=body))
    out = _run_generate(pool, inbox)
    assert len(out) <= _mod.FILE_CHAR_LIMIT
    assert "UNIQUE-BODY-0-" not in out  # 條目模式不貼 excerpt
    assert "候選數：10" in out
    assert _mod.MARK_EDIT in out or _mod.MARK_ADD in out  # 標記仍隨條目列在場


# ---- 同一 target 多 edits：順序展示語義 ----


def test_same_target_multiple_edits_shown_in_intercept_order(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(
        inbox,
        "20260914-100000-1-aaa.json",
        _payload("edit_memory", "entry-a.md", "first"),
    )
    _drop(
        inbox,
        "20260914-110000-2-bbb.json",
        _payload("edit_memory", "entry-a.md", "second"),
    )
    out = _run_generate(pool, inbox)
    assert "同一目標多筆" in out
    first = out.index("20260914-100000")
    second = out.index("20260914-110000")
    assert first < second
    multi = out.index("同一目標多筆")
    seq1 = out.index("1. 20260914-100000", multi)
    seq2 = out.index("2. 20260914-110000", multi)
    assert seq1 < seq2
    assert "依攔截順序" in out


# ---- 原子寫：無殘檔；aged tmp 清、in-flight tmp 不誤殺 ----


def test_atomic_write_cleans_aged_tmp_keeps_inflight(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload())
    aged = pool / f"{_mod.PENDING_NAME}.111.tmp"
    aged.write_text("stale\n", encoding="utf-8")
    os.utime(aged, (time.time() - 3600, time.time() - 3600))
    inflight = pool / f"{_mod.PENDING_NAME}.999999.tmp"
    inflight.write_text("in-flight\n", encoding="utf-8")
    _run_generate(pool, inbox)
    assert not aged.exists()
    assert inflight.exists()
    assert not list(pool.glob(f"{_mod.PENDING_NAME}.*.tmp")) or inflight.exists()


# ---- 零碰 MEMORY.md／_inventory.md ----


def test_never_touches_memory_and_inventory(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload())
    _run_generate(pool, inbox)
    assert (pool / "MEMORY.md").read_text(encoding="utf-8") == "SENTINEL-MEMORY\n"
    assert (pool / "_inventory.md").read_text(
        encoding="utf-8"
    ) == "SENTINEL-INVENTORY\n"


# ---- CAS visibility：base 失效＝STALE/conflict ----


def test_cas_current_when_base_matches(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(
        inbox,
        "20260914-100000-1-aaa.json",
        _payload("edit_memory", "entry-a.md", base_sha=_sha(pool / "entry-a.md")),
    )
    out = _run_generate(pool, inbox)
    assert "current" in out


def test_cas_stale_when_canonical_modified(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    base = _sha(pool / "entry-a.md")
    (pool / "entry-a.md").write_text(
        "---\nname: entry-a\ndescription: changed\ntype: feedback\n---\nbody v2\n",
        encoding="utf-8",
    )
    _drop(
        inbox,
        "20260914-100000-1-aaa.json",
        _payload("edit_memory", "entry-a.md", base_sha=base),
    )
    out = _run_generate(pool, inbox)
    assert "STALE" in out
    assert "conflict" in out


def test_cas_stale_when_canonical_deleted(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    base = _sha(pool / "entry-a.md")
    (pool / "entry-a.md").unlink()
    _drop(
        inbox,
        "20260914-100000-1-aaa.json",
        _payload("edit_memory", "entry-a.md", base_sha=base),
    )
    out = _run_generate(pool, inbox)
    assert "STALE" in out
    assert "已不存在" in out


# ---- inbox 狀態面：root＝new、new/ 子目錄＝new、processing＝processing ----


def test_inbox_states_root_new_subdir_and_processing(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-r.json", _payload(path="root.md"))
    _drop(inbox, "20260914-100001-2-n.json", _payload(path="sub.md"), state="new-sub")
    _drop(
        inbox, "20260914-100002-3-p.json", _payload(path="proc.md"), state="processing"
    )
    out = _run_generate(pool, inbox)
    assert "候選數：3（new: 2／processing: 1）" in out
    assert "processing/20260914-100002-3-p.json" in out
    assert "20260914-100001-2-n.json" in out


# ---- crash semantics：malformed 候選 fail loud、不發布、舊視圖保留 ----


def test_malformed_candidate_fails_loud_and_keeps_previous_view(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-ok.json", _payload(path="good.md"))
    first = _run_generate(pool, inbox)
    assert "good.md" in first
    (inbox / "20260914-100001-2-bad.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(_mod.PendingError):
        _mod.generate(pool=pool, inbox=inbox)
    assert (pool / _mod.PENDING_NAME).read_text(encoding="utf-8") == first


def test_non_object_payload_fails_loud(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    (inbox / "20260914-100000-1-arr.json").write_text("[]", encoding="utf-8")
    with pytest.raises(_mod.PendingError):
        _mod.generate(pool=pool, inbox=inbox)


# ---- 確定性：同狀態重跑同 bytes（禁牆鐘入輸出）----


def test_deterministic_rerun_same_bytes(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    _drop(inbox, "20260914-100000-1-aaa.json", _payload("edit_memory", "entry-a.md"))
    _run_generate(pool, inbox)
    b1 = (pool / _mod.PENDING_NAME).read_bytes()
    time.sleep(1.1)
    _run_generate(pool, inbox)
    b2 = (pool / _mod.PENDING_NAME).read_bytes()
    assert b1 == b2


# ---- CLI 契約（消費端＝手動／daily-maintain Phase0，走 exit code）----


def test_cli_ok_and_zero_state(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    done = _run_cli("--pool", str(pool), "--inbox", str(inbox))
    assert done.returncode == 0, done.stderr
    assert "[OK]" in done.stdout
    assert "候選數：0" in (pool / _mod.PENDING_NAME).read_text(encoding="utf-8")


def test_cli_missing_pool_fails_loud(tmp_path: Path) -> None:
    _pool, inbox = _seed(tmp_path / "repo")
    missing = tmp_path / "no-such-pool"
    done = _run_cli("--pool", str(missing), "--inbox", str(inbox))
    assert done.returncode == 1
    assert "[FAIL]" in done.stdout


def test_cli_malformed_candidate_exit_1(tmp_path: Path) -> None:
    pool, inbox = _seed(tmp_path / "repo")
    (inbox / "20260914-100000-1-bad.json").write_text("{oops", encoding="utf-8")
    done = _run_cli("--pool", str(pool), "--inbox", str(inbox))
    assert done.returncode == 1
    assert "20260914-100000-1-bad.json" in done.stdout


def test_cli_default_paths_from_repo_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pool, inbox = _seed(repo)
    _drop(inbox, "20260914-100000-1-aaa.json", _payload(path="root.md"))
    done = _run_cli("--repo-root", str(repo))
    assert done.returncode == 0, done.stderr
    assert "root.md" in (pool / _mod.PENDING_NAME).read_text(encoding="utf-8")
