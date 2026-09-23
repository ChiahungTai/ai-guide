---
id: AIR-168
title: scbus 位址制契約——address+binding＋送達意圖三態（D4；sc-router 工單前置）
status: To Do
assignee: []
created_date: '2026-09-22 23:29'
updated_date: '2026-09-23 00:03'
labels:
  - orchestration
dependencies: []
ordinal: 154000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**問題**：現在 session 之間寄信，地址是一長串 session id。這種 id 識別的是「哪個視窗開著」，不是「誰負責這條工作線」。所以：換了 session 地址就失效（信寄進已關閉視窗的信箱）、地址太長複製會截斷出錯（已出事兩次）、你要一直提醒 AI 去收信。實測（0923 盤點）：98 封信 23 封沒人讀、13 封寄進死信箱、marshal 的名字甚至掛在一個早就結束的 session 上。

**這張卡要做**：
1. 地址改成「有意義的名字」（例如 ai-guide-marshal）。信寄到名字、不寄到視窗；誰在線上就把名字認領過去，session 關了信不丟，下一個接手的認領後收得到。（今天已手動試辦：名字重綁後信自動出現在現任 session，驗證通。）
2. 寄信可標急緩：急件（打斷在跑的）／普通（下次開口時給）／只是通知——現在只有一種模式。
3. 背景監看員：沒人認領的信箱有信就通知（借用現成 bridge_waiter 形態，不是常駐程式）。
4. 記錄「信什麼時候被讀掉」——現在完全不可考。
5. 順帶修：registry 一千多筆假活註冊資料；codex/claude 端只能報到不能自動收信（只有 zcode 能）——列入規格。

**分工**：本卡只寫規格＋驗收；實作歸 sc-router repo，規格用工單信送過去（寄出前問你）。

**不動**：對外發送同意規則；不做常駐 daemon。

```mermaid
flowchart LR
  A["寄信人"] -->|"寄名字不寄 id"| MB["名字信箱（持久）"]
  MB -->|"有人在線：已認領"| OK["自動送達現任 session"]
  MB -->|"沒人在線"| KEEP["信留在信箱"]
  KEEP --> W["監看員發通知"]
  KEEP --> NEXT["接手 session 認領後收到"]
```

證據與完整設計：.agent-tmp/air-135-disc/marshal-rethink-convergence-proposal.md（D4 節）＋flash-scbus-usage-result.md。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 契約文件落地：位址語義＋binding 生命週期（claim/transfer/tombstone/lease）＋三態語義＋consumed_at stage＋registry 分離——單一源落點（skills 或 governance docs），含 zcode/codex/claude/muse 四面 drain 能力矩陣
- [ ] #2 sc-router 工單信草稿完成（含 flash B 實證數據＋D4 契約全文＋drain adapter 缺口清單）——送出前 user 授權＋主權 session 位址
- [ ] #3 journal 在飛總表機械生成 helper 落地（查 bridge show/scbus list/git status 現值輸出）＋弧結算流程接線（狀態欄位禁手抄）
- [ ] #4 handoff packet 模板增『收取法形』欄位正典化（flash A 結構發現：收取法形全活、狀態快照形寫下即爛）
<!-- AC:END -->
