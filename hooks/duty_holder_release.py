#!/usr/bin/env python3
"""dutymail holder release hook 前導（AIR-288 judge MF1(i)——bridge
item 6(a) SessionEnd 面）。

薄前導：stdin payload（SessionEnd——session 終局邊界）→ session_id
（per-session holder state key，與收信 hook 同源）→ 載入
scripts/duty_receive 核心（檔案路徑顯式載入——單一源不複製）→
`release_holder`：以 state 檔的 live token 呼 `dutymail holder release
--address --token`（fencing 未 ack 批次、交回消費權威——bridge 契約
「Clean shutdown is release — not walking away」；3.8.0 拔 renew 後
session 結束不釋出＝binding active 恆存＝下一班 session 冷啟即
HolderConflict、收信面停擺——release 是正常生命週期非邊角）→ 成功後
state 檔移除（session 終局；下一 session 冷啟 rebind、寧重不漏吸收
fenced 批）。

**fail-soft by design：release 失敗不擋 session 收尾**——exit 恆 0、
失敗只 stderr 一行；釋出失敗的殘局由 ZCode 面 death-evidence takeover
兜底（單一源＝scripts/duty_receive.py `_holder_death_evidence`——ZCode
無 SessionEnd 事件〔harness 限制〕，本 hook 只掛 codex/grok 面，
註冊單一源＝governance/registrations/{codex.toml,grok.json}）。

決策表（hook 運作面；stdout 恆空——SessionEnd 無 additionalContext
通道）：

| 情境 | stderr | exit |
|---|---|---|
| SessionEnd＋state 有 live token → release＋state 移除 | 一行（已釋出） | 0 |
| 無 state／無有效 token（從未值星／已釋） | 靜默 | 0 |
| release face 失敗（含 shape 漂移） | fail-soft 一行（state 保留） | 0 |
| --address 給定且與 state address 不符 | 拒釋一行（防跨 address 誤釋——state dir 跨 checkout 共享） | 0 |
| stdin 壞 JSON／缺或未知事件／無 session_id | 靜默 | 0 |

刻意不做 cwd eligibility gate（收信 hook 有）：SessionEnd payload 的
cwd 在各家 harness 面最不標準化，而 release 以 session_id→state 存在
性自限——沒值過星就沒 state，釋不了別人的權威；`--address` 吻合檢查
再加一層跨 address 誤釋防護。

部署 runtime＝governance-resolved Python 3.12；部署＝marshal 職責
（governance install——codex/grok SessionEnd 條目隨 manifest 落地）。
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

# 核心單一源＝scripts/duty_receive.py（同 hooks/duty_receive.py 前導
# 模式——檔案路徑顯式載入，sys.path dance 下不解析回同名 hook）。
_core_spec = importlib.util.spec_from_file_location(
    "_duty_receive_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(core)

HOOK_TAG = core.HOOK_TAG
SUPPORTED_EVENTS = ("SessionEnd",)


def run(raw, runner=None, state_dir=None, address=None):
    """stdin 原文 → (exit_code, stdout)。

    永不 raise、exit 恒 0（fail-soft——release 失敗不擋 session 收尾）。
    runner／state_dir／address 可注入（測試 fake face＋fake state，不碰
    真 store）。address（註冊面顯式宣告）：給定且與 state address 不符
    ＝拒釋。stdout 恆空（SessionEnd 無輸出通道）。
    """
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0, ""
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS:
            return 0, ""
        session_id = compat.session_id(payload)
        if not session_id:
            return 0, ""
        state_file = core.state_path(session_id, state_dir)
        if address is not None:
            st = core.load_state(state_file)
            if st is not None and st.get("address") != address:
                print(
                    f"[{HOOK_TAG}] release 拒釋——state address"
                    f"（{st.get('address')!r}）與註冊 address"
                    f"（{address!r}）不符",
                    file=sys.stderr,
                )
                return 0, ""
        released = core.release_holder(runner, state_file)
        if released:
            print(
                f"[{HOOK_TAG}] holder released（清潔關閉釋出；"
                f"session {session_id}）",
                file=sys.stderr,
            )
        return 0, ""
    except core.DutymailFaceError as exc:
        print(
            f"[{HOOK_TAG}] release fail-soft（不擋 session 收尾；殘局由"
            f" death-evidence 接管兜底）——{exc}",
            file=sys.stderr,
        )
        return 0, ""
    except Exception as exc:  # fail-soft by design——絕不擋收尾
        print(
            f"[{HOOK_TAG}] release fail-soft（{exc!r}）", file=sys.stderr
        )
        return 0, ""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail holder release hook（AIR-288 MF1；SessionEnd 面"
            "——清潔關閉釋出消費權威）"
        )
    )
    parser.add_argument(
        "--address", default=None, metavar="ALIAS",
        help="門牌 alias（exact match；給定則與 state address 核對——"
        "不符拒釋；由註冊條目顯式宣告）",
    )
    parser.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="holder state 目錄覆寫（預設 XDG state——診斷用）",
    )
    return parser.parse_args(argv)


def main(argv=None, runner=None) -> int:
    args = parse_args(argv)
    _code, out = run(
        sys.stdin.read(), runner=runner, state_dir=args.state_dir,
        address=args.address,
    )
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
