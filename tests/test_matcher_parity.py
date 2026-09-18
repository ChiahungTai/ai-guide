"""matcher↔handler parity assertion（AIR-100 S-C——TC-5/P5-1）。

dead-matcher 防再生：registration 端宣稱攔的工具名集合，必須 ⊆ handler script
實際分支集合。P0-4 探針定案（2026-09-17）：handler 讀 `tool_input.file_path`，
NotebookEdit payload 路徑鍵是 `notebook_path` → file_path guard 直落 exit 0
（合成 payload 帶 file_path 時才會誤觸第①層索引檢查——真實 runtime 不可達）。
處置＝(a) 移 matcher 字面（EP 寫死決策），本測試防「再加 matcher 字面而無分支」
的 dead-matcher 再生。

三來源（AC-C2）：範本 governance/registrations/zcode.json（AIR-116 收編，原
hooks/zcode-registration.json）、CC settings（repo settings.json——
~/.claude/settings.json symlink 真實目標；**gitignored local-only，fresh
worktree 天生缺席** → skip＋標記 `live-config-absent`）、ZCode live config
（~/.zcode/cli/config.json——enforcement 面；缺席 → skip 同標記）。範本是
版控資產，缺席＝fail 不得靜默。
"""

import json
import os
import re
from pathlib import Path

import pytest
from conftest import REPO_ROOT

# AIR-125 AC#2 hook 模式隔離：live drift 偵測的單一歸宿＝installer --check
# （launchd monitor 日頻調用），不在 commit gate——hook 執行 pytest 腿前
# export PRE_COMMIT=1，live 面測試在該模式下 skip，commit gate 對機器 live
# config 維持確定性（不讀真實環境 → 同 commit 結果可重現）。
_IN_PRE_COMMIT = os.environ.get("PRE_COMMIT") == "1"

TEMPLATE = REPO_ROOT / "governance" / "registrations" / "zcode.json"
CC_SETTINGS = REPO_ROOT / "settings.json"
ZCODE_LIVE = Path.home() / ".zcode" / "cli" / "config.json"
HANDLED_SCRIPT = REPO_ROOT / "hooks" / "block-memory-index-write.py"
HANDLED_BRIDGE = "block-memory-index-write.py"


def handler_branches() -> set[str]:
    """由 script 機械抽取 tool 分支集合（`tool == "X"` 比較——非手寫）。"""
    src = HANDLED_SCRIPT.read_text(encoding="utf-8")
    branches = set(re.findall(r'tool == "(\w+)"', src))
    return branches


def _pretooluse_groups(doc: dict) -> list:
    """三種 registration 形狀收斂：範本（events 頂層）、CC（hooks.PreToolUse）、
    ZCode live（hooks.events.PreToolUse）。"""
    hooks = doc.get("hooks", doc)
    events = hooks.get("events", hooks) if isinstance(hooks, dict) else {}
    groups = events.get("PreToolUse", []) if isinstance(events, dict) else []
    return groups if isinstance(groups, list) else []


def _commands(group: dict) -> list[str]:
    """hook entry 的可判斷命令串（command＋args 合併——範本/ZCode live 把 script
    放 args、CC settings 放 command 字串，兩形態都要命中）。"""
    out = []
    for h in group.get("hooks", []):
        if isinstance(h, dict):
            joined = " ".join(
                [str(h.get("command", ""))] + [str(a) for a in h.get("args", [])]
            )
            out.append(joined)
    return out


def collect_memory_hook_matchers(sources: dict[str, Path]) -> dict[str, set[str] | None]:
    """各來源中 wire 到 block-memory hook 的 PreToolUse matcher 字面集合。

    值 None＝檔缺席（marker；消費端決定 skip 或 fail）。
    """
    out: dict[str, set[str] | None] = {}
    for name, path in sources.items():
        if not path.exists():
            out[name] = None
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        matchers: set[str] = set()
        for group in _pretooluse_groups(doc):
            if not isinstance(group, dict):
                continue
            if any(HANDLED_BRIDGE in c for c in _commands(group)):
                raw = group.get("matcher", "")
                matchers.update(m for m in raw.split("|") if m)
        out[name] = matchers
    return out


def test_handler_branches_extracted_nonempty():
    """機械抽取自身健全性：分支集合非空且不含 NotebookEdit（處置後事實）。"""
    branches = handler_branches()
    assert branches == {"Write", "Edit"}, branches


@pytest.mark.skipif(
    _IN_PRE_COMMIT,
    reason="PRE_COMMIT=1（commit gate）：live drift 偵測單一歸宿＝installer --check＋"
           "launchd monitor 日頻，不在 commit gate（AIR-125 AC#2 職責歸位）",
)
def test_matcher_lives_within_handler_branches():
    """TC-5 P5-1：三來源 matcher 字面集合 ⊆ handler 分支集合。

    live 面（讀 ~/.zcode/cli/config.json＋repo settings.json 真實環境）——
    PRE_COMMIT=1（hook 模式）時 skip：commit gate 須確定性，live drift 偵測
    職責歸 installer --check＋launchd monitor 日頻（AIR-125 AC#2）。"""
    handled = handler_branches()
    sources = {"template": TEMPLATE, "cc-settings": CC_SETTINGS, "zcode-live": ZCODE_LIVE}
    collected = collect_memory_hook_matchers(sources)
    if collected["zcode-live"] is None:
        pytest.skip("live-config-absent: ~/.zcode/cli/config.json 缺席——live 面未驗")
    if collected["cc-settings"] is None:
        pytest.skip(
            "live-config-absent: repo settings.json 缺席（gitignored local-only——"
            "fresh worktree 天生無）——CC 面未驗"
        )
    assert collected["template"] is not None, "範本缺席＝registration 源斷裂（fail）"
    for name, matchers in collected.items():
        assert matchers is not None, name
        extra = matchers - handled
        assert not extra, f"{name}: matcher 字面 {extra} 無 handler 分支——dead-matcher（P5-1 紅）"


def test_notebookedit_reintroduction_detected(tmp_path):
    """AC-C4 防再生 negative：範本加回 NotebookEdit → parity 判定面浮出該字面。"""
    doc = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    for group in _pretooluse_groups(doc):
        if any(HANDLED_BRIDGE in c for c in _commands(group)):
            group["matcher"] = "Edit|Write|NotebookEdit"
    mutated = tmp_path / "mutated-registration.json"
    mutated.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    collected = collect_memory_hook_matchers({"mutated": mutated})
    handled = handler_branches()
    assert collected["mutated"] is not None
    extra = collected["mutated"] - handled
    assert extra == {"NotebookEdit"}, extra


def test_live_config_absent_yields_marker_not_silent_green(tmp_path):
    """live 缺席 → None marker（消費端據此 skip＋標記），非空集合靜默綠。"""
    collected = collect_memory_hook_matchers({"absent": tmp_path / "nope.json"})
    assert collected["absent"] is None


if __name__ == "__main__":
    pytest.main([__file__])
