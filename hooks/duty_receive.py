#!/usr/bin/env python3
"""dutymail 值星收信 hook 前導（AIR-254.3 S2）。

薄前導：stdin payload（SessionStart／UserPromptSubmit——值星在場的
interaction boundary）→ eligibility gate（cwd 在 repo 內，AIR-233 模式
——不過＝零查詢零輸出）→ session_id 取自 payload（per-session holder
state key）→ 載入 scripts/duty_receive 核心（檔案路徑顯式載入——
hooks/ 與 scripts/ 同 repo，核心單一源不複製）→
hookSpecificOutput.additionalContext 輸出（sync；
與 AIR-233 hook 同形）。核心邏輯（holder／prepare／triage／ack、
default-deny 分診表、絕不 flush-ack）單一源＝scripts/duty_receive.py。

決策表（hook 運作面；stdout 皆協議 JSON 或空）：

| 情境 | stdout | exit |
|---|---|---|
| 新到信件（digest＋surface 項） | hookSpecificOutput | 0 |
| 無新信（空批次）／無 session_id | 空（安靜） | 0 |
| eligibility gate 不過（cwd 在 repo 外） | 空（零查詢零輸出） | 0 |
| store 缺席（face class 4 storage） | 空＋stderr 一行註記 | 0 |
| 其他 face 失敗（含 shape 漂移） | 空＋stderr 註記帶錯誤摘要 | 0 |
| holder 衝突（live holder 在場／rebind CAS 失敗——皆不搶不重試） | 衝突訊息行（surface） | 0 |
| stdin 壞 JSON／缺或未知事件 | 空（fail-soft） | 0 |
| config 缺席／壞形 | 空＋stderr 註記 | 3（fail-loud——配置錯誤要大聲） |
| 註冊 args 誤用（argparse 拒絕） | 空（stderr 用法） | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

ack（唯一 cursor 前進邊）由 commit closure 在 stdout 寫出成功後執行
（advance-after-emit：先呈報後 ack）；ack 失敗不擋 turn——state 保留
處置紀錄，下輪先試 ack（冪等）或重 prepare（寧重不漏）。

本 hook 不觸達 send／replies 面（v1 絕不主動送信）；只掛值星在場的
兩事件，無 session＝零查詢零輸出（閒置完全安靜）。部署 runtime＝
governance-resolved Python 3.12（hooks/AGENTS.md 部署紀律——本 hook
非 sc-router canonical 條目，獨立 group 註冊；部署＝marshal 職責）。
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

# 核心單一源＝scripts/duty_receive.py——以檔案路徑顯式載入（自建模組名
# _duty_receive_core，不進 sys.modules["duty_receive"]）：sys.path dance 下
# `import duty_receive` 在 scripts/ 已在 path 時會解析回 hooks/ 自己
# （同名 circular import），對 scripts/ 的 path 依賴整段退役。
_core_spec = importlib.util.spec_from_file_location(
    "_duty_receive_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(core)

HOOK_TAG = core.HOOK_TAG
SUPPORTED_EVENTS = ("SessionStart", "UserPromptSubmit")


# ── monitor eligibility gate（AIR-233 模式：cwd/workspace 鎖）────────


def script_repo_root():
    """hook script 所在 repo 根（registrations 以絕對路徑引用本目錄
    腳本；repo 根＝hooks/ 上一層。測試 monkeypatch 此函式換鎖）。"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_eligible(cwd):
    """合法 invocation 判定：session cwd（payload `cwd`）必須在 script
    所在 repo 內。fail-closed——cwd 缺席／非字串／repo 外皆 False（
    gate 不過＝零查詢零輸出，防錯誤 session 消費信件）。"""
    if not isinstance(cwd, str) or not cwd:
        return False
    root = script_repo_root()
    real = os.path.realpath(cwd)
    return real == root or real.startswith(root + os.sep)


def _default_config_path():
    return os.path.join(
        script_repo_root(), "governance", "dutymail-processor.toml"
    )


def run(raw, address, runner=None, state_dir=None, config_path=None,
        now_us=None):
    """stdin 原文 → (exit_code, stdout, commit | None)。

    永不 raise、exit 恆 0（唯二例外：config 壞形＝3 fail-loud；args
    誤用由 argparse exit 2）。runner／state_dir／config_path／now_us
    可注入（測試 fake face＋fake state，不碰真 store）。commit＝ack
    closure——呼叫端在 stdout 寫出成功後才執行（advance-after-emit）。
    """
    runner = runner if runner is not None else core._default_runner
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0, "", None
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS:
            return 0, "", None
        if not is_eligible(payload.get("cwd")):
            return 0, "", None
        session_id = compat.session_id(payload)
        if not session_id:
            return 0, "", None
        try:
            policy = core.load_policy(
                config_path if config_path is not None
                else _default_config_path()
            )
        except core.ConfigError as exc:
            print(
                f"[{HOOK_TAG}] config fail-loud（{exc}）", file=sys.stderr
            )
            return 3, "", None
        state_file = core.state_path(session_id, state_dir)
        try:
            lines, commit = core.process_once(
                address, runner, policy, state_file, now_us=now_us
            )
        except core.HolderConflict as exc:
            lines, commit = [f"[{HOOK_TAG}] {exc}"], None
        except core.DutymailFaceError as exc:
            kind = (
                "store 缺席（pre-migration）" if exc.is_storage
                else "dutymail face 失敗"
            )
            print(
                f"[{HOOK_TAG}] fail-soft：{kind}——{exc}", file=sys.stderr
            )
            return 0, "", None
        out = ""
        if lines:
            out = json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event_name,
                        "additionalContext": "\n".join(lines),
                    }
                },
                ensure_ascii=False,
            )
        return 0, out, commit
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail 值星收信 hook 前導（AIR-254.3；SessionStart／"
            "UserPromptSubmit sync 兩事件）"
        )
    )
    parser.add_argument(
        "--address", required=True, metavar="ALIAS",
        help="門牌 alias（exact match；由註冊條目顯式宣告）",
    )
    parser.add_argument(
        "--config", default=None, metavar="PATH",
        help="分診表路徑覆寫（預設 repo 根 governance/"
        "dutymail-processor.toml）",
    )
    parser.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="holder state 目錄覆寫（預設 XDG state——診斷用）",
    )
    return parser.parse_args(argv)


def main(argv=None, runner=None) -> int:
    args = parse_args(argv)
    code, out, commit = run(
        sys.stdin.read(), args.address,
        runner=runner, state_dir=args.state_dir,
        config_path=args.config,
    )
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if code != 0:
        return code
    if commit is not None:
        try:
            commit()  # advance-after-emit：stdout 寫出成功後才 ack
        except Exception as exc:  # 寧重不漏——不擋 turn
            print(
                f"[{HOOK_TAG}] ack 失敗——state 保留處置紀錄，下輪先試"
                f" ack（{exc!r}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
