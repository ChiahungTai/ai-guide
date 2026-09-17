#!/usr/bin/env python3
r"""codex PreToolUse hook：memory 主體 path-deny（AIR-100 S-A——D4 最小 path-deny-all）。

codex 對 memory 主體（.agents/memory／.agents/memory-inbox／.agents/memory-auto）
「唯讀」原為紀律（AGENTS.md 觀察池路由節）——本 hook 補機械面：apply_patch 對池
路徑的寫入一律 deny＋回報指針「交 CC/ZCode 側 session」。

註冊語義（P0-2 查證，ref-docs/harness/codex/hooks.md——2026-09-16 鏡像）：
- 事件鍵＝[[hooks.PreToolUse]]；matcher regex 套 tool_name 與 alias。codex 檔案
  編輯的 canonical tool 名＝`apply_patch`（`Edit`/`Write` 僅 matcher alias，
  hook input 仍回報 `tool_name: "apply_patch"`）——註冊用 `^apply_patch$`。
- payload：`tool_input.command`＝patch 文本；檔案路徑在 `*** Add/Update/Delete
  File:` 與 `*** Move to:` 標頭內（非 CC/ZCode 的 `tool_input.file_path` 形狀）。
- deny 語義：exit 2＋stderr 阻斷理由（同源文檔認可的兩形之一）。
- codex 對非 0 非 2 exit 按 hook failure 處理且「continues the tool call」
  （fail-open）——故 admission 門 fail-closed（D3）必須走 exit 2：stdin parse
  失敗／tool_input 形狀不可判定 → exit 2 deny（EP pseudo code 原寫 exit 1，
  按 codex 協定事實修正——EP 偏差記錄 AIR-100 S-A）。

覆蓋邊界：Bash（shell）redirect／MCP 寫檔工具不在本 hook 面（與 CC/ZCode 同
邊界——reconcile detected 兜底，coverage matrix 註記）。
hook runtime python 3.9——禁 3.10+ 語法（與 block-memory-index-write.py 同界）。
"""

import json
import os
import re
import sys
from pathlib import Path

# apply_patch 標頭抽取（P0-2：四類寫入座標；路徑行尾全取——含空白路徑原樣保留）。
# canonical 對齊（codex BI 審查裁決）：parser 對 marker 大小寫敏感、無 case-insensitive
# parsing；IGNORECASE／行首空白寬鬆匹配已移除——`^\s*` 會把 hunk context 誤判為
# header（false positive），parser 寬容變體漏網由 reconcile 兜底。
# `Move to:` 的 dialect 來源未驗證（mirror 零標頭佐證）——保守 deny（F-4）。
PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
    re.MULTILINE,
)

# 池根錨定＝repo root（script 位於 <repo>/hooks/，parent.parent 推導——codex session
# cwd 不保證是 repo root，官方支援子目錄啟動；相對解析曾被 `../.agents/...` 繞過，
# codex BI 審查 Critical）。patch 相對路徑仍以 session cwd 為基準 resolve（apply_patch 語義）。
REPO_ROOT = Path(__file__).resolve().parent.parent
POOL_ROOTS = tuple(
    str(REPO_ROOT / rel) for rel in (".agents/memory", ".agents/memory-inbox", ".agents/memory-auto")
)
# 跨池共享層（spine）與家目錄偽池路徑——codex 為 spine 唯讀方（AIR-100 S-D＋live 探針
# 發現 codex 會探索 ~/.agents）：寫 spine＝污染所有 harness 共享的 user state；家目錄
# 偽池＝影子記憶目錄防禦。兩者皆 deny＋指針（有發現交 CC/ZCode 側 session）。
POOL_ROOTS += (
    str(Path.home() / ".agents/memory-spine"),
    str(Path.home() / ".agents/memory"),
)

DENY_MESSAGE = (
    "[Hook Blocked] 主體對 codex 唯讀——memory 寫入權威＝CC/ZCode 側 consolidation"
    "（D1 admission 唯一化）。\n"
    "有該寫的發現：以最終回報交 CC/ZCode 側 session，由主 session 走 consolidation"
    "（AGENTS.md 觀察池路由節）。\n"
    "本路徑由 codex_memory_path_deny.py 機械擋下（AIR-100 S-A path-deny）。"
)
FAIL_CLOSED_MESSAGE = (
    "[Hook Blocked] codex_memory_path_deny fail-closed：payload 不可判定"
    "（admission 門 deny 非 fail-open——D3；codex 對非 0/2 exit 按 hook failure"
    " 續行工具呼叫，故本門一律 exit 2）。"
)


def extract_patch_paths(command):
    """從 patch 文本抽寫入座標（Add/Update/Delete File＋Move to；出現順序）。

    路徑 `.strip()`（F-3）：吃掉行尾 `\r`（CRLF patch 文本）與首尾空白。
    """
    paths = []
    for m in PATCH_PATH_RE.finditer(command or ""):
        paths.append((m.group(1) or m.group(2)).strip())
    return paths


def _resolve(path, cwd):
    p = Path(path)
    if not p.is_absolute():
        p = Path(cwd) / p
    return p.resolve()


def violation(paths, cwd):
    """回第一個落池根的寫入座標（顯示形）；全數池外回 None。

    containment＝resolve 後相等或 root 在 parents（delimiter-aware——sibling
    `memory-x` 不誤傷；與 memory-audit path contract ③ 同界）。
    """
    roots = [(_resolve(root, cwd)) for root in POOL_ROOTS]
    for raw in paths:
        resolved = _resolve(raw, cwd)
        for root in roots:
            if resolved == root or root in resolved.parents:
                return raw
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"{FAIL_CLOSED_MESSAGE}\n詳情：stdin parse error: {exc}", file=sys.stderr
        )
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"{FAIL_CLOSED_MESSAGE}\n詳情：payload 非 dict", file=sys.stderr)
        sys.exit(2)
    # F-5 防禦深度：非 apply_patch 工具不歸本 hook 管（註冊 matcher 已過濾，
    # 此為第二道）。tool 名取自 payload——缺席/非字串時不早退，照走後續檢查
    # （無法判定≠可放行判定）。
    tool_name = data.get("tool_name")
    if isinstance(tool_name, str) and tool_name != "apply_patch":
        sys.exit(0)
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(
        tool_input.get("command"), str
    ):
        print(
            f"{FAIL_CLOSED_MESSAGE}\n詳情：tool_input.command 缺失或非字串",
            file=sys.stderr,
        )
        sys.exit(2)
    command = tool_input["command"]
    if not command:
        sys.exit(0)
    cwd_raw = data.get("cwd")
    cwd = cwd_raw if isinstance(cwd_raw, str) and cwd_raw else os.getcwd()  # F-1：缺席退 process cwd
    hit = violation(extract_patch_paths(command), cwd)
    if hit:
        print(f"{DENY_MESSAGE}\n命中座標：{hit}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
