#!/usr/bin/env python3
"""dutymail 值星收信 hook 前導（AIR-254.3 S2）——**RETIRED＋inert no-op
（AIR-312 R1 M1）**。

SessionStart／UserPromptSubmit 自動收信註冊已退役（governance
registrations 零本腳本條目；manifest hooks surface 除名）。本檔保留
可執行入口，但行為＝**零副作用 no-op**：任何事件、任何地址（canonical
新址／`<repo>-marshal` 舊址）皆 exit 0＋零 stdout＋零 dutymail face
呼叫（status／bind／prepare／ack 全不觸）＋零 holder state／
disposition ledger／sidecar 寫入。重掛本 hook＝違反 AIR-312 退役裁定
（普通 inbox 模型：不自動處理信）；現行信件消費＝S2 消費整合
（pending，見 skills/mail-handle）。

**為什麼留 no-op 而非刪檔（stale session snapshot 邊界）**：ZCode 於
session 啟動取得 hook 註冊快照——在 operator 升級（governance
installer `--prune-stale` 移除 stale 註冊，程序見 hooks/AGENTS.md）
**之前**啟動的 session 仍持舊註冊，會以絕對路徑繼續呼叫本檔直到該
session 結束；檔案缺席＝每 prompt hook 報錯噪音。本 no-op 把殘留呼叫
吸收成零效（新 session snapshot＝零 duty 條目，不再觸發）。

歷史對照：舊址 receive 自 AIR-312 repo 身份制起被 custody fence 拒絕
（零 face 呼叫——舊址信件不曾被本 hook ACK）；canonical 新址的自動
收信亦隨同退役。內部 hook flow（core／disposition ledger 載入／
eligibility gate／per-session lock／sink factory）已整段移除——歷史
見 git log。duty_holder_release（SessionEnd 釋章）不屬本退役——照常。
3.9 語法相容（hooks/AGENTS.md rollback floor）。
"""

import sys


def main(argv=None, runner=None) -> int:
    """inert no-op：stdin 排空（防上游 EPIPE）後零輸出 exit 0。

    argv／runner 參數保留接受但完全忽略（舊註冊帶 --address <alias>
    呼叫、測試帶 fake runner 呼叫——兩者皆必須零效）。"""
    del argv, runner
    try:
        sys.stdin.read()  # 排空 stdin——內容一律不消費
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
