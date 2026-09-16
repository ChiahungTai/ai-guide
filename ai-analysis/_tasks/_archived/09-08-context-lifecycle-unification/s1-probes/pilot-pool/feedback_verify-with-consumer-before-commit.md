---
name: verify-with-consumer-before-commit
description: 消費端回報 bug：先修活路徑（雙活期勿修新家）→回報方原始輸入重現→commit→交棒吸收（user 修正順序＋落點）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_03a95bfb-afca-4b31-a259-060d932f97ce
---

2026-08-25 user 糾正：「你應該是先讓 mosaic 確認修改有效，之後 commit 再傳給 code reality」——當時我已完成 delta_tour 三 bug 修復（435 tests 綠）並直接端出 commit 提案。

**Why**：修復者的測試綠燈只證「AI 自洽地修了」（L2/L3）；消費端的原始失敗輸入（他們的 snapshots/EPs/真實 repo）才是 acceptance 層證據——特別是 bug 根因有多候選時（如 delta_tour Bug 1：profile 未載入 vs 相對路徑 miss），只有回報方的實際材料能分辨。跳過這步＝commit 了「測試綠但沒對到病」的修復。

**How to apply**：跨 session/repo 的 bug 報告修復流程＝①修（TDD）②**修復者先用回報方原始失敗輸入重現**（機械驗收條款逐項；根因多候選時用實際材料分辨——這只是 pre-verification）③commit ④**交付完整重產 handoff prompt 給回報方**——命令全形（活消費路徑、輸出落他們真實位置覆寫舊檔）＋走讀確認點（含主觀體驗維度——機械條款過≠消費者滿意）＋已知限制框住（防誤報）＋回報格式——**消費者自行重產＋走讀回報才是 acceptance gate**，修復者代勞重現不算數 ⑤handoff/relay 給吸收方（回報作為吸收驗收輸入）。與 [[relay-claims-verify-current-state]] 互為對偶：那是「接收宣稱先驗現況」，這是「送出修復先驗消費端」。與 [[cr-live-faces-roadmap]] 的 delta_tour 弧為首例（user 三度修正：①順序「先讓 mosaic 確認再 commit」②落點「修 ai-rules 活路徑」③誰驗證「mosaic 用完整 handoff prompt 自行重產」）。

**首例全程閉環（2026-08-25 末）**：mosaic 依 handoff 自行重產兩份 tour 回報——驗收全過（⚠ 55→0×2、死步/範圍外 0 且 52 檔步 ⊆ git range 程式化驗證、新檔錨落宣告行）、總分 1.83→3.17、定位從「免責聲明」變「準確描述」；回報同時帶回敘事缺口 backlog（最大槓桿＝EP 文本語義抽取＋import graph 拓撲排序）與三小項新問題——**消費者走讀不僅是 gate，還產出下一輪規格輸入**，這是修復者代勞重現拿不到的增量。
