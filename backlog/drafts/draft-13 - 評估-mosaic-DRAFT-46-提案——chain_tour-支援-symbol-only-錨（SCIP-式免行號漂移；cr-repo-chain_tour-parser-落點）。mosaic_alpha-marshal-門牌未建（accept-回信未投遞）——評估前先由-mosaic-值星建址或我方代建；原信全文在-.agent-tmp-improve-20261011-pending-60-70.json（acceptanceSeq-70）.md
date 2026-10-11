---
id: DRAFT-13
title: >-
  評估 mosaic DRAFT-46 提案——chain_tour 支援 symbol-only 錨（SCIP 式免行號漂移；cr repo
  chain_tour parser 落點）。mosaic_alpha-marshal 門牌未建（accept 回信未投遞）——評估前先由 mosaic
  值星建址或我方代建；原信全文在 .agent-tmp/improve-20261011/pending-60-70.json（acceptanceSeq
  70）
status: Draft
assignee: []
created_date: '2026-10-11 12:21'
labels: []
dependencies: []
---

## Notes

- 2026-10-11 接手 session 對帳：原信（envelope 7688e6a4…、acceptanceSeq 70）已由前值星 drain（primaryCursor 70）；mosaic 側 completion 段 3（consumed/accepted）仍在等我方 `completed` 回信閉環。PENDING：向 mosaic_alpha-marshal 回 completed（result_pointer＝本卡＋原信檔；評估本體留池待排程）——outward send 待 user AUTH。門牌在場性未驗（前值星記「mosaic_alpha-marshal 門牌未建」）；回信前先 `dutymail address` 面確認。
- 2026-10-11 CR inform（seq 72、`cr-draft46-notice-aiguide-1011-001`）：**提案改由 CR 本體直接承做**（卡 CR-7、設計已過 codex 對抗審查收斂）——mosaic 原設想「經 ai-guide session 固化」路徑已修訂，**本卡評估不再需要**。ai-guide 側唯一尾巴：CR 出貨（landing notice 為準）後同步 `skills/code-reality` 接線文檔 chain_tour 錨格式一行（現行若僅載 path:line 形需補 line-omitted 變體）——本卡轉為該尾巴記憶錄。mosaic completed 回信內容改指 CR-7（實際歸屬）＋本卡（文檔尾巴）。
- 2026-10-11 **completed 回信已發**（user AUTH「發」）：`air-draft46-completed-1011-001`（reply/completed、in_reply_to 原信 message_id 87772d96…；對方址 `mosaic_alpha-marshal` **acceptanceSeq 1＝門牌首封——門牌已建成**，原信 body 自述 reply_address 為準）。mosaic 側 completion 四段收尾＝等他們 drain 本信。
- 2026-10-11 **landing notice 到（seq 73、`cr-draft46-landing-aiguide-1011-001`）**：CR 0.12.0 已出貨（PyPI live）——symbol path # 註解行號可省略、graph.db 唯一同檔命中代填、miss/歧義 noanchor 帶原因跳過、顯式 path:line 零變更。**尾巴執行時查證發現**：CR 指稱的慣例單一源 `ai-analysis/blueprint/callstack-v1/` 在本 repo **不存在**（blueprint 規範現行目錄＝`callstack/`、亦未生成）。**user 裁定（10-12）：blueprint 歸 mosaic**——callstack 錨格式慣例檔是 mosaic 側資產，CR 的指向應路由 mosaic 非 ai-guide；我側無義務。剩餘動作＝是否回信 CR 更正指向（outward 待授權）。本卡實質閉環。




