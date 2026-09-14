# Work Order — Foreign-runtime 委派工單模板（_common）

> 共享子範本——foreign runtime（delegate-bridge `task --family muse|codex|glm`）共用；skill 間引用＋主 session 直接填寫。prompt 為任務本文，禁含委派語言（muse-in-muse EPERM 教訓）。本檔定義十節硬欄位，缺一不可；消費端填寫時逐節落實，空缺＝未就緒。

> **契約值指路不 inline**：工單涉及既有契約（卡 ref 形態、命令語義、流程步驟、規則集條款）時寫「見 `skills/<skill>/SKILL.md` 對應段」並標「以合約為準」，不複製完整值——工單是快照，內嵌值與單一源脫鉤，源更新後工單仍帶舊值，被委派方不載自家 skill 無從發現漂移（真實案例：muse 工單內嵌當時形態的 URL，中央 viewer 改版後結案卡 ref 照抄舊值；spawn prompt 內聯規則集濃縮版當場漏條款）。**pointer 必須接手方可達**：跨 repo/外部 runtime 委派用絕對路徑（同機可達形態＝`~/.agents/skills/<skill>/SKILL.md`）；不可達時嵌最小必要契約值＋標「以源 repo 為準，值僅快照」。執行中發現工單值與源漂移 → 中途注入「以 skill 段為權威＋漏項」校正，不必等收屍。

## 1. 紅線（首段，違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯（「止步 commit 前」不夠，AIR-18 自行 staged 多檔教訓）
- read-only 任務禁任何寫入（advisory profile 尤甚）
- 禁把產物寫到 `/tmp` 或 repo 外；中間筆記不留檔
- 紅線違反＝失敗，非風格問題；審查未過不得結卡
- 外部 runtime flag 未暴露時，以本紅線承載 read-only 約束（bridge 暴露 `--disable-write` 後改 flag；roadmap 記 delegate-bridge 側）

## 2. 目標（一句話）

> 一句話說明本次委派要達成的背景與目標（讓 reviewer 一句看懂為何派）。

- 例句型：「把 X 制度化為 Y，達成 Z」（填寫時替換為本次任務的具體目標）

### Role contract（派發 registry role 時必填子段）

> 派發對象是 ai-guide registry role 時（muse/codex/grok 皆同），role 紀律核心**引用不重寫**——單一源在 `agents/roles/<name>.md`：

- **role name**＋**requirement**（tier token：full/vision/lite——分配表見 `skills/model-routing/SKILL.md` role→requirement 表）
- **role body 交接**：貼入 `agents/roles/<name>.md` 全文（附 body hash）或給絕對路徑令 runtime 自讀；與 §4 必讀的分工——§4 列 repo 材料路徑，本段承載 role 選擇依據
- **model/effort**：按 requirement 查 `skills/model-routing/SKILL.md` tier×provider 權威表（本 harness 綁定哪家 provider 見 `agents/AGENTS.md` harness 軸表）；vision 不得降非影像款、lite 禁 luna
- 非 role 派發（ad-hoc 任務）本子段留空

## 3. Baseline identity

- repo root：絕對路徑（如 `/Users/ctai/Github/ai-guide`）＋是主 working tree 還是 worktree
- 工作目錄：本次任務的 cwd（若與 repo root 不同需明示）
- base commit：凍結基線 commit hash
- 並行改動聲明：working tree 已有但不屬清理範圍的改動（如 backlog 卡、任務家產物），列出路徑與性質，避免誤判為本次改動

## 4. 必讀（按序，絕對路徑）

> 按序列出，確保可執行讀取（`cat`／`Read` 可達）；路徑一律絕對路徑。

1. `.../ep.md`——指定段落（核心原則、S1/S2/S3 等）
2. `.../rules/<rule>.md`——對應段落
3. `.../skills/<skill>/SKILL.md`——解析表結構
4. `.../agents/AGENTS.md`——治理段現況
5. `.../skills/_common/<template>.md`——層慣例（僅檔頭，無需全文）

