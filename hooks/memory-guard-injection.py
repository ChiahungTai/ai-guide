#!/usr/bin/env python3
"""AIR-187 S1b——memory 寫入面注入偵測 hook（高精度子集、fail-open 觀察面）。

定位（tri 定案「閘快拒、審終判」的 hook 側）：只吃 S1 規則（scripts/
memory_guard_rules.py）的高精度 black 子集——冒充系統提示／角色指派特徵組
（BLACK_SIGNALS 之 impersonation：`system:`／`developer:`／`assistant:` 行首、
`you are` 指派形、disregard previous／忽略前文／以下指示優先／act as／
扮演＋冒充語境共現）。低精度訊號（gate 語彙 cooccur／一般祈使／directive
citation）不進 hook——hook 誤傷代價高，廣譜與語義終判歸 memory-audit skill
「注入安全」機械化消費面（LLM）。本 hook 不攔截任何寫入：deny 形態掛 S2
觀察數據後另弧。

行為契約
────────
- 輸入：hook payload JSON（stdin）。tool_name ∈ {Edit, Write} 且 file_path
  是池條目（memory_hook_common.is_pool_entry——與 memory-write-sensor.py
  同入口認定，MEMORY.md／`_` 前綴排除）才掃描；Write 掃 content 全文
  （含 frontmatter——desc 是常駐注入面），Edit 掃 new_string（新入文本；
  old_string 是既有內容不掃）。
- 命中（高精度 black）：stderr 大聲（路徑＋行號＋節錄＋終判指針）＋emit
  持久事件（kind="injection_guard_hit"，log 契約＝memory_hook_common——
  S2 deny 弧的觀察數據源）＋exit：
  - hook_event_name=PostToolUse（建議掛載形態）→ exit 2：CC 語義＝
    非阻斷（工具已執行、無可擋）、stderr 餵回模型——觀察面最響通道；
    ZCode 端 PostToolUse exit 2 語義未實證，最壞 transcript-only
    （fail-open；持久證據在 emit JSONL）。
  - hook_event_name=PreToolUse → exit 0＋stderr：純觀察。禁把本檔以
    「PreToolUse＋exit 2」形態註冊——那是 deny（阻擋）語義，非本弧
    授權形態（deny 須 S2 數據支撐誤傷率後另弧裁定）。
- 未命中／非池條目／非 Edit|Write → exit 0 靜默。
- fail-open 語義：解析／執行任何錯誤 → exit 0——觀察面故障不得反寫工具
  流；且**偵測缺席≠安全**（見覆蓋邊界，本 hook 不是完整性宣稱）。

掛載建議（本弧只寫腳本不註冊——註冊歸 governance）
────────────────────────────────────────────────────
- 建議形態：PostToolUse、matcher `Edit|Write`——與 memory-write-sensor.py
  同款入口（S1b 掛載點候選承接）。PreToolUse 同 matcher 亦可（純觀察
  exit 0 形態；exit 語義分歧見行為契約）。
- 註冊落點＝governance/registrations/cc.json＋zcode.json（command=
  `{{HOOK_PYTHON}}`＋args `{{REPO}}/hooks/memory-guard-injection.py`），
  安裝經 `uv run python governance/install.py --surface hooks`；註冊模板
  與 runtime 解析單一源＝hooks/AGENTS.md「註冊維護與 runtime」。
- runtime：系統 python3 3.9 相容語法（rollback floor；部署 interpreter
  由 governance {{HOOK_PYTHON}} 解析）。

runtime 方案論證（為何複製 regex 而非 import／subprocess）
──────────────────────────────────────────────────────────
- import memory_guard_rules：該模組 runtime 契約＝uv run ≥3.10（PEP 604
  union 註解在 3.9 module exec 即 TypeError），sys.path 注入救不了語法面；
  本弧邊界亦禁改其註解（S1 產物凍結）。
- subprocess `uv run`：牴觸 hooks/AGENTS.md runtime 紀律——hook fire 不
  呼叫 uv、不依賴 user shell PATH／project discovery／uv cache；且每次
  寫入多一趟 process＋uv 專案解析延遲，uv 缺席機器直接失效。
- 複製（採用）：高精度子集＝兩個 regex 常數逐字複製＋指回單一源；drift
  防護＝tests/test_memory_guard_injection_hook.py 同步釘（pattern 字串
  與 flags 相等＋「hook 命中恆 ⊆ S1 black」行為子集，golden 全量驗證）
  ＋改單一源時 rg "IMPERSONATION_RE"／"PAST_FRAME_RE" 掃本檔同步
  （single-source drift 防護）。

覆蓋邊界（fail-open 的另一半——偵測缺席≠安全）
──────────────────────────────────────────────
- AIR-93 teardown 原生寫入不經 tool 層——本 hook 天然攔不到（dossier
  §2）；池面重放偵測歸 reconcile exit-2 quarantine（scripts/
  reconcile_memory_pool.py）＋memory-audit「Inbox 消費」終判。
- subagent 寫入不觸發 hook（ZCode 實證，同 memory sensor 家族）；Bash
  redirect／MCP 寫入面不可見。
- 高精度子集刻意犧牲 recall：cooccur／一般祈使／directive citation 形
  payload 不在此面（S1 全譜在 classify_detail）。

單一源指回：scripts/memory_guard_rules.py（S1 規則定義源）；memory-audit
skill「注入安全」節（終判語義）；本檔＝寫入瞬間觀察面實作。
測試：tests/test_memory_guard_injection_hook.py（合成輸入＋同步釘）。
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_hook_common import emit, is_pool_entry, utc_now

# ==== 高精度子集（逐字複製自 scripts/memory_guard_rules.py——單一源，此處禁改判）====
# 單一源：BLACK_SIGNALS 之 ("primary", "impersonation", …) 特徵組＋
# _PAST_TENSE_FRAME（S1 演算法步驟 0：過去式完成框架先於 primary 黑——記載形
# 豁免，例「system: 冒充形已於 09-14 實證結案」不旗標）。改單一源必同步本檔
# （rg "IMPERSONATION_RE"／"PAST_FRAME_RE"）；機械防護＝tests/
# test_memory_guard_injection_hook.py 同步釘（字串＋flags 相等）。
IMPERSONATION_RE = re.compile(
    r"^\s*(?:system|developer|assistant)\s*[:：]"
    r"|you are (?:now |a |an )"
    r"|disregard (?:all |any |the )?(?:previous|prior|above|earlier)"
    r"|忽略(?:之前|以上|上文|先前)"
    r"|以下(?:指示|指令|規則)(?:優先|覆蓋|生效)"
    r"|\bact as\b"
    r"|(?=[^\n]*扮演)(?=[^\n]*(?:you are|你|(?:system|developer|assistant)\s*[:：]))",
    re.IGNORECASE,
)
PAST_FRAME_RE = re.compile(r"已於|曾於|實證|結案|已落地|已上線|已退役|終態|考古")

EXCERPT_CHARS = 100  # stderr／事件節錄上限——大聲但不傾印全文


def scan_lines(text):
    """逐行掃高精度子集；回 [(1-based 行號, 命中行節錄)]。

    語義＝S1 演算法步驟 0–1 投影到 impersonation 單訊號：過去式完成框架
    先豁免（步驟 0），其後 impersonation 命中即旗標（步驟 1——primary 黑
    壓過白框架，故本 hook 不帶白豁免表）。hook 命中恆 ⊆ S1 black 判定
    （同步釘釘此性質）。
    """
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if PAST_FRAME_RE.search(line):
            continue
        if IMPERSONATION_RE.search(line):
            hits.append((lineno, line.strip()[:EXCERPT_CHARS]))
    return hits


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return 0
    try:
        if not isinstance(data, dict):
            return 0
        tool = data.get("tool_name")
        if tool not in ("Edit", "Write"):
            return 0
        tool_input = data.get("tool_input") or {}
        canon = is_pool_entry(tool_input.get("file_path", ""))
        if canon is None:
            return 0
        text = tool_input.get("content") if tool == "Write" else tool_input.get("new_string")
        if not isinstance(text, str) or not text:
            return 0
        hits = scan_lines(text)
        if not hits:
            return 0
        event_name = str(data.get("hook_event_name") or "")
        detail = "\n  ".join(f"L{lineno}: {excerpt}" for lineno, excerpt in hits)
        print(
            f"[memory-guard-injection] 高精度注入特徵命中 {len(hits)} 行"
            f"（S1 impersonation 子集——觀察非阻擋）：{canon}\n"
            f"  {detail}\n"
            "  終判＝memory-audit skill「注入安全」機械化消費面（classify_detail 來源分層）；"
            "池面重放歸 reconcile exit-2 quarantine。定義源＝scripts/memory_guard_rules.py。",
            file=sys.stderr,
        )
        emit(
            {
                "kind": "injection_guard_hit",
                "ts": utc_now(),
                "event": event_name,
                "session_id": data.get("session_id"),
                "tool": tool,
                "file_path": canon,
                "hits": [{"line": n, "excerpt": e} for n, e in hits],
            }
        )
        if event_name == "PostToolUse":
            # CC：PostToolUse exit 2＝非阻斷（工具已執行）＋stderr 餵回模型——
            # 觀察面最響通道；ZCode 端語義未實證（fail-open，證據在 emit JSONL）
            return 2
        # PreToolUse mount＝純觀察；exit 2 在 Pre 是 deny 語義，非本弧授權形態
        return 0
    except Exception:
        return 0  # fail-open：觀察面故障不得反寫工具流


if __name__ == "__main__":
    raise SystemExit(main())
