---
name: harness-model-orthogonal-axes
description: 三層勿混：provider→model→harness（muse 是 harness 非公司）；dispatch 不綁 backend id；需求三類＝旗艦/影像/隨意；五家清單見檔內
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 09-05 四波裁定（AIR-29 EP 的設計基準，取代「per-harness pins 寫死 role」做法）：

- **「harness 跟 model 是不同的角度」**：zcode／cc／grok-build／muse code 是 harness——agents 目錄要記載「**怎樣用 agents**」（各家調用機制）；特化 agent 載入什麼 model 是**另一回事**——每個任務的 agent 按任務性質選**適合的 model+effort**（dispatch-time 決策，非 registry 檔內 pin）
- **「你將 model provider 跟 harness 又搞混」**（二次勘正）：表裡出現 CC/codex/muse/grok-build 當欄頭即混淆殘留。dispatch 順序：先選 harness→再在該 harness 綁定的 provider 內依需求類選 model
- **「zai/Anthropic/OpenAI/xai/meta 是公司, provider，他們提供的 model 有不同的，這樣才對」**（三次勘正——AI 把公司層壓扁了）：**公司（provider）＝zai／Anthropic／OpenAI／xai／meta 五家**——每家提供多個 model、檔次不同（旗艦／影像／標準）。GLM 是 zai 的 model 家族非公司；**muse 是 harness 不是公司**（muse-spark 歸 meta 欄，經 muse code harness 服務）。三層結構：公司（provider）→ model（檔次）→ harness（調用面，綁定公司）
- **「codex 是 terra high+, luna不要」**（OpenAI 欄具體指定）：標準款＝**terra high+**；**luna 排除禁派發**
- **「harness 綁定 provider」語義＝本機部署配置，非原生家**（第五次同族勘誤，AI 自查發現）：本機 CC（Claude Code）跑的是 **GLM backend**（zai 帳號，L4 log 實證）非 Anthropic——CC 原生家未訂閱但 backend 可重配；tier 表的「CC × GLM｜spawn-time haiku 別名直達 flash」行就是在這配置下才成立。harness 軸表寫綁定時永遠指本機現配置
- **「在 cc 環境下，你就用 cc 的 model 來使用就好，不用太複雜」**（第六次勘正——**dispatch 不綁 backend id**，正交第四步：role 不綁 model〔AIR-29〕→ dispatch 不綁 backend）：CC 是自足 harness，模型解析（enum 別名→實體 model）屬它的 infra 層（settings.json env 映射）——dispatch 端用 **CC 自己的詞彙**（inherit 預設／lite 點名別名），落哪顆是映射層的事。AI 反例：把「本機掛 GLM」事實焊進 dispatch 文檔（「CC 直填 flash 非 haiku 別名」）＝越層依賴，且 workflow 腳本 `ANCHOR_MODEL='flash'`（GLM id）在 CC 可能無效——CC enum 才對。每 harness 詞彙表：ZCode＝registry pins／CC＝inherit·enum 別名／muse＝bridge pin
- **「haiku 跟 luna 基本上不會用，一般最低會用 sonnet terra」**（第七次裁定——**lite 地板＝sonnet/terra 級**）：CC 詞彙點名 `sonnet`（env 映射直達 flash——兩端 lite 實體自動同顆）；OpenAI 側 terra high+（luna 排除）；haiku 僅存於 agent-workflow 偵測表的事實記載（別名存在≠會派）；`ANCHOR_MODEL` 終態 'sonnet'

**model 需求三類（旗艦清單 user 逐項指定——與五家公司一一對應）**：①**一定要旗艦**——judge／EP 規劃／批判＝**zai:GLM 5.3／Anthropic:opus／OpenAI:sol high+max／xai:fabel／meta:muse-spark 1.3**（GLM 5.3 調用形態＝主 session full inherit 不釘 id）；②**一定要影像**——視覺類任務＝glm-5.3-flash（多模✓）／muse `--image`✓／**claude·chatgpt·grok 影像款＝查證待辦**（user「你再去找」）；③**其他隨意**——實作/驗證/挖掘/渲染標準款（zai:glm-5.3-flash／Anthropic:sonnet·haiku／OpenAI:terra high+／xai:待查證；meta 不入隨意桶——旗艦同體額度貴）。tier 詞彙對齊：full＝旗艦、vision＝影像、lite＝隨意

- **程序糾正「你不是應該整理這張表先嗎」**：權威映射表先整理成型落在 spec（需求層），EP/spec/殼全部引用同一張表——禁邊跑 review 邊零碎補丁散文版（AI 初犯：先 patch EP 散文、表後補）

**分類形狀教訓**：初版 EP 把 model 軸寫成「執行檔/判斷檔」兩 tier 等價表——錯形狀且**影像需求維度整個漏掉**（只藏在 pins 隱含選擇裡）；需求語義（旗艦/影像/隨意）才是主鍵，provider 映射跟隨需求。「隨意」≠隨便——flash 分工律保護面約束照舊。

**agent 定義品質序**：最重要是**目標**，其次做法與 skills 引用（現行 agent 檔紀律多、目標埋 description——重構時目標升第一節）。

**Why**：AIR-24 已裁「tier＝能力檔語義非模型綁定」（[[feedback_capability-tier-not-model-binding]]），但 registry 把 model/thoughtLevel pins 凍結進 zcode/ 檔＝把 dispatch 決策寫死成「這個 role 永遠 flash」，同時造成跨 harness 不可達（8/10 ZCode-only）。兩個病同根：dispatch 決策沉進了 role 檔。flash 能力剖面（sess_e905a8a2：強機械執行、弱批判——judge 塌陷/sycophancy）是旗艦需求的依據。

**How to apply**：agents/ 重構三層——①`roles/<name>.md` 單一源（目標＋做法＋skills；零 model/harness 字樣）②dispatch matrix 兩軸（harness 軸＝各家調用形態＋綁定公司；model 軸＝需求三類→**五公司欄**映射，單一源 model-routing skill）③zcode/claude/ 降為**生成式投影**（ZCODE_PINS 帶 `req` 需求欄——**正式 token 收斂裁定（二輪 ep-review F3-A）＝tier 詞 full/vision/lite**：flagship/any 詞彙被否決，依據＝五檔既有 tier 引用面零改動＋AIR-24 通篇 tier 措辭；中文語義〔旗艦/影像/隨意〕只作表列標籤；vision pin 禁降標準款〔降級＝視覺驗收靜默壞〕、新 role 缺鍵 fail loud）。結構診斷與 UC 盤點見 [[project_agents-registry-split-design]]；弧狀態見 [[agents-registry-split-design]]；盤點方法論見 [[feedback_uc-inventory-before-structure-proposal]]。