> review 工單（external second-opinion）必讀含審查方法論 bundle：`review-engine` + 消費命令 profile（如 code-review 場景的 `code-review-and-quality`、結構軸 `arch-thinking`）——findings 沿用 bundle 既有詞彙（不定義新詞，詞彙單一源在對應 skill），供 in-harness judge 對譯裁決。

## 5. 已決策（勿重辯）＋矛盾例外

- 逐條列出已定案事項（落點、thin forwarder 維持、兩層契約、模板節名、family 角色拆名等），標「勿重辯」
- **矛盾例外**：若發現現有檔案內容、程式碼、官方文檔或驗收輸出與已決策具體衝突（同段已有矛盾的既定義），**停下來在報告中舉證**，不要自行改設計或為服從工單靜默做錯
- 舉證需附 file:line 與逐字引用

## 6. 範圍限定

- 動：檔案級列舉（如 `rules/model-routing.md`、`skills/model-routing/SKILL.md`、`agents/AGENTS.md`、`skills/_common/work-order.md`）
- 不動：其他一切（尤其 `agents/zcode/*.md`／`agents/claude/*.md` **生成檔**——勿手改，sync 會覆蓋；`rules/tool-discipline.md`、`skills/CLAUDE.md` 以外的索引檔等）
- 違反範圍＝失敗；不動檔需在交付報告中舉證 `git diff --name-only` 未改

## 7. 工具接線

- 讀查：`bash`（`cat`／`rg`／`ls`）、`Read`；字串搜尋一律 `rg`
- external runtime 接線（available-face 階梯，以 runtime 實際能力為準——禁從 role/template 宣告推定 runtime 實際具有 MCP）：① runtime/role 實際暴露 CR MCP query tools → 優先 MCP；② 否則 runtime 可執行 code-reality CLI → 唯讀 query face；③ 兩者皆不可用 → `rg` degraded，交付報告標 `[WARN] structural context degraded`
- fallback 可見化：CR query transient failure → 同 face 重試一次；capability 缺場／binary missing／auth 明確拒絕 → 記 reason 往下降階（禁盲重試、禁靜默漂移到純文字查證）；external runtime spawn auth failure 屬 dispatch 層處置，不與 CR query fallback 混同
- 最小可用：不引入非必要工具
- 三禁令：
  - 禁 code-reality 寫入面（`build`／`snapshot`／`delta_tour`／`project`）；查詢面可用可不用
  - 禁把任何工具輸出寫到 repo 外（含 `/tmp`）
  - 禁自行妥協路徑（遇缺口停下舉證，不繞路）

## 8. 驗收（命令＋預期結果，逐條實跑）（例——填單時替換為本工單實際命令）

> 每條＝可貼上執行的命令＋預期結果，機械可判；逐條實跑並採集原始輸出。

1. `rg -n "external-runtime" rules/model-routing.md` → ≥1 命中
2. `rg -n "eligibility" rules/model-routing.md` → 命中
3. `rg -n "needs-fix" skills/model-routing/SKILL.md` → 命中
4. `rg -n "flag profile|thin forwarder" agents/AGENTS.md` → 兩詞皆命中
5. `test -f skills/_common/work-order.md && rg -n "紅線|Baseline|矛盾例外|PII|交付報告格式" skills/_common/work-order.md` → 檔在且五關鍵詞皆命中
6. `head -3 skills/_common/work-order.md | rg -c "^---"` → 0
7. `rg -n "<model-id-前綴>" rules/model-routing.md agents/AGENTS.md skills/_common/work-order.md` → 零命中（skill 檔除外；實際掃三家族模型前綴小寫，此處為避模板自身命中而改寫示意）
8. `rg -n "external-runtime" skills/model-routing/SKILL.md` → ≥2 命中
9. `rg -n "model-routing" rules/AGENTS.md` → 讀現況並報告（本次不改）

