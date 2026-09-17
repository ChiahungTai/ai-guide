"""codex memory path-deny hook 契約測試（AIR-100 S-A——TC-1 合成層）。

P0-2 查證定案（ref-docs/harness/codex/hooks.md）：codex 檔案編輯走
`apply_patch`（hook input `tool_name: "apply_patch"`；`tool_input.command` 含
patch 文本，路徑在 `*** Add/Update/Delete File:`／`*** Move to:` 標頭內）——
非 CC/ZCode 的 `tool_input.file_path` 形狀，本 hook 據此解析。

deny 語義（同源文檔）：exit 2＋stderr 阻斷理由。admission 門 fail-closed
（D3）：stdin parse 失敗／tool_input 形狀不可判定 → exit 2 deny——codex 對
非 0 非 2 exit（如 exit 1）按 hook failure 處理且「continues the tool call」
（fail-open），故 fail-closed 必須走 exit 2。

實際 codex session 實跑（AC-A6/TC-1 actual-runtime）deferred——本檔為合成
payload 行為層（L2）＋工具級 subprocess 餵入（L4 合成形）。
"""

import json
import subprocess
import sys
from pathlib import Path

from conftest import load_module

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "codex_memory_path_deny.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
POOL = REPO_ROOT / ".agents" / "memory"
_mod = load_module("hooks/codex_memory_path_deny.py")


def _payload(command: str, cwd: str, tool: str = "apply_patch") -> str:
    return json.dumps(
        {
            "session_id": "sess_probe",
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"command": command},
            "cwd": cwd,
        }
    )


def _run_hook(payload: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )


def _patch(action: str, path: str) -> str:
    """action＝完整標頭動詞（Add File／Update File／Delete File）。"""
    return f"*** Begin Patch\n*** {action}: {path}\n+content\n*** End Patch"


class TestExtractPatchPaths:
    def test_add_update_delete_move(self):
        cmd = (
            "*** Begin Patch\n"
            "*** Add File: src/a.md\n"
            "*** Update File: src/b.md\n"
            "*** Delete File: src/c.md\n"
            "*** Move to: src/d.md\n"
            "*** End Patch"
        )
        assert _mod.extract_patch_paths(cmd) == [
            "src/a.md",
            "src/b.md",
            "src/c.md",
            "src/d.md",
        ]

    def test_no_headers_empty(self):
        assert _mod.extract_patch_paths("*** Begin Patch\n+hi\n*** End Patch") == []


class TestContainment:
    """池根錨定＝REPO_ROOT（script 位置推導）——cwd 只影響 patch 相對路徑的
    resolve 基準（apply_patch 語義），不影響池根。測試以真實 repo 池路徑為靶
    （合成 payload 不落盤，僅驗 hook 判定）。"""

    def test_pool_entry_relative_to_repo_root(self):
        assert _mod.violation([".agents/memory/entry.md"], str(REPO_ROOT)) is not None

    def test_inbox_and_auto_staging(self):
        assert _mod.violation([".agents/memory-inbox/x.json"], str(REPO_ROOT))
        assert _mod.violation([".agents/memory-auto/MEMORY.md"], str(REPO_ROOT))

    def test_pool_root_itself(self):
        assert _mod.violation([".agents/memory"], str(REPO_ROOT))

    def test_absolute_pool_path(self):
        assert _mod.violation([str(POOL / "e.md")], str(REPO_ROOT))

    def test_subdirectory_cwd_escape_denied(self):
        """codex BI 審查 Critical：session cwd＝repo 子目錄、`../.agents/...`
        相對跳出——池根 REPO_ROOT 錨定後仍命中（cwd 相對解析以 session cwd
        為基準是正確的 apply_patch 語義；池根不受 cwd 影響）。"""
        subdir = REPO_ROOT / "skills"
        assert _mod.violation(["../.agents/memory/e.md"], str(subdir)) is not None

    def test_outside_pool_allows(self):
        assert (
            _mod.violation(["hooks/block-memory-index-write.py"], str(REPO_ROOT))
            is None
        )

    def test_sibling_prefix_dir_not_denied(self):
        """delimiter-aware：.agents/memory-x ≠ .agents/memory（memory-audit path contract ③ 同界）。"""
        assert _mod.violation([".agents/memory-x/entry.md"], str(REPO_ROOT)) is None

    def test_move_to_into_pool_denied(self):
        cmd = (
            "*** Begin Patch\n"
            "*** Update File: other.md\n"
            "*** Move to: .agents/memory/renamed.md\n"
            "*** End Patch"
        )
        paths = _mod.extract_patch_paths(cmd)
        assert "other.md" in paths
        assert ".agents/memory/renamed.md" in paths
        assert _mod.violation(paths, str(REPO_ROOT)) is not None


