# Work Order — AIR-38 EP 審查（read-only 深審，advisory）

## 1. 紅線（違反＝失敗）

- read-only：禁任何寫入（含 repo 外、memory 池、/tmp）；交付＝最終回覆文字
- 禁 git add/commit/push、禁改 backlog 卡狀態
- 中間筆記不留檔

## 2. 目標（一句話）

審查 AIR-38 EP 修正版（四家比較路由反饋七項修訂——handoff tier 欄／架構級 EP 出口／開卡屬性標註／旗艦資格條款）的設計合理性與引用 drift，產 findings。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- base commit：`7ef65c6`
- 並行改動聲明：working tree 有 AIR-37 任務家（untracked，EP review 中）——非本審查對象

## 4. 必讀（scope manifest）

- **core（逐段讀）**：`ai-analysis/_tasks/09-07-routing-feedback-tier/ep.md`（審查對象——已含 GLM 側 11 findings 修正與 Review Record）；`ai-analysis/_tasks/09-07-routing-feedback-tier/spec.md`（user 拍板＋證據錨點——EP 的輸入）
- **leaf（機械掃＋異常深讀）**：`skills/self-contained-prompt/SKILL.md`（S1 schema 落點 :42-49）；`skills/handoff/SKILL.md`（消費側＋「八欄」:54）；`skills/model-routing/SKILL.md`（S2 落點群：tier 段/gate :110/family 表 :86-96/tier 表 :16-18）；`rules/model-routing.md`（pointer 行＋「隨意」:11＋gate 枚舉 :34）；`rules/acceptance-evidence.md`（claim 群 :19-24）
- **exclusions**：ref-docs/、backlog/、.muse-bridge/、其他 ai-analysis/

## 5. 已決策（勿重辯）＋矛盾例外

- 核心裁決：路由詞彙一律「旗艦／一般」tier 抽象；模型名只在解析層；family 軸是第二軸非 tier 降級（user 拍板）
- tier 詞彙體系（full/lite/vision 英文 token）不動——「隨意→一般」只動中文標籤
- D 項無標的記錄不落地（不虛構但書）
- S3 排 AIR-37 之後（execution-plan 同檔）＋升級路徑已補——勿建議立即重排
- 矛盾例外：發現 EP 引用條文/結構與實際衝突 → 停下舉證（file:line＋逐字引用）

## 6. 範圍限定

動＝零（read-only）；不動＝全部。交付以未產生任何檔案變更自證。

## 7. 工具接線

cat/rg/ls（字串搜尋一律 rg）；禁 code-reality 寫入面；輸出禁寫 repo 外。

## 8. 驗收（查證命令＋預期證據形態）

1. `rg -n "隨意" rules/ skills/ agents/ --type md` → 現況四處命中（rule:11/skill:3/:12/:18）——EP 修正後標籤統一目標可達
2. `rg -n "八欄" skills/` → handoff:54 唯一產品面命中（EP 宣稱核對）
3. `rg -n "eligibility gate" skills/model-routing/SKILL.md` → gate 段結構（EP 增第六條落點）
4. `rg -n "43-57" rules/ skills/ agents/` → 產品面零命中（D 無標的宣稱核對）

## 9. 證據紀律＋PII 禁令

每 finding 附 file:line＋逐字引用；禁 PII；審查方法論限制段。

## 10. 交付報告（findings schema）

每 finding：file:line 錨點、嚴重度（H/M/L）、信心（0-1）、remedy 三分類（bug／drift／design-reversal——需 user 拍板）、一句修法。審查維度：EP 引用 drift（錨點 vs 實際）／設計合理性（G 條款分層、坐位單一記載、兩套條件管轄邊界）／漏改（rg 掃 tier/旗艦/隨意 引用面找 EP 未覆蓋項）／SM 覆蓋／過度工程線。最後總評一行：可定稿／需修正後定稿。
