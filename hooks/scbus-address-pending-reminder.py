#!/usr/bin/env python3
"""scbus 門牌 pending 監看提醒 hook（AIR-225.1）——UPS 與 SessionStart 獨立提醒面。

實證缺口：門牌信（repo well-known durable address）寄達後只有 point-in-time
人工輪詢（值星開場 `scbus address ls --pending` 快照），無 liveness——「查完
才到信」的信躺到下個開場才被發現（AIR-225 漏接事故的 interaction-boundary
gap）。本 hook 在兩個 interaction boundary 補 monitor discovery 觸發：
UserPromptSubmit（每次 user 打字）與 SessionStart（session 回場）。單一 script
服務兩事件——stdin 的 hook_event_name 決定輸出的 hookEventName；兩註冊條目
皆 sync（無 async 鍵——additionalContext 通道 sync-only，async 輸出不影響
當前 turn；sc-router hooks_install v1.5 SC-206 同款結論）。

職責＝monitor 只讀 badge：執行 `scbus address ls --pending`（subprocess、
無 shell）、取 --address 指名門牌的 pending 計數，>0 才輸出 additionalContext
一行——內容只含 address＋數量＋操作指針。**禁 recv/ack/lease 操作**（monitor
≠ holder，governance/scbus-address-ownership.md「Holder ≠ monitor」）；
**禁注入命令原始 stdout**——上游對 holder-less 門牌（lease 過期）自帶首行
body preview（pending[].preview），原樣轉發即洩信件內容進 context；本 hook
輸出只取 address 與 count，連 envelope header 都不帶。

決策表（hook 運作面 stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用，見末行）：

| 情境                                             | stdout            | exit |
|--------------------------------------------------|-------------------|------|
| 指名門牌 pending>0（每門牌一行，可多行）          | hookSpecificOutput | 0   |
| pending=0／未傳 --address                        | 空（靜默）        | 0    |
| scbus 缺席／命令失敗／stdout 壞 JSON／門牌不在清單 | 空（fail-soft）   | 0    |
| stdin 壞 JSON／缺或未知 hook_event_name           | 空（fail-soft）   | 0    |
| pending 非 list（上游形契約漂移）                 | 空（fail-soft）   | 0    |
| 註冊 args 誤用（argparse 拒絕）                   | 空（stderr 用法）  | 2（大聲、刻意——misconfig 歸註冊單一源修復，不走 fail-soft） |

fail-soft 契約（繼承 L2 drain 面）：ZCode 讀 exit 2 為「擋 turn」、非 JSON
stdout 餵 hook-output parser——exit 0＋零 stdout 是唯一安全靜默形（上游毒信
envelope_corrupt 會使 listing 整命令失敗，本 hook 對應靜默，絕不擋 turn）。

監看面邊界：本 script 不 hardcode 門牌——--address 可重複，monitor
subscription 由各 repo 註冊條目顯式宣告（ai-guide 註冊 ai-guide-marshal 單
值）；binding_active 只代表 routing lease，不代表本 session 有監看責任，故
不掃全清單。人工輪詢（`scbus address ls --pending`）仍是 fallback
（hook 未註冊機器／fail-soft 靜默時），兩面語義見 ownership doc monitor 段。

ZCode 協議（ref-docs/harness/zcode hooks.md）：stdin 一行 JSON；只有去空白後
以 { 開頭的合法 JSON 被協議解析，hookSpecificOutput.additionalContext 注入
context；同源多 hook 按陣列順序執行（本條目為獨立 group，不與 sc-router
canonical scbus hook 條目或 compact-restore-inject group 同 group——sc-router
installer 以精確 command equality 認 ownership，包進 wrapper 會與其 repair
機制打架）。部署 runtime 由 governance installer 解析 uv-managed Python 3.12
（hooks/AGENTS.md）；mixed-session／rollback 窗期維持 Python 3.9 語法相容。
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_payload_compat as compat

HOOK_TAG = "scbus-monitor"
SCBUS_TIMEOUT_SECONDS = 8  # hook 條目 timeoutMs=10000；內層更短留收尾餘裕
SUPPORTED_EVENTS = ("UserPromptSubmit", "SessionStart")


def reminder_line(address, count):
    """單門牌提醒行——只含 address＋count＋指針＋禁權聲明（卡定款式）。"""
    return (
        "[" + HOOK_TAG + "] " + address + " pending=" + str(count)
        + "；監看請用 scbus address ls --pending。此提醒不授權 recv/ack/acquire"
    )


def _default_runner(argv):
    """真實 scbus 呼叫（無 shell）；非零 exit＝失敗（raise → fail-soft）。"""
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=SCBUS_TIMEOUT_SECONDS,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[:200]
        raise RuntimeError("scbus exit " + str(proc.returncode) + ": " + detail)
    return proc.stdout


def query_counts(addresses, runner=None):
    """`scbus address ls --pending` → {address: count}（只含指名門牌）。

    任何錯誤（缺席／非零 exit／壞 JSON／形狀不符／指名門牌不在清單）一律
    raise——由 run() 的 fail-soft 吸收成靜默。pending header（envelope_id/
    from/mode/preview…）在此層即丟棄，只留計數——上游 preview 欄位進不了
    輸出（語義邊界的結構性防線，非約定俗成）。
    """
    run = runner if runner is not None else _default_runner
    out = run(["scbus", "address", "ls", "--pending"])
    doc = json.loads(out)
    if not isinstance(doc, dict) or not isinstance(doc.get("addresses"), list):
        raise TypeError("scbus listing unexpected shape")
    by_address = {}
    for entry in doc["addresses"]:
        if isinstance(entry, dict) and isinstance(entry.get("address"), str):
            by_address[entry["address"]] = entry
    counts = {}
    for address in addresses:
        entry = by_address.get(address)
        if entry is None:
            raise LookupError("address not in listing: " + address)
        pending = entry.get("pending")
        if not isinstance(pending, list):
            # 形契約漂移（上游 pending 非 list）不靜默歸零——raise 交 fail-soft
            # 統一路徑（零 stdout exit 0＋stderr 診斷），禁吞成 pending=0。
            raise TypeError(
                "pending not a list for address " + address
                + " (got " + type(pending).__name__ + ")"
            )
        counts[address] = len(pending)
    return counts


def build_output(event_name, addresses, runner=None):
    """pending>0 → hookSpecificOutput JSON；其餘情境回空字串（靜默）。"""
    counts = query_counts(addresses, runner=runner)
    lines = [
        reminder_line(address, counts[address])
        for address in addresses
        if counts[address] > 0
    ]
    if not lines:
        return ""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": "\n".join(lines),
            }
        },
        ensure_ascii=False,
    )


def run(raw, addresses, runner=None):
    """stdin 原文 → (exit_code, stdout payload)。永不 raise、exit 恆 0。

    addresses＝註冊條目 --address 累積值（可重複；空＝無監看責任，靜默且
    不呼叫 scbus）。事件名經 hook_payload_compat 正規化（grok snake 值同款
    處理；本 hook 僅註冊 zcode/cc 面，正規化為防禦性相容非註冊面宣稱）。
    """
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise TypeError("stdin not a JSON object")
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS or not addresses:
            return 0, ""
        return 0, build_output(event_name, addresses, runner=runner)
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(HOOK_TAG + ": fail-soft（" + repr(exc) + "）", file=sys.stderr)
        return 0, ""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="scbus 門牌 pending 監看提醒（AIR-225.1；sync 兩事件）"
    )
    parser.add_argument(
        "--address",
        action="append",
        default=[],
        metavar="ADDR",
        help="要監看的門牌（可重複；由註冊條目顯式宣告，script 不 hardcode）",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    _code, out = run(sys.stdin.read(), args.address)
    if out:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