class TestHookBehavior:
    def test_pool_write_denied_with_pointer(self):
        """AC-A3（TC-1 P1-1 合成形）：池內路徑 → exit 2＋stderr 回報指針。"""
        r = _run_hook(
            _payload(_patch("Add File", ".agents/memory/entry.md"), str(REPO_ROOT))
        )
        assert r.returncode == 2
        assert "唯讀" in r.stderr
        assert "CC/ZCode" in r.stderr

    def test_outside_pool_allowed(self):
        """AC-A4（TC-1 P1-2）：池外路徑 → exit 0 放行（先證座標確實被抽取——防假陽性）。"""
        cmd = _patch("Add File", "notes/scratch.md")
        assert _mod.extract_patch_paths(cmd) == ["notes/scratch.md"]
        r = _run_hook(_payload(cmd, str(REPO_ROOT)))
        assert r.returncode == 0
        assert r.stderr == ""

    def test_relative_and_mixed_patch(self):
        cmd = (
            "*** Begin Patch\n"
            "*** Update File: README.md\n"
            "*** Add File: .agents/memory-inbox/payload.json\n"
            "*** End Patch"
        )
        r = _run_hook(_payload(cmd, str(REPO_ROOT)))
        assert r.returncode == 2

    def test_canonical_marker_case_sensitive(self):
        """codex BI 審查 F-2 終審：parser 對 marker 大小寫敏感——小寫變體非
        apply_patch 語法，不抽取（對齊 canonical；漏網由 reconcile 兜底）。"""
        cmd = "*** Begin Patch\n*** add file: .agents/memory/lower.md\n*** End Patch"
        assert _mod.extract_patch_paths(cmd) == []

    def test_malformed_stdin_fails_closed(self):
        """AC-A5（D3 admission fail-closed）：非 JSON stdin → exit 2（非靜默放行）。"""
        r = _run_hook("not json {")
        assert r.returncode == 2
        assert "fail-closed" in r.stderr

    def test_missing_tool_input_fails_closed(self, tmp_path):
        """tool_input 缺失／command 非字串＝形狀不可判定 → deny（admission 門）。"""
        bad = json.dumps(
            {"tool_name": "apply_patch", "tool_input": None, "cwd": str(tmp_path)}
        )
        assert _run_hook(bad).returncode == 2
        no_cmd = json.dumps({"tool_name": "apply_patch", "cwd": str(tmp_path)})
        assert _run_hook(no_cmd).returncode == 2

    def test_empty_command_allows(self, tmp_path):
        """空 command 寫不了任何東西——放行非 fail-closed 面。"""
        r = _run_hook(_payload("", str(tmp_path)))
        assert r.returncode == 0

    def test_cwd_absent_pool_write_denied(self):
        """F-9：cwd 缺席退 process cwd——相對池內路徑仍 resolve 到池根 → exit 2
        （修前 cwd=None 落 Path(None) TypeError traceback＝exit 1 fail-open 面）。"""
        payload = json.dumps(
            {
                "tool_name": "apply_patch",
                "tool_input": {"command": _patch("Add File", ".agents/memory/e.md")},
            }
        )
        r = _run_hook(payload)
        assert r.returncode == 2, f"expected deny, got {r.returncode}: {r.stderr}"

    def test_cwd_absent_outside_pool_allowed(self):
        """F-9：cwd 缺席＋池外路徑 → exit 0（fallback 解析不誤傷）。"""
        payload = json.dumps(
            {
                "tool_name": "apply_patch",
                "tool_input": {"command": _patch("Add File", "notes/scratch.md")},
            }
        )
        r = _run_hook(payload)
        assert r.returncode == 0, r.stderr
