"""marshal admission guard 契約測試（AIR-135.10——AC#6 矩陣；AIR-152 marker 泛化擴充）。

沙箱形態：tmp「canonical repo」內放**拷貝的 hook＋guard＋marker**（self-gate 錨與
guard sibling 隨拷貝落沙箱內——deny 腿得以真實 subprocess 全鏈驗證：
hook → /bin/bash control-plane-guard.sh --match-path），外加 linked
worktree（非 canonical 放行腿）與他 repo（marker absent 腿）。

AIR-152 marker 三態契約：
- wt 級（ai-guide 現行等價）——canonical×控制面命中 deny（原 AC#6 矩陣全保留）
- branch 級——canonical∧branch==trunk∧sourceRoots 命中才 deny（branch 級沙箱）
- malformed——fail-closed deny＋指路修 marker；marker 檔本身恆豁免（修復出口）

deny 輸出契約＝exit 2＋stderr 指路＋stdout hookSpecificOutput JSON 說明；
fail-open 契約＝malformed payload／非轄面工具 → exit 0。
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import load_module

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "marshal_admission_guard.py"
GUARD = REPO / ".githooks" / "control-plane-guard.sh"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


# ai-guide 自身 marker 形態（wt 級——patterns 單一源仍走 control-plane-guard.sh，
# sourceRoots 空＝現行行為等價；.agents/marshal-governance.json 同款）
WT_MARKER = {
    "protocol": 1,
    "trunk": "main",
    "invariantLevel": "wt",
    "sourceRoots": [],
    "allowlist": ["^\\.agents/marshal-governance\\.json$"],
}


def _write_marker(repo: Path, profile: dict) -> None:
    agents = repo / ".agents"
    agents.mkdir(exist_ok=True)
    (agents / "marshal-governance.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    """canonical repo（main）＋卡 worktree（air-1）＋他 repo（無 marker——absent 腿）。"""
    tmp_path = tmp_path_factory.mktemp("marshal-guard")
    canon = tmp_path / "canon"
    canon.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(canon)], check=True)
    _git(canon, "config", "user.email", "t@t")
    _git(canon, "config", "user.name", "t")
    (canon / ".githooks").mkdir()
    (canon / "hooks").mkdir()
    (canon / ".githooks" / "control-plane-guard.sh").write_text(
        GUARD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (canon / "hooks" / "marshal_admission_guard.py").write_text(
        HOOK.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _write_marker(canon, WT_MARKER)
    (canon / "rules").mkdir()
    (canon / "rules" / "tool-discipline.md").write_text("x\n", encoding="utf-8")
    (canon / "notes").mkdir()
    (canon / "notes" / "idea.md").write_text("x\n", encoding="utf-8")
    (canon / "README.md").write_text("seed\n", encoding="utf-8")
    _git(canon, "add", "-A")
    _git(canon, "commit", "-q", "-m", "seed")
    wt = tmp_path / "canon-wt"
    r = _git(canon, "worktree", "add", "-b", "air-1", str(wt))
    assert r.returncode == 0, r.stderr
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(other)], check=True)
    _git(other, "config", "user.email", "t@t")
    _git(other, "config", "user.name", "t")
    (other / "rules").mkdir()
    (other / "rules" / "tool-discipline.md").write_text("x\n", encoding="utf-8")
    (other / "README.md").write_text("seed\n", encoding="utf-8")
    _git(other, "add", "-A")
    _git(other, "commit", "-q", "-m", "seed")
    return {"canon": canon, "wt": wt, "other": other}


@pytest.fixture(scope="module")
def branch_sandbox(tmp_path_factory):
    """branch 級 invariant repo（自帶 hook 拷貝——self repo 語音；sourceRoots
    ^src/、allowlist ^src/legacy/）。模擬「收編 repo 的 canonical main 改
    sourceRoots 檔案→deny」probe 情境（工單任務 2——temp repo，不碰真 canonical）。"""
    tmp_path = tmp_path_factory.mktemp("marshal-branch")
    repo = tmp_path / "repo2"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / ".githooks").mkdir()
    (repo / "hooks").mkdir()
    (repo / ".githooks" / "control-plane-guard.sh").write_text(
        GUARD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (repo / "hooks" / "marshal_admission_guard.py").write_text(
        HOOK.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _write_marker(
        repo,
        {
            "protocol": 1,
            "trunk": "main",
            "invariantLevel": "branch",
            "sourceRoots": ["^src/"],
            "allowlist": ["^src/legacy/"],
        },
    )
    (repo / "src" / "legacy").mkdir(parents=True)
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src" / "legacy" / "old.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("x\n", encoding="utf-8")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")
    return {"repo": repo}


def _run_hook(
    sandbox: dict, payload, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(sandbox["canon"] / "hooks" / "marshal_admission_guard.py"),
        ],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd) if cwd is not None else None,
    )


def _edit_payload(file_path: str, tool: str = "Edit") -> dict:
    return {"tool_name": tool, "tool_input": {"file_path": file_path}}


def _patch(action_line: str, cwd: Path) -> dict:
    return {
        "tool_name": "apply_patch",
        "tool_input": {
            "command": f"*** Begin Patch\n*** {action_line}\n+content\n*** End Patch"
        },
        "cwd": str(cwd),
    }


def _assert_deny(r: subprocess.CompletedProcess, context: str) -> None:
    assert r.returncode == 2, f"{context}：應 deny（exit 2）未擋\n{r.stderr}"
    assert "控制面路徑禁 canonical 主樹直寫" in r.stderr, context
    assert "wt-open" in r.stderr, f"{context}：deny 須指路卡 WT\n{r.stderr}"
    out = json.loads(r.stdout)  # stdout JSON 說明
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny", context


def _assert_allow(r: subprocess.CompletedProcess, context: str) -> None:
    assert r.returncode == 0, f"{context}：應放行卻擋\n{r.stdout}\n{r.stderr}"


# ---------------------------------------------------------------------------
# branch 級 invariant（AIR-152 marker 泛化）：canonical∧branch==trunk∧sourceRoots
# ---------------------------------------------------------------------------


def _run_branch_hook(
    branch_sandbox: dict, payload, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(branch_sandbox["repo"] / "hooks" / "marshal_admission_guard.py"),
        ],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd) if cwd is not None else None,
    )


def _assert_branch_deny(r: subprocess.CompletedProcess, context: str) -> None:
    assert r.returncode == 2, f"{context}：應 deny（exit 2）未擋\n{r.stderr}"
    assert "branch 級 invariant" in r.stderr, context
    assert "wt-open" in r.stderr, f"{context}：deny 須指路卡 WT\n{r.stderr}"
    assert "--base main" in r.stderr, f"{context}：指路須帶 marker trunk\n{r.stderr}"
    assert "--ephemeral" in r.stderr, f"{context}：指路須含 ephemeral 出路\n{r.stderr}"
    out = json.loads(r.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny", context


def test_branch_level_canonical_trunk_hit_deny(branch_sandbox):
    """probe 情境：canonical main（==trunk）改 sourceRoots 檔案 → deny。"""
    repo = branch_sandbox["repo"]
    r = _run_branch_hook(branch_sandbox, _edit_payload(str(repo / "src" / "app.py")))
    _assert_branch_deny(r, "canonical trunk × src/ 命中")


def test_branch_level_new_file_nearest_parent_deny(branch_sandbox):
    repo = branch_sandbox["repo"]
    r = _run_branch_hook(
        branch_sandbox, _edit_payload(str(repo / "src" / "sub" / "new.py"))
    )
    _assert_branch_deny(r, "canonical trunk 新檔（nearest parent=src/）")


def test_branch_level_non_trunk_branch_allow(branch_sandbox):
    """branch 級豁免主腿：canonical checkout 切到非 trunk branch → 放行。"""
    repo = branch_sandbox["repo"]
    _git(repo, "checkout", "-q", "-b", "feature-x")
    try:
        r = _run_branch_hook(
            branch_sandbox, _edit_payload(str(repo / "src" / "app.py"))
        )
        _assert_allow(r, "canonical 非 trunk branch")
    finally:
        _git(repo, "checkout", "-q", "main")


def test_branch_level_detached_head_allow(branch_sandbox):
    """detached HEAD（--abbrev-ref 回 HEAD）≠ trunk → 豁免（封閉 predicate 不確定不擋）。"""
    repo = branch_sandbox["repo"]
    _git(repo, "checkout", "-q", "--detach")
    try:
        r = _run_branch_hook(
            branch_sandbox, _edit_payload(str(repo / "src" / "app.py"))
        )
        _assert_allow(r, "detached HEAD")
    finally:
        _git(repo, "checkout", "-q", "main")


def test_branch_level_allowlist_allow(branch_sandbox):
    repo = branch_sandbox["repo"]
    r = _run_branch_hook(
        branch_sandbox, _edit_payload(str(repo / "src" / "legacy" / "old.py"))
    )
    _assert_allow(r, "allowlist ^src/legacy/ 豁免")


def test_branch_level_non_source_path_allow(branch_sandbox):
    repo = branch_sandbox["repo"]
    r = _run_branch_hook(branch_sandbox, _edit_payload(str(repo / "docs" / "a.md")))
    _assert_allow(r, "sourceRoots 未命中路徑")


def test_branch_level_worktree_allow(branch_sandbox):
    """非 canonical 卡 WT 寫 sourceRoots 檔＋在場憑證 → 放行（SC-199.1 後的
    正當出路：卡 WT 寫 src/ 需 marshal 發放的 work-order.json）。"""
    repo = branch_sandbox["repo"]
    wt = branch_sandbox["repo"].parent / "repo2-wt"
    r = _git(repo, "worktree", "add", "-b", "card-1", str(wt))
    assert r.returncode == 0, r.stderr
    _write_work_order(wt)
    r = _run_branch_hook(branch_sandbox, _edit_payload(str(wt / "src" / "app.py")))
    _assert_allow(r, "卡 WT 寫 src/（有憑證）")


# ---------------------------------------------------------------------------
# SC-199.1——非 canonical 卡 WT 寫 sourceRoots 需在場 work-order 憑證
# ---------------------------------------------------------------------------

# work-order 憑證 v1 schema（SC-199.1 決策①——marshal spawn 時發放；
# hook 只驗在場性＋schema 必填欄位，不做內容語義驗證）
WO_VALID = {
    "schema": "work-order/1",
    "worker": "implement-lite",
    "card": "SC-199.1",
    "scope": "src/**",
    "brief": "unit-test work order",
    "issuedBy": "marshal",
    "issuedAt": "2026-09-24T00:00:00Z",
}


@pytest.fixture(scope="module")
def wo_sandbox(tmp_path_factory):
    """SC-199.1 憑證閘沙箱：governed repo（branch 級）sourceRoots 刻意涵蓋
    src 面＋豁免面（backlog/.agent-tmp/docs 也命中 sourceRoots——豁免須在
    sourceRoots 命中之下仍放行，測試才非平凡）＋卡 worktree。"""
    tmp_path = tmp_path_factory.mktemp("marshal-wo")
    repo = tmp_path / "repo3"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / ".githooks").mkdir()
    (repo / "hooks").mkdir()
    (repo / ".githooks" / "control-plane-guard.sh").write_text(
        GUARD.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (repo / "hooks" / "marshal_admission_guard.py").write_text(
        HOOK.read_text(encoding="utf-8"), encoding="utf-8"
    )
    _write_marker(
        repo,
        {
            "protocol": 1,
            "trunk": "main",
            "invariantLevel": "branch",
            "sourceRoots": ["^src/", "^docs/", "^backlog/", "^\\.agent-tmp/"],
            "allowlist": ["^\\.agents/marshal-governance\\.json$"],
        },
    )
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("x\n", encoding="utf-8")
    (repo / "backlog" / "tasks").mkdir(parents=True)
    (repo / "backlog" / "tasks" / "t.md").write_text("x\n", encoding="utf-8")
    (repo / ".agent-tmp").mkdir()
    (repo / ".agent-tmp" / "keep.txt").write_text("x\n", encoding="utf-8")
    (repo / "notes").mkdir()
    (repo / "notes" / "idea.md").write_text("x\n", encoding="utf-8")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed")
    wt = tmp_path / "repo3-wt"
    r = _git(repo, "worktree", "add", "-b", "card-9", str(wt))
    assert r.returncode == 0, r.stderr
    yield {"repo": repo, "wt": wt}
    _git(repo, "worktree", "remove", "--force", str(wt))  # 測試建 worktree 收尾


@pytest.fixture()
def wo_clean(wo_sandbox):
    """每案例憑證隔離：進出都保證卡 WT 無殘留 .agent-tmp/work-order.json
    （module fixture 的可變狀態不跨測試洩漏——rerun／-k 單選不誤報）。"""
    wo_path = wo_sandbox["wt"] / ".agent-tmp" / "work-order.json"
    wo_path.unlink(missing_ok=True)
    yield wo_sandbox
    wo_path.unlink(missing_ok=True)


def _run_wo_hook(
    wo_sandbox: dict, payload, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(wo_sandbox["repo"] / "hooks" / "marshal_admission_guard.py"),
        ],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd) if cwd is not None else None,
    )


def _write_work_order(wt: Path, data: dict | None = None, raw: str | None = None):
    """在卡 WT 根放 .agent-tmp/work-order.json（data=None→合法憑證；
    raw 非 None→原樣寫入壞 JSON 用）。"""
    d = wt / ".agent-tmp"
    d.mkdir(exist_ok=True)
    path = d / "work-order.json"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
        return
    payload = dict(WO_VALID) if data is None else data
    path.write_text(json.dumps(payload), encoding="utf-8")


def _assert_wo_deny(r: subprocess.CompletedProcess, context: str) -> None:
    assert r.returncode == 2, f"{context}：應 deny（exit 2）未擋\n{r.stderr}"
    assert "work-order.json" in r.stderr, (
        f"{context}：deny 須指到憑證檔 .agent-tmp/work-order.json\n{r.stderr}"
    )
    assert "marshal" in r.stderr, (
        f"{context}：deny 須指路 marshal spawn 流程\n{r.stderr}"
    )
    out = json.loads(r.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny", context


def test_wo_card_wt_src_without_credential_deny(wo_clean):
    """①非 canonical 卡 WT 寫 src/ 無憑證 → deny＋指路 spawn 流程。"""
    wt = wo_clean["wt"]
    r = _run_wo_hook(wo_clean, _edit_payload(str(wt / "src" / "app.py")))
    _assert_wo_deny(r, "卡 WT 寫 src/ 無憑證")


def test_wo_deny_message_generic_pointer_with_workable_example(wo_clean, tmp_path):
    """deny 指路文字（AIR-194 定案反轉 SC-199.1 舊斷言）：寫死 repo 限定語
    （governed repo）退場——發行工具改通用措辭（對端 repo scripts/… 或等值
    發行面）＋附最小手寫憑證範例（可發現性）；仍不以 repo 內可執行命令形態
    （node scripts/…）誤導。範例須機驗可過 load_work_order——文案↔schema
    drift 防護（本卡主題的反向閘）。"""
    wt = wo_clean["wt"]
    r = _run_wo_hook(wo_clean, _edit_payload(str(wt / "src" / "app.py")))
    _assert_wo_deny(r, "deny 指路文字")
    assert "node scripts/" not in r.stderr, "deny 文字勿以 repo 內命令形態指路"
    assert "governed repo" not in r.stderr, "寫死 repo 限定語已退場（AIR-194）"
    assert "issue-work-order.mjs" in r.stderr, "發行工具通用指路保留"
    assert "等值發行面" in r.stderr, "措辭須通用化至等值發行面"
    m = re.search(r'\{"schema":"work-order/1"[^\n]*\}', r.stderr)
    assert m, "deny 須附一行 JSON 手寫憑證範例"
    example = json.loads(m.group(0))  # 範例須為合法 JSON
    guard = load_module("hooks/marshal_admission_guard.py")
    (tmp_path / ".agent-tmp").mkdir()
    (tmp_path / ".agent-tmp" / "work-order.json").write_text(
        json.dumps(example), encoding="utf-8"
    )
    assert guard.load_work_order(str(tmp_path)) is not None, (
        "deny 文案所附範例須實際可過 schema 驗證（文案↔schema drift 防護）"
    )


# ---------------------------------------------------------------------------
# AIR-194——scope 兩形（非空 str 或非空 list[str]）＋canonical schema 單一源
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scope",
    [
        "src/**",  # 手寫 str 形（回兼容——SC-199.1 原形）
        ["src/**"],  # 發行工具 list 形（單元素）
        ["src/**", "tests/**"],  # list 形（多元素）
    ],
)
def test_wo_scope_two_forms_allow(wo_clean, scope):
    """AC#1：scope 兩形皆過閘——清單形（工具產憑證正典）＋文字形（手寫回兼容）。"""
    data = dict(WO_VALID)
    data["scope"] = scope
    _write_work_order(wo_clean["wt"], data=data)
    r = _run_wo_hook(wo_clean, _edit_payload(str(wo_clean["wt"] / "src" / "app.py")))
    _assert_allow(r, f"scope 兩形過閘（{scope!r}）")


