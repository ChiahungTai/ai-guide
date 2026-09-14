---
id: AIR-91
title: model 派工詞彙整體治理——vision／旗艦／最強檔三題軸清理（先整體討論再動手）
status: To Do
assignee: []
created_date: '2026-09-14 08:36'
labels: []
dependencies: []
ordinal: 77000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕model 派工的詞彙表有三個彆扭點：vision 其實是「能力」不是強度檔位、「旗艦」一詞在文檔裡兩個意思混用、還有比現役旗艦更強但表格沒位置的新 model（astra／fabel）。這卡先把整體做法討論清楚再動手——不預設定稿。

## baseline
main @ `14da94c`。源起＝2026-09-14 user×AI 詞彙治理討論（側聊三連：flagship 上層→vision 軸性→旗艦雙義掃描）；機械掃描證據已備（見下），勿重掃。

## 三題材料（掃描證據在案）

1. **vision 是能力軸非強度軸，卻放在 tier 枚舉裡**——doctrine 自己承認（model-routing skill L12「能力軸非強度軸，旗艦／一般都可能具備或不具備」），AIR-24 以詞彙經濟學併入；症狀：vision row 結構上是 filter（哪些 model 有影像）非強度 profile、L44 需 footnote 自衛（「非所有 lite 款都具影像能力」）、全庫唯一消費者＝vision-review。方向素材：兩軸重構（tier: full/lite＋capability flags: vision；解析序＝capability 先過濾、tier 在過濾集內選）；今天派工結果零變化（vision-review 仍落 glm-5.3-flash，user 拍板「影像都用 flash」與 tier 無關）。
2. **「旗艦」一詞雙義**——A 義＝full tier 中文 gloss（rules/model-routing.md:9、skill L12/L16/L22-32、agent-workflow L57/L233、agents/AGENTS.md:110、self-contained-prompt L50、skills/CLAUDE.md:132、sync_agents.py:44）；B 義＝家族在籍最強 model 屬性（skill L119「gpt-5.6-sol（原生旗艦）」、L120）。A 義的「最強」語感是假的（見題 3），兩義會打架；drift 命中清單已掃齊（上列即全清單）。
3. **最強檔天花板沒有詞彙位置**——gpt-6-astra（最強檔；ChatGPT 帳號路徑 server 拒、需 credits 載具）與 fabel（禁派、訂閱面）強於在籍旗艦（sol／GLM-5.3）；不開新 tier（tier＝requirement 檔非 capability 排行榜）；現有落點＝family inventory＋spine `model-runtime-entitlements` 帳號面 gate，解鎖日才進 tier 表換首選——此現狀是否足夠屬討論項。

## 已決策（勿重辯）
- **整體討論、不預設定稿、作法要再討論**（user 2026-09-14 側聊裁定）——本卡是討論載體＋治理承諾，開工前須先收斂做法
- 三題同根：model-domain 詞彙未做過一次性軸清理；討論起點原則＝「一詞一義、一軸一表」（非結論）
- 機器契約層現狀統一：`sync_agents.py` `_TIER_TOKENS = {full, vision, lite}` 硬編碼、agents/roles/*.md frontmatter 全用正式 token——本卡純散文/詞彙層治理，**派工行為零變化是驗收硬約束**
- 旗艦 gloss 漂移面與 vision 重構捆綁處理（一次討論、一份遷移），不兩頭改

## 開放問題（討論議程）
① vision 兩軸分離的具體形態：capability flag 語法（frontmatter？解析表欄位？）、解析序、vision-review 重釘哪個 tier＋vision flag
② 旗艦去雙義方向：保留哪一義（family 屬性義 vs tier gloss 義）、另一義換什麼詞
③ 最強檔的詞彙位置：family inventory＋spine gate 現狀是否足夠，還是要顯式詞彙（如「最強檔」入表註記）
④ 遷移形態：獨立弧一次清理 vs 隨觸及漸進（AIR-89 剛動過 model-routing——時點考量）

## 漣漪清單（實作時 rg drift 全掃，命中清單現成）
rules/model-routing.md、skills/model-routing/SKILL.md、skills/agent-workflow/SKILL.md、skills/self-contained-prompt/SKILL.md、skills/CLAUDE.md、agents/AGENTS.md、scripts/sync_agents.py（含 pin dict 生成物 registry）、agents/roles/vision-review.md（若重釘）
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 討論材料齊：三題現況＋選項方向＋漣漪清單落卡（本卡 desc 即初版，討論中增補）
- [ ] #2 作法經整體討論收斂：軸模型與遷移形態 user 拍板，落卡 notes（勿重辯段更新）
- [ ] #3 落地後 rg drift 掃描零殘留＋派工行為零變化驗證（機器 token 與實際 model 解析結果不變）
<!-- AC:END -->
