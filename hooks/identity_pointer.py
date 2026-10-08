#!/usr/bin/env python3
"""identity pointer hook 前導（AIR-286）——PreToolUse 寫 per-cwd session 指針.

薄前導：stdin payload（session_id＋cwd——ZCode 通用欄位，
ref-docs/harness/zcode/cn/docs/hooks.md stdin 輸入契約）→ 鍵值正規化
（hook_payload_compat.session_id 雙讀）→ 載入 scripts/session_discovery
核心（檔案路徑顯式載入——duty_receive 同款；**指針路徑／schema／TTL
單一源＝scripts/session_discovery.py**，本檔零複製定義）→
core.write_identity_pointer（atomic 寫、0600/0700、last-writer-wins）。

註冊面＝governance/registrations/zcode.json PreToolUse 無 matcher 條目
（匹配全部工具——心跳完備：純 Read/Edit 活動也更新活躍度）。**省略
matcher 而非收窄 Bash-only**：whoami 經 Bash 呼叫，該 Bash 自己的
PreToolUse 先於其執行——「讀前自寫」性質令 in-session 主消費路徑閉合；
全工具 matcher 使此性質與活躍度觀測對所有工具成立。禁 async（fire-and-
forget 無 happens-before 保證）。

決策表（advisory——AIR-135 條 3；hook 在每次工具呼叫熱路徑上）：

| 情境 | stdout | stderr | exit |
|---|---|---|---|
| payload 含 session_id＋cwd（寫入成功或失敗） | 空 | 空 | 0 |
| 壞 JSON／空 stdin／非 dict | 空 | 空 | 0 |
| 缺 session_id／缺 cwd／非字串或空值 | 空 | 空 | 0 |
| 核心載入失敗／寫入 OSError | 空 | 空 | 0 |

**恆 (0, "", 全靜默)**——降級可觀測性由 whoami 讀側 `identity_source`
標記承擔（scripts/session_discovery.py `_whoami_raw`），寫側零噪音。
membership 機驗（sid 在 store、subagent 排除）在讀側——本 hook 不查
store（熱路徑零查詢）。部署 runtime＝governance-resolved Python 3.12
（hooks/AGENTS.md 部署紀律）；本檔 syntax 保留 3.9 parse 相容
（rollback floor，test_governance_check 3.9 gate 涵蓋）。模板在場≠live
已部署——啟用須 governance installer 安裝＋新 session 驗證。
"""

import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)  # hook_payload_compat（hooks/ 同目錄）
import hook_payload_compat as compat


def _load_core():
    """核心單一源＝scripts/session_discovery.py——以檔案路徑顯式載入
    （自建模組名，不進 sys.modules；duty_receive 前導同款）。"""
    spec = importlib.util.spec_from_file_location(
        "_session_discovery_identity_core",
        os.path.join(_REPO, "scripts", "session_discovery.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_writer(state_dir=None):
    """writer factory（測試注入 state_dir 用；生產路徑由 run() 內建）。"""
    core = _load_core()
    return lambda sid, cwd: core.write_identity_pointer(sid, cwd, state_dir=state_dir)


def run(raw, writer=None):
    """stdin 原文 → (exit_code, stdout)。**恆 (0, "")**——任何失敗
    （壞 JSON／缺欄位／核心載入／OSError）皆靜默吞掉（advisory 護甲）。"""
    try:
        payload = json.loads(raw) if raw and raw.strip() else None
        if isinstance(payload, dict):
            sid = compat.session_id(payload)
            cwd = payload.get("cwd")
            if (
                isinstance(sid, str)
                and sid
                and isinstance(cwd, str)
                and cwd
            ):
                if writer is None:
                    writer = make_writer()
                writer(sid, cwd)
    except Exception:
        pass  # advisory——恆靜默放行（fail-open 對齊 zcode_agent_background_gate）
    return 0, ""


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    _code, out = run(raw)
    if out:  # 現契約恆空——保留防禦性寫出點
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