@pytest.mark.parametrize(
    "scope",
    [
        "",  # 空 str
        [],  # 空清單
        ["src/**", ""],  # 清單含空 str
        ["src/**", 123],  # 混型清單
        123,  # 非容器非 str
        {"glob": "src/**"},  # dict 形（第三形 drift 防護）
    ],
)
def test_wo_scope_bad_forms_deny(wo_clean, scope):
    """AC#2：fail-loud 不回歸——空 str／空清單／含空元素／混型／型別錯皆拒。"""
    data = dict(WO_VALID)
    data["scope"] = scope
    _write_work_order(wo_clean["wt"], data=data)
    r = _run_wo_hook(wo_clean, _edit_payload(str(wo_clean["wt"] / "src" / "app.py")))
    _assert_wo_deny(r, f"scope 壞形（{scope!r}）")


@pytest.mark.parametrize(
    "key", ["worker", "card", "scope", "brief", "issuedBy", "issuedAt"]
)
def test_wo_missing_required_key_deny(wo_clean, key):
    """AC#2：六必填欄位逐一缺皆拒（與缺席同罪 fail-closed）。"""
    data = {k: v for k, v in WO_VALID.items() if k != key}
    _write_work_order(wo_clean["wt"], data=data)
    r = _run_wo_hook(wo_clean, _edit_payload(str(wo_clean["wt"] / "src" / "app.py")))
    _assert_wo_deny(r, f"缺必填欄位 {key}")