- 每條附完整命令與原始輸出（截斷標明）；不可只貼結論

## 9. 證據紀律＋PII 禁令

- 每條驗收附完整命令與原始輸出（截斷標明）；宣稱「沒改 X」須附 `git diff --name-only` 佐證
- 報告中禁出現任何 email／人名等 PII（`user_email`／`user_full_name` 禁入輸出）
- 宣稱需有獨立證據（非重跑自身假設）；失敗需如實記錄，不掩蓋

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 `git diff`）
2. 逐段落落實說明：EP S1 三塊／S2 兩點／S3 十節各落在哪（file:line 級對照）
3. 驗收 1-9 命令與輸出（原始）
4. 偏差記錄：與 EP 規格有任何出入處＋原因
5. 未驗證項／被阻擋項
6. 建議 reviewer 聚焦點（最有信心不足之處）

> 附加：jobId／thread id、改檔清單、實跑命令與輸出、未驗證項、建議 reviewer 聚焦點（completion-check 話術承載節）；無對應項標「無」勿留空。

## Review／advisory variant（唯讀深審工單的欄位替換語義）

> 十節結構不變；review/advisory 形態（read-only、無 EP、無 writer、無預期改檔——external second-opinion、[/state-review](../state-review/SKILL.md) 深審腿）以下欄位**替換**而非豁免，缺替換欄位一樣＝未就緒。implementation 形態缺 §4 EP／§10 落實說明仍為未就緒（兩形態互不冒充）。

- **§3 Baseline identity** 增：環境凍結證據——clean tree 聲明，或 dirty 模式的 tracked diff hash＋untracked 清單/content hash（審查端前後比對，不一致標 stale）
- **§4 必讀**：EP 段落項替換為 **scope manifest**——審查範圍逐 path 分類（core 逐檔讀／leaf 機械掃＋異常深讀／generated 驗投影不當源／mirror 驗 manifest 帳），每 path 恰屬一 bucket、exclusions 明列；方法論 bundle 照舊（§4 既有 review 注記）
- **§6 範圍限定**：動＝零（read-only）；不動＝全部（含 backlog 卡狀態）——交付以 `git diff --name-only` 空 + `git status` 前後一致舉證
- **§8 驗收**：逐條「查證命令＋預期證據形態」（錨點存在性、hash 對帳、coverage 分類帳完備性）；**驗證 baseline 用正式檔的副本**（collector 每次比較推進 baseline——唯讀驗收直接跑正式 baseline-dir 會消耗下一輪比較起點，codex 09-08 實證）
- **§10 交付報告**：逐段落落實說明替換為 **findings schema**——每 finding 附 file:line 錨點、嚴重度（review-engine 三級）、信心水準、**remedy 三分類**（bug＝行為違反意圖且無文檔宣稱刻意／drift＝兩處宣稱或實作不一致／design-reversal＝文檔化的刻意設計但設計本身該反轉——反轉需 user 拍板）、Important 以上附**可機械化驗收設計**（failure-injection 形態最佳）；**每條 finding 附驗證式**（可機械複驗的 rg 命令／pytest case——external reviewer 工單標準要求；與 review-engine／workflow-review-pattern 同詞，定義單一源在彼處；followup 驗收逐條重跑；工單標準嚴於鏈內——鏈內 Important+ 附，工單每條附）；另附環境前提自曝（worktree identity／HEAD／工具新鮮度）與方法論限制段（用了什麼、什麼無法驗證）

---

> 消費形態：skill 間以 `../_common/work-order.md` link 引用，或主 session 直接依本模板填寫新工單本文後經 bridge `task`（`--family muse|codex|glm`）派發。長跑工單派發後回報 jobId（供 `wait`／`show` 晚收與跨 session 認領），收法單一源見 model-routing skill「完成回報收法」決策樹。`rules/model-routing.md` tier 詞彙句與 `skills/model-routing/SKILL.md` 解析表為 family／profile 詞彙與映射單一源，本模板不自帶定義。
