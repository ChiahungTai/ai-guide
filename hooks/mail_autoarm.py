#!/usr/bin/env python3
"""mail auto-arm advisory hook 前導（AIR-318——夜間通信鏈 v1 SessionStart 面）。

一句話：session 開場檢查本 repo 的信件喚醒哨是否在場，缺哨＝經
SessionStart additionalContext 印一行 advisory 提醒 session 執行 arm
流程——**hook 本身零背景程序、零 dutymail 呼叫、零 state 寫入（純讀
面）**；掛哨與否的處置權恆歸 session LLM（跑 `mail_waiter.py start`
並把印出的 worker 命令放上背景 shell——協議單一源＝skills/mail-watch；
本 hook 只提醒，advisory 非授權）。

opt-in marker（per-repo，三態同 marshal-governance 慣例——禁
fail-open）：
`<repo-root>/.agents/mail-autoarm.json`
- absent（檔不在）＝不啟用——零輸出 exit 0
- valid（JSON 物件且 `protocol == 1`；額外鍵容忍——前向相容）＝啟用
  → 偵測面
- malformed（壞 JSON／非物件／缺 protocol／protocol != 1）＝fail-loud
  提示修復——additionalContext 一行（stderr 同步註記）＋exit 0
  （SessionStart 不擋 session 啟動；「大聲」＝session context 可見，
  絕不靜默當 absent 吃掉）

偵測面（marker valid 時）：caller repo 身份（git common-dir 推導——
核心單一源＝scripts/duty_receive.py `caller_repo_address`，本檔經
scripts/mail_waiter.py 的 core 複用、身份與 state 佈局零複製；import
無循環——檔案路徑顯式載入，duty_receive 不反向依賴本檔）→ 唯讀該
repo 的 per-repo watcher state（`<XDG>/ai-guide/mail-waiter/<repo
編碼>/state.json`）：
- `desired=stopped`（user 停哨 flag 權威）→ 不動（靜默）
- armed_at 新鮮（< 輪詢週期×門牌數×3——判準單一源＝mail_waiter
  `_staleness_mark`）→ 不動（有活哨）
- 其餘（state 缺席／損壞／desired=running 但 stale／缺 armed_at）→
  印一行 advisory：「[mail-autoarm] 已為 <repo> 掛哨——請執行背景
  shell：<start 命令>（依 mail-watch 協議：start 後執行其印出的
  worker 命令）」（hook 唯讀無法代產 worker 命令——generation 由
  start 落定，故 advisory 帶的是 start 命令）

部署 runtime＝governance-resolved Python 3.12；全檔維持 Python 3.9
語法相容（hooks/AGENTS.md rollback floor）。決策表：

| 情境 | stdout | stderr | exit |
|---|---|---|---|
| stdin 壞 JSON／非 SessionStart／缺 cwd | 空 | 空 | 0 |
| marker absent | 空 | 空 | 0 |
| marker valid＋desired=stopped／有新鮮哨 | 空 | 空 | 0 |
| marker valid＋缺哨／stale | hookSpecificOutput advisory 一行 | 空 | 0 |
| marker malformed | hookSpecificOutput fail-loud 提示一行 | 同步一行 | 0 |
| 身份無法判定／核心載入失敗 | 空 | fail-soft 一行 | 0 |
| 註冊 args 誤用（argparse 拒絕） | 空 | 用法 | 2（大聲、刻意——bridge_ledger_sweeper 同款） |
"""

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)  # hook_payload_compat（hooks/ 同目錄）
import hook_payload_compat as compat

HOOK_TAG = "mail-autoarm"
SUPPORTED_EVENTS = ("SessionStart",)
MARKER_REL = os.path.join(".agents", "mail-autoarm.json")
MARKER_PROTOCOL = 1

# 核心單一源＝scripts/mail_waiter.py（watcher state 佈局＋staleness
# 判準＋身份核心〔其 .core＝scripts/duty_receive.py〕皆自彼複用）。
# 以檔案路徑顯式載入（自建模組名，不進 sys.modules——hooks/duty_receive.py
# 同名檔不誤解析）；J-3 lazy cache：載入移入 run() 的 try 內——module-level
# 載入會把檔缺/語法錯炸成 traceback exit 1 擋 session start，fail-soft
# 界內吸收（bridge_ledger_sweeper 同款）。
_core_cache = None