def test_wo_schema_single_source_doc_and_hook_pointer():
    """AC#4：canonical schema 單一源文檔在場、涵蓋六欄＋scope 兩形，hook 源碼
    帶引用指針（防第三個消費者再分叉）。"""
    doc = REPO / "hooks" / "work-order-schema.md"
    assert doc.is_file(), "hooks/work-order-schema.md 單一源文檔在場"
    text = doc.read_text(encoding="utf-8")
    for token in (
        "work-order/1",
        "worker",
        "card",
        "scope",
        "brief",
        "issuedBy",
        "issuedAt",
        "hooks/marshal_admission_guard.py",
        "issue-work-order.mjs",
    ):
        assert token in text, f"schema 文檔缺錨點 {token!r}"
    hook_src = HOOK.read_text(encoding="utf-8")
    assert "work-order-schema.md" in hook_src, "hook 源碼應引用 schema 單一源文檔"


def test_wo_card_wt_src_with_valid_credential_allow(wo_clean):
    """②同座標＋合法憑證在場 → 放行（SC-199.1 後卡 WT 寫 src 的正當出路）。"""
    wt = wo_clean["wt"]
    _write_work_order(wt)
    r = _run_wo_hook(wo_clean, _edit_payload(str(wt / "src" / "app.py")))
    _assert_allow(r, "卡 WT 寫 src/ 有憑證")


