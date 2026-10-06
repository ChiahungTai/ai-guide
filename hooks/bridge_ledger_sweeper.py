#!/usr/bin/env python3
"""bridge ledger sweeper hook 前導（AIR-267）。

薄前導：stdin payload（SessionStart／UserPromptSubmit——收線 backstop 的
interaction boundary）→ boundary 判定＋session_id 取自 payload → importlib
載入 scripts/bridge_sweeper 核心（檔案路徑顯式載入——hooks/ 與 scripts/
同 repo，核心單一源不複製；載入點在 run() 內 lazy cache（J-3：載入失敗
＝fail-soft，非 duty_receive 的 module-level 形））→
hookSpecificOutput.additionalContext 輸出（sync；duty 家族同形）。核心邏輯
（兩態偵測／節流／signature 去重／唯讀面）單一源＝scripts/bridge_sweeper.py
（invariants 見該檔 module docstring）。

決策表（hook 運作面；stdout 皆協議 JSON 或空）：

| 情境 | stdout | exit |
|---|---|---|
| 偵測命中且值變化（R1/R2 advisory） | hookSpecificOutput | 0 |
| 乾淨／同 signature／節流窗內／eligibility gate 不過／缺 session_id | 空（零查詢） | 0 |
| face 失敗（runs 面／binary 缺席／壞形／內層逾時） | 空＋stderr 註記 | 0 |
| 核心載入失敗（scripts/bridge_sweeper.py 檔缺/語法錯——J-3） | 空＋stderr 註記 | 0 |
| liveness 台帤缺席（R2 退化——R1 照跑） | 視 R1 而定＋stderr 註記 | 0 |
| stdin 壞 JSON／缺或未知事件 | 空（fail-soft） | 0 |
| 註冊 args 誤用（argparse 拒絕） | 空（stderr 用法） | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

sweeper 只出一行級 advisory（值變化才出聲）——處置（arm/show/收線）恆歸
session LLM；絕不 arm/stop/寫 liveness/寫 ledger（提醒面非處置面）。
state 推進（節流窗＋signature baseline）advance-after-emit：stdout 寫出
成功後才 commit；寫失敗寧可下輪重掃（寧重不漏）。部署 runtime＝
governance-resolved Python 3.12（hooks/AGENTS.md 部署紀律）；全檔維持
Python 3.9 語法相容（mixed-session／rollback 窗期）。
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

# 字面鏡像 core.HOOK_TAG——核心載入失敗（檔缺/語法錯）時 stderr 註記仍可
# 標名出處（J-3：import 邊界也在 fail-soft 界內）。
HOOK_TAG = "bridge-sweeper"
SUPPORTED_EVENTS = ("SessionStart", "UserPromptSubmit")

# 核心單一源＝scripts/bridge_sweeper.py——以檔案路徑顯式載入（自建模組名
# _bridge_sweeper_core，不進 sys.modules：duty_receive hook 同款形態）。
# J-3：載入移入 run() 的 try 內（lazy cache）——module-level 載入會把
# 檔缺/語法錯炸成 traceback exit 1，擋 prompt 面；fail-soft 界內吸收。
_core_cache = None


def _core_module():
    global _core_cache
    if _core_cache is None:
        spec = importlib.util.spec_from_file_location(
            "_bridge_sweeper_core",
            os.path.join(_REPO, "scripts", "bridge_sweeper.py"),
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("core spec 不可載入（bridge_sweeper.py）")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _core_cache = module
    return _core_cache


def run(raw, runner=None, state_dir=None, liveness_path=None):
    """stdin 原文 → (exit_code, stdout, commit | None)。

    永不 raise、exit 恆 0（唯一例外＝註冊 args 誤用由 argparse exit 2）。
    runner／state_dir／liveness_path 可注入（測試 fake face＋fake state，
    零真 bridge 呼叫）。事件名／session_id 經 hook_payload_compat 正規化
    （grok snake 值同款處理；防禦性相容）。"""
    try:
        core = _core_module()  # J-3：載入失敗＝fail-soft（stderr＋零 stdout）
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0, "", None
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS:
            return 0, "", None
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0, "", None  # eligibility fail-closed（core 再驗）
        session_id = compat.session_id(payload)
        lines, commit = core.run_hook(
            event_name,
            cwd,
            session_id,
            runner=runner,
            state_dir=state_dir,
            liveness_path=liveness_path,
        )
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
    except Exception as exc:  # fail-soft by design——絕不擋 prompt
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "bridge ledger sweeper hook 前導（AIR-267；SessionStart／"
            "UserPromptSubmit sync 兩事件——唯讀提醒面）"
        )
    )
    parser.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="節流 state 目錄覆寫（預設 XDG state——診斷用）",
    )
    return parser.parse_args(argv)


def main(argv=None, runner=None):
    args = parse_args(argv)
    code, out, commit = run(
        sys.stdin.read(),
        runner=runner,
        state_dir=args.state_dir,
    )
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if code != 0:
        return code
    if commit is not None:
        try:
            commit()  # advance-after-emit：stdout 寫出成功後才推進 state
        except Exception as exc:  # 寧重不漏——推進失敗不擋 turn
            print(
                f"[{HOOK_TAG}] state 寫入失敗——節流/去重不推進，下輪重掃"
                f"（{exc!r}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