def _core_module():
    global _core_cache
    if _core_cache is None:
        spec = importlib.util.spec_from_file_location(
            "_mail_autoarm_waiter",
            os.path.join(_REPO, "scripts", "mail_waiter.py"),
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("core spec 不可載入（mail_waiter.py）")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _core_cache = module
    return _core_cache


def marker_state(repo_root):
    """marker 三態 → "absent" | "valid" | "malformed"。

    valid＝JSON 物件且 protocol == 1（bool 不算——True == 1 為 Python
    等值陷阱，顯式排除）；其餘在場形態＝malformed（禁 fail-open 當
    absent——三態同 marshal-governance 慣例）。"""
    path = os.path.join(repo_root, MARKER_REL)
    if not os.path.exists(path):
        return "absent"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return "malformed"
    if not isinstance(doc, dict):
        return "malformed"
    protocol = doc.get("protocol")
    if isinstance(protocol, bool) or protocol != MARKER_PROTOCOL:
        return "malformed"
    return "valid"


def _context(line):
    """SessionStart advisory envelope（bridge_ledger_sweeper 同形——
    hookSpecificOutput.additionalContext；單行）。"""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": line,
            }
        },
        ensure_ascii=False,
    )


def _start_command(waiter):
    """advisory 帶的 arm 命令（start 形）。hook 唯讀無法代產 worker 命令
    （generation 由 start 落定）——advisory 指 start，session 依
    mail-watch 協議接手：start 後執行其印出的 worker 命令上背景 shell。"""
    return "uv run python {} start".format(
        os.path.join(waiter._REPO, "scripts", "mail_waiter.py")
    )


def run(raw, state_dir=None):
    """stdin 原文 → (exit_code, stdout)。

    stdout＝SessionStart hookSpecificOutput JSON（advisory／fail-loud
    提示）或空。永不 raise、exit 恆 0（唯一例外＝argparse 誤用 exit 2）。
    state_dir 可注入（測試隔離——不碰真 XDG store）；零 dutymail 呼叫、
    零寫入。"""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0, ""
        if compat.hook_event_name(payload) not in SUPPORTED_EVENTS:
            return 0, ""
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0, ""
        waiter = _core_module()
        root = waiter.core._caller_primary_root(cwd)
        if root is None:
            return 0, ""  # 非 git cwd＝無 marker 可讀（fail-soft 靜默）
        state = marker_state(root)
        if state == "absent":
            return 0, ""
        if state == "malformed":
            hint = (
                "[{0}] fail-loud：marker {1} malformed（須 JSON 物件且 "
                "protocol=={2}）——修復或刪除該檔後新 session 生效；本 "
                "session 不自動掛哨"
            ).format(HOOK_TAG, os.path.join(root, MARKER_REL),
                     MARKER_PROTOCOL)
            print("[{0}] marker malformed：{1}".format(
                HOOK_TAG, os.path.join(root, MARKER_REL)), file=sys.stderr)
            return 0, _context(hint)
        identity = waiter.core.caller_repo_address(cwd)
        state_file = waiter.state_file_path(
            waiter.repo_state_dir(identity, state_dir)
        )
        doc = waiter.core.load_state(state_file)
        if doc is not None:
            if doc.get("desired") == "stopped":
                return 0, ""  # 停哨 flag 權威——不動
            mark, _age = waiter._staleness_mark(doc)
            if mark.startswith("fresh"):
                return 0, ""  # 有活哨——不動
        line = (
            "[{0}] 已為 {1} 掛哨——請執行背景 shell：{2}"
            "（依 mail-watch 協議：start 後執行其印出的 worker 命令）"
        ).format(HOOK_TAG, identity, _start_command(waiter))
        return 0, _context(line)
    except Exception as exc:  # fail-soft by design——絕不擋 session 啟動
        print("[{0}] fail-soft（{1!r}）".format(HOOK_TAG, exc),
              file=sys.stderr)
        return 0, ""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "mail auto-arm advisory hook（AIR-318；SessionStart 面——"
            "缺哨提醒，零背景程序零 dutymail 呼叫）"
        )
    )
    parser.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="watcher state 目錄覆寫（預設 XDG state——測試/診斷注入）",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    code, out = run(sys.stdin.read(), state_dir=args.state_dir)
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