def test_wo_broken_credential_schema_deny(wo_clean):
    """③憑證 schema 壞（版本錯／缺必填欄位／空值／型別錯／非 dict／爛 JSON）
    → 與缺席同罪 deny（fail-closed）。憑證清理交 wo_clean fixture。"""
    wt = wo_clean["wt"]
    missing = {k: v for k, v in WO_VALID.items() if k != "card"}
    broken_variants = [missing, "{not-json", "[1, 2]"]
    for patch in (
        {"schema": "work-order/2"},
        {"scope": ""},
        {"worker": None},
        {"brief": 123},
    ):
        data = dict(WO_VALID)
        data.update(patch)
        broken_variants.append(data)
    for bad in broken_variants:
        if isinstance(bad, str):
            _write_work_order(wt, raw=bad)
        else:
            _write_work_order(wt, data=bad)
        r = _run_wo_hook(wo_clean, _edit_payload(str(wt / "src" / "app.py")))
        _assert_wo_deny(r, f"憑證 schema 壞（{bad!r}）")


def test_wo_exempt_paths_card_wt_allow_without_credential(wo_clean):
    """⑤豁免面（backlog metadata／.agent-tmp／docs）在 sourceRoots 命中下
    仍不觸發憑證要求——寫憑證檔自身亦不需憑證（防循環）。
    豁免語義＝目錄前綴（`backlog/`…帶尾斜線；見 _work_order_exempt docstring）：
    bare 目錄名不豁免亦不命中 sourceRoots——Edit/Write 座標恆為檔案路徑。"""
    wt = wo_clean["wt"]
    for rel in (
        "docs/a.md",
        "backlog/tasks/t.md",
        ".agent-tmp/scratch.md",
        ".agent-tmp/work-order.json",
    ):
        r = _run_wo_hook(wo_clean, _edit_payload(str(wt / rel)))
        _assert_allow(r, f"豁免面 {rel}（無憑證）")


