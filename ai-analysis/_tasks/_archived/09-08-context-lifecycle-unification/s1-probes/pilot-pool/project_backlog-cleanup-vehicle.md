---
name: project-backlog-cleanup-vehicle
description: backlog Done 欄清場每日 launchd 載體弧（ai-rules+mosaic 09-06
  上線）——ai-rules 腿已閉；殘項：mosaic twin brace 修正＋一檔 handoff 對方 session
metadata:
  node_type: memory
  type: project
  originSessionId: sess_67e0c1d8-0c00-4239-946f-694e9e86df4b
---

backlog Done 欄清場從「maintain 週期手動批次」升級為每日 launchd 自動腿（user 2026-09-06 裁定：寫成載體、每日跑、ai-rules 與 mosaic 都做）。設計語義單一源＝kanban-board SKILL.md 清理段＋schedule-registry.md（門檻 `Done`+`updated_date`>30d、逐卡 precheck→`task complete`→commit、多 worktree 全展開、precheck 跨 repo 依賴 ai-rules 絕對路徑、腳本 twin 副本改動須雙份同步）——細節以 repo 為準，本條不重複。

**殘項（弧末快照）**：ai-rules 三檔 commit（run-backlog-cleanup.sh＋schedule-registry.md＋kanban-board SKILL.md）停在驗證工單的預期落差——工單預期 codex worktree（`~/.codex/worktrees/8b3c/ai-rules`）列 `[WT] 0 張`，實際 `[skip-WT]（detached HEAD）`（該 WT 真 detached、skip 是腳本設計行為）；其餘 gate 全綠（syntax-ok、雙腳本 exit 0、零 `[moved]`/`[commit]`、三檔在場未被帶走），依「任一非預期→停」未 commit——user 裁定該行算預期即執行 add 三檔＋commit＋`rm .review/main.md`（該檔原樣未動）。ai-rules 腳本多位元組 9 位點已修 `${var}` 大括號；**mosaic twin 同型 9 位點未修**（dormant：三 WT 全在 branch，任一 detached 即炸）——twin 同步半套，併 mosaic 側處理。mosaic 一檔已 /handoff（user 當 dispatcher：「$handoff 過去，我叫他處理」——接收 session 只 commit 該檔、勿掃兩份外來 untracked report）。清場 commit 授權＝機械批次免逐次確認（user 09-06 裁定，建卡 commit 同型）。存量 Done 卡皆 <30d——上線首月 no-op 屬預期非故障。

**REST/UI 替代路徑已評估、不換載體（09-06）**：web board「Clean Up Completed Tasks」按鈕背後是 REST cleanup 端點（見 [[reference-backlog-md-browser-id-mechanics]]）——headless 自動化理論上可 curl 常駐 browser server，但腳本路線保留：①規則強制 precheck 治理閘（UI/REST 都不跑跨線掃描）②REST execute 吃年齡全批、不能逐卡跳過被擋卡③依賴 browser server 活著（腳本獨立成立）④版本面（文檔對應新版，1.50.1 endpoint 在場未驗）。UI 按鈕手動用 OK（人點＝在場協調者，precheck 防護目的已滿足）；提醒：UI/REST 搬完不 commit（auto_commit false），懸 working tree 到手動 commit 或夜間腳本 `git add backlog/` 順手帶走。

CLI 事實（cleanup 互動 TUI 陷阱、npm 無自動更新）見 [[reference-backlog-md-browser-id-mechanics]]；治理動機「有進有出」見 [[feedback_inflow-needs-outflow]]；bash 3.2 空陣列陷阱見 [[reference_bash32-set-u-empty-array-trap]]。