def test_wo_card_wt_non_source_path_allow(wo_clean):
    wt = wo_clean["wt"]
    r = _run_wo_hook(wo_clean, _edit_payload(str(wt / "notes" / "idea.md")))
    _assert_allow(r, "卡 WT 非 sourceRoots 路徑（無憑證）")


def test_wo_canonical_source_hit_still_deny(wo_sandbox):
    """豁免只及非 canonical 憑證面——canonical 寫命中 sourceRoots 的 docs/
    仍走既有 invariant deny。"""
    repo = wo_sandbox["repo"]
    r = _run_wo_hook(wo_sandbox, _edit_payload(str(repo / "docs" / "a.md")))
    _assert_branch_deny(r, "canonical docs/ 命中 sourceRoots")


def test_wo_empty_sourceroots_repo_card_wt_unchanged(sandbox):
    """④sourceRoots 空清單 repo（ai-guide 形態）：卡 WT 寫 src 面（非豁免面）
    無憑證仍放行——零行為變更。"""
    wt = sandbox["wt"]
    r = _run_hook(sandbox, _edit_payload(str(wt / "src" / "new.py")))
    _assert_allow(r, "空 sourceRoots repo 卡 WT 寫 src/（行為不變）")


def test_marker_file_itself_exempt(sandbox):
    """marker 檔恆豁免——valid profile 下仍可直接編輯（改 profile 的入口）。"""
    canon = sandbox["canon"]
    r = _run_hook(
        sandbox, _edit_payload(str(canon / ".agents" / "marshal-governance.json"))
    )
    _assert_allow(r, "marker 檔自身")


# ---------------------------------------------------------------------------
# marker 三態：malformed fail-closed（禁 fail-open）——deny＋指路修復
# ---------------------------------------------------------------------------


def test_malformed_marker_deny_with_repair_guidance(sandbox):
    """JSON 壞 → 本 repo 寫入 deny（fail-closed）；訊息指路修 marker。"""
    canon = sandbox["canon"]
    marker = canon / ".agents" / "marshal-governance.json"
    original = marker.read_text(encoding="utf-8")
    marker.write_text("{not-json", encoding="utf-8")
    try:
        r = _run_hook(sandbox, _edit_payload(str(canon / "notes" / "idea.md")))
        assert r.returncode == 2, f"malformed marker 應 deny\n{r.stderr}"
        assert "marker 損毀" in r.stderr
        assert "marshal-governance.json" in r.stderr, "須指到 marker 檔路徑"
        out = json.loads(r.stdout)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        # 修復出口：marker 檔本身仍可編輯
        r_fix = _run_hook(sandbox, _edit_payload(str(marker)))
        _assert_allow(r_fix, "malformed 下修 marker 自身")
    finally:
        marker.write_text(original, encoding="utf-8")


def test_malformed_marker_schema_deny(sandbox):
    """JSON 可解析但 schema 不符（protocol 錯／level 非法）＝malformed → deny。"""
    canon = sandbox["canon"]
    marker = canon / ".agents" / "marshal-governance.json"
    original = marker.read_text(encoding="utf-8")
    for bad in (
        {"protocol": 2, "trunk": "main", "invariantLevel": "wt"},
        {"protocol": 1, "trunk": "main", "invariantLevel": "repo"},
        {"protocol": 1, "invariantLevel": "wt"},
        {"protocol": 1, "trunk": "main", "invariantLevel": "wt", "sourceRoots": "src/"},
    ):
        marker.write_text(json.dumps(bad), encoding="utf-8")
        try:
            r = _run_hook(sandbox, _edit_payload(str(canon / "notes" / "idea.md")))
            assert r.returncode == 2, f"{bad} 應 malformed deny\n{r.stderr}"
        finally:
            marker.write_text(original, encoding="utf-8")


def test_malformed_marker_deny_extends_to_card_worktree(sandbox):
    """marker 以 canonical 為準讀——canonical 上壞 marker，卡 WT 寫入也 fail-closed。"""
    canon = sandbox["canon"]
    marker = canon / ".agents" / "marshal-governance.json"
    original = marker.read_text(encoding="utf-8")
    marker.write_text("[broken", encoding="utf-8")
    try:
        r = _run_hook(sandbox, _edit_payload(str(sandbox["wt"] / "notes" / "idea.md")))
        assert r.returncode == 2, f"壞 marker 下卡 WT 寫入應 deny\n{r.stderr}"
        assert "marker 損毀" in r.stderr
    finally:
        marker.write_text(original, encoding="utf-8")


def test_absent_marker_other_repo_allow(sandbox):
    """三態之一 absent：無 marker repo 全放行（opt-in 向下相容）。"""
    other = sandbox["other"]
    r = _run_hook(sandbox, _edit_payload(str(other / "rules" / "tool-discipline.md")))
    _assert_allow(r, "無 marker repo（absent）")


# ---------------------------------------------------------------------------
# deny 腿：canonical 主樹 × 控制面路徑（path resolution 各形態）
# ---------------------------------------------------------------------------


def test_canonical_control_plane_absolute_deny(sandbox):
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload(str(canon / "rules" / "tool-discipline.md")))
    _assert_deny(r, "canonical rules 絕對路徑")


@pytest.mark.parametrize("tool", ["Edit", "Write"])
def test_tool_matrix_deny(sandbox, tool):
    canon = sandbox["canon"]
    r = _run_hook(
        sandbox, _edit_payload(str(canon / "skills" / "x" / "SKILL.md"), tool=tool)
    )
    _assert_deny(r, f"tool={tool}")


def test_relative_path_with_payload_cwd_deny(sandbox):
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload("rules/tool-discipline.md"), cwd=canon)
    _assert_deny(r, "相對路徑＋payload cwd")


def test_relative_path_with_process_cwd_deny(sandbox):
    """payload 無 cwd → 退 process cwd（subprocess cwd 釘在 canonical）。"""
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload("rules/tool-discipline.md"), cwd=canon)
    _assert_deny(r, "相對路徑＋process cwd")


def test_dotdot_traversal_from_worktree_deny(sandbox):
    wt = sandbox["wt"]
    r = _run_hook(
        sandbox,
        _edit_payload("../canon/rules/tool-discipline.md"),
        cwd=wt,
    )
    _assert_deny(r, "../ 穿越回 canonical")


def test_symlink_dir_into_canonical_deny(sandbox):
    """卡 WT 內目錄 symlink 指回 canonical——resolve 後以實際 write target 判定。"""
    canon = sandbox["canon"]
    wt = sandbox["wt"]
    link = wt / "link-rules"
    link.symlink_to(canon / "rules")
    r = _run_hook(sandbox, _edit_payload(str(link / "tool-discipline.md")))
    _assert_deny(r, "目錄 symlink 回 canonical")


def test_symlink_file_into_canonical_deny(sandbox):
    canon = sandbox["canon"]
    wt = sandbox["wt"]
    alias = wt / "rules-alias.md"
    alias.symlink_to(canon / "rules" / "tool-discipline.md")
    r = _run_hook(sandbox, _edit_payload(str(alias)))
    _assert_deny(r, "檔案 symlink 回 canonical")


def test_new_file_nearest_existing_parent_deny(sandbox):
    """新檔（rules/sub/ 不存在）以 nearest existing parent（rules/）定 toplevel。"""
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload(str(canon / "rules" / "sub" / "new.md")))
    _assert_deny(r, "新檔 nearest parent（控制面）")


def test_new_file_deep_broken_chain_deny(sandbox):
    """父鏈多層不存在仍能走到 canonical。"""
    canon = sandbox["canon"]
    r = _run_hook(
        sandbox, _edit_payload(str(canon / "governance" / "a" / "b" / "c.json"))
    )
    _assert_deny(r, "新檔深鏈（控制面）")


@pytest.mark.parametrize(
    "header",
    [
        "Add File: rules/patched.md",
        "Update File: rules/tool-discipline.md",
        "Delete File: agents/roles/x.md",
        "Update File: notes/b.md\n*** Move to: rules/moved.md",
    ],
)
def test_codex_patch_any_hit_deny(sandbox, header):
    """codex apply_patch adapter——Add/Update/Delete／Move to 各標頭形態；一命中即 deny。"""
    r = _run_hook(sandbox, _patch(header, cwd=sandbox["canon"]))
    _assert_deny(r, f"apply_patch header：{header.splitlines()[0]}")


def test_codex_multifile_patch_clean_plus_hit_deny(sandbox):
    """多檔 patch——clean 檔＋控制面檔混署，任一 canonical 命中即整 call deny。"""
    canon = sandbox["canon"]
    command = (
        "*** Begin Patch\n"
        "*** Update File: notes/idea.md\n"
        "-old\n+new\n"
        "*** Add File: hooks/evil.py\n"
        "+x = 1\n"
        "*** End Patch"
    )
    r = _run_hook(
        sandbox,
        {
            "tool_name": "apply_patch",
            "tool_input": {"command": command},
            "cwd": str(canon),
        },
    )
    _assert_deny(r, "多檔 patch 一命中")


# ---------------------------------------------------------------------------
# allow 腿：非 canonical WT、非控制面路徑、self-gate
# ---------------------------------------------------------------------------


def test_sibling_worktree_allow(sandbox):
    """canonical session 寫卡 WT——非 canonical 放行（guard 的正當出路）。"""
    wt = sandbox["wt"]
    r = _run_hook(sandbox, _edit_payload(str(wt / "rules" / "tool-discipline.md")))
    _assert_allow(r, "卡 WT 控制面路徑")


def test_canonical_non_control_plane_allow(sandbox):
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload(str(canon / "notes" / "idea.md")))
    _assert_allow(r, "canonical 非控制面")


def test_new_file_non_control_plane_allow(sandbox):
    canon = sandbox["canon"]
    r = _run_hook(sandbox, _edit_payload(str(canon / "notes" / "deep" / "new.md")))
    _assert_allow(r, "新檔 nearest parent（非控制面）")


def test_other_repo_same_name_rules_allow(sandbox):
    """repo self-gate——他 repo 的 canonical 同名 rules/ 不得被 ai-guide policy 誤殺。"""
    other = sandbox["other"]
    r = _run_hook(sandbox, _edit_payload(str(other / "rules" / "tool-discipline.md")))
    _assert_allow(r, "他 repo 同名 rules/")


def test_other_repo_new_rules_file_allow(sandbox):
    other = sandbox["other"]
    r = _run_hook(sandbox, _edit_payload(str(other / "rules" / "fresh.md")))
    _assert_allow(r, "他 repo 新檔 rules/")


def test_path_outside_any_repo_allow(sandbox):
    """repo 外路徑（tmp 根）——git 不可判定 → 放行。"""
    p = sandbox["canon"].parent / "no-repo" / "x.md"
    r = _run_hook(sandbox, _edit_payload(str(p)))
    _assert_allow(r, "repo 外路徑")


def test_codex_clean_patch_allow(sandbox):
    canon = sandbox["canon"]
    command = (
        "*** Begin Patch\n"
        "*** Update File: notes/idea.md\n"
        "-old\n+new\n"
        "*** Add File: scripts-helpers/util.py\n"
        "+x = 1\n"
        "*** End Patch"
    )
    r = _run_hook(
        sandbox,
        {
            "tool_name": "apply_patch",
            "tool_input": {"command": command},
            "cwd": str(canon),
        },
    )
    _assert_allow(r, "多檔 patch 全 clean")


# ---------------------------------------------------------------------------
# fail-open 契約：malformed payload／形狀漂移／非轄面工具 → exit 0
# ---------------------------------------------------------------------------


def test_malformed_json_fail_open(sandbox):
    r = _run_hook(sandbox, "not-json{{")
    _assert_allow(r, "malformed JSON")


def test_payload_not_dict_fail_open(sandbox):
    r = _run_hook(sandbox, "[1, 2, 3]")
    _assert_allow(r, "payload 非 dict")


def test_missing_tool_input_fail_open(sandbox):
    r = _run_hook(sandbox, {"tool_name": "Edit"})
    _assert_allow(r, "缺 tool_input")


def test_missing_file_path_fail_open(sandbox):
    r = _run_hook(sandbox, {"tool_name": "Edit", "tool_input": {"old_string": "a"}})
    _assert_allow(r, "缺 file_path")


def test_non_registered_tool_ignored(sandbox):
    """註冊 matcher 外的工具（第二道防禦）——不歸本 hook 管。"""
    canon = sandbox["canon"]
    r = _run_hook(
        sandbox,
        {
            "tool_name": "Bash",
            "tool_input": {"file_path": str(canon / "rules" / "x.md")},
        },
    )
    _assert_allow(r, "Bash 工具")


def test_apply_patch_empty_command_fail_open(sandbox):
    r = _run_hook(sandbox, {"tool_name": "apply_patch", "tool_input": {"command": ""}})
    _assert_allow(r, "apply_patch 空 command")


# ---------------------------------------------------------------------------
# --match-path 子入口（AC#2——patterns 單一源 predicate）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel,expected",
    [
        ("rules/tool-discipline.md", 1),
        ("skills/foo/SKILL.md", 1),
        ("hooks/block-x.py", 1),
        ("governance/install.py", 1),
        (".githooks/pre-commit", 1),
        ("ai-development-guide.md", 1),
        ("CLAUDE.md", 1),
        ("tests/test_githooks.py", 1),
        ("scripts/deploy_agents.py", 1),
        ("backlog/tasks/air-1 - x.md", 0),
        ("scripts/util.py", 0),
        ("ai-analysis/reports/note.md", 0),
        ("notes/idea.md", 0),
    ],
)
def test_match_path_predicate(sandbox, rel, expected):
    r = subprocess.run(
        [
            "/bin/bash",
            str(sandbox["canon"] / ".githooks" / "control-plane-guard.sh"),
            "--match-path",
            rel,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == expected, f"--match-path {rel}：期望 {expected}"


def test_match_path_missing_arg_usage_error(sandbox):
    r = subprocess.run(
        [
            "/bin/bash",
            str(sandbox["canon"] / ".githooks" / "control-plane-guard.sh"),
            "--match-path",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 2
    assert "usage" in r.stderr


# ---------------------------------------------------------------------------
# mixed-session／rollback Python 3.9 syntax compatibility gate
# ---------------------------------------------------------------------------


def test_hook_parses_as_py39():
    source = HOOK.read_text(encoding="utf-8")
    ast.parse(source, filename=str(HOOK))  # 當前 runtime 可解析
    ast.parse(source, filename=str(HOOK), feature_version=(3, 9))  # 3.9 語法面


def test_real_repo_hook_runs_allow_on_repo_external_target():
    """真 repo hook（非拷貝）煙霧腿：repo 外目標 → fail-open 面放行 exit 0。"""
    r = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(_edit_payload("/private/tmp/definitely-not-a-repo/x.md")),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO),
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_malformed_marker_invalid_regex_deny(sandbox):
    """sourceRoots／allowlist 任一 regex 語法錯＝malformed deny（152-C2：靜默
    失效即假保護——enrollment 也不得對 non-enforcing profile 回報成功）。"""
    canon = sandbox["canon"]
    marker = canon / ".agents" / "marshal-governance.json"
    original = marker.read_text(encoding="utf-8")
    for bad in (
        {
            "protocol": 1,
            "trunk": "main",
            "invariantLevel": "branch",
            "sourceRoots": ["["],
        },
        {
            "protocol": 1,
            "trunk": "main",
            "invariantLevel": "branch",
            "sourceRoots": ["src/"],
            "allowlist": ["(unclosed"],
        },
    ):
        marker.write_text(json.dumps(bad), encoding="utf-8")
        try:
            r = _run_hook(sandbox, _edit_payload(str(canon / "notes" / "idea.md")))
            assert r.returncode == 2, f"{bad} 壞 regex 應 malformed deny\n{r.stderr}"
        finally:
            marker.write_text(original, encoding="utf-8")
