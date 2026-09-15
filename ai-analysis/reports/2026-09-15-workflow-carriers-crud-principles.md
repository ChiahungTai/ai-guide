# Marshal 工作流的載體分工與 CRUD 判準

> 用途：人類與 LLM 重新檢查 memory／skills／rules／Cards 是否放對位置的設計報告。不是新的 instruction 定義源，未授權批次搬移或清除資料，亦未做獨立審查。
> 分類單一源：`skills/memory-audit/SKILL.md:137`；Card 欄位：`skills/kanban-board/SKILL.md:43,109`；部署：`rules/AGENTS.md`。採納後應更新對應源，不把本報告變成第五套規則。

## 一句話分工

**Rules 約束這次不能犯什麼錯；Skills 告訴 LLM 這類工作怎麼做；Cards 記錄這件工作承諾做什麼、做到哪；Memory 提供跨任務仍有用的個人／專案背景事實。**

EP 是任務的詳細執行計畫，report 是證據／分析載體，git/code 是可推導實物；不應為了硬塞四分法把它們放進 memory 或 rules。

兩個軸分開判：內容屬於誰（scope/ownership），何時載入（residency）。project-specific 事實不能因常用就升全域 rule；全域必要規範不能只藏在某 project memory。某 harness 會自動載入某檔，也不代表該檔內容本來就該常駐。

## CRUD 矩陣

| 載體 | Create：何時新增 | Read：何時讀 | Update：何時／誰改 | Delete／退役：何時處理 |
|---|---|---|---|---|
| Memory | 已確認、跨任務有用、與 user／專案綁定，且不能廉價從目前 repo／卡推導的事實、偏好、事故教訓。先查同主題再決定新建 | 按任務／決策缺口檢索索引，再讀命中 body；依賴易變事實前核對現況。不是每步重讀整池 | 有新證據、偏好更新、原事實失效時，由該池授權 owner 更新原主題；記錄適用條件及證據，矛盾不默默拼接。生成索引不手改 | 錯誤、重複、已被權威來源完整取代、只剩任務歷程時，先確認引用／保留必要事故證據再移除或合併；低讀取次數本身不構成刪除理由 |
| Skills | 有可辨識任務觸發、需要重用的方法、輸入／輸出與驗收；已存在相近 skill 優先擴充。單次工單不建 skill | 執行該類任務前讀入口；細節按觸發展開。同 context 已讀且未變可引用，新 worker 不假設繼承 | 方法、工具入口、輸出契約、失敗處理變更時改 owning skill；共用方法只改單一源，消費者留指針並同步。控制面變更做行為驗證 | 無消費者且功能退役，或被另一來源完整吸收後才移除；先查 trigger、顯式引用、wrapper／部署接線。不能只因全文搜尋零命中判不存在消費 |
| Rules → bundled AGENTS.md | 必須在首個有後果行動前在場的最小約束／bootstrap，且有 user 裁定、已驗證校準或可靠觸發需要。一般教材與完整流程不進 rule | 由各 harness 實際載入；不能把「檔案存在」當「模型已讀」。詳細方法按 pointer 載 skill | 改 rules/guide authoring source；instruction-writing＋consumer 對帳＋必要行為實驗；授權部署後重建 bundle、逐端驗內容與新鮮度。禁止直接改 generated bundle | 條件已不存在、重複保護已可靠承接，或可安全下沉 skill 才退出常駐。先通過 bootstrap／首動／跨來源重複三測試；同步部署及 fresh context 驗證 |
| Cards | 已承諾且有明確 scope、owner、結果的任務；建前查重。未承諾想法放 draft/report，別膨脹 To Do | 接手／開工／變更承諾／結案前讀該卡必要全層；一般 worker 只讀相關卡及 EP 段，不掃整個 backlog | 主責編排者依卡流程更新。scope／已定決策→Plan；驗收→AC；進度與接續→Notes；人話狀態→desc；結案→Final Summary。worker 回證據，不自行改別卡 | Done 是狀態，不是刪除；結案需 AC/證據/refs 一致。重複、撤回承諾依 board 流程合併／歸檔，留下可追溯歸屬；不重用 id、不隨意刪歷史 |

CRUD 的「可以改」是內容歸屬判準，不是操作授權。尤其本環境 Codex 對專案共享 memory 池唯讀；本報告不授權寫池、改索引、commit、deploy 或刪共享資料。

## Card 內部再分工，避免一張卡四套 spec

| 欄位／相鄰載體 | 權威內容 | 不放什麼 |
|---|---|---|
| title／desc | 給人看：問題、目的、目前狀態／等什麼 | 模型路由表、長工單、log |
| Plan | scope、baseline、已決策與理由、任務邊界 | 持續追加的對話流水 |
| AC | 可驗收的外部行為／不變量 | 只寫「改完某檔」當完整功能驗收 |
| Notes | 進度、阻擋、job／evidence 指針、下一步 | 把唯一規格埋在大量追加紀錄 |
| EP | 跨檔實作步驟、自足段落、依賴、驗證 | 重抄全部 rules／skills／memory |
| Final Summary／refs | 真正交付、未交付、證據與最後位置 | 把 planned/Built/Verified 混成 Done |

Card 是承諾與任務摘要的 owner；EP 擁有詳細步驟。scope/AC 改變時同步兩者，日常進度優先更新詳細 owner 並在卡留指針，不每輪複製整份 EP。

## 如何判定目前是否誤置

針對「可獨立成立的一段內容」判定，不以整個檔案一刀切。逐項問：

1. **這是事實、方法、強制約束，還是一次任務狀態？** 混合就拆段，不能每段都貼所有載體。
2. **適用 user-level、project、module 還是本次 task？** 先定 scope；讀取頻繁不能改變 scope。
3. **哪個目前來源能證明它？** repo 可推導就回 repo；猜測與未定歸因留 report/checkpoint。
4. **等到任務觸發才讀會不會太晚？** 是→最小 rule；否→skill／檢索型資料。測模型不知道 body 時能否可靠選對 trigger。
5. **是否已有 owner？** 有→更新／引用，不再建另一套正文；索引、bundle、Card 摘要是 projection，不是新 owner。
6. **它的輸出給谁用？** 機器契約、人的 brief、raw evidence 分開存，只建立必要連結。
7. **更新或刪除會讓哪些 consumer 失效？** 查顯式／隱式 trigger、模板、生成與部署路徑、未結卡；缺證據就列待查，不猜安全。
8. **失效條件是什麼？** 任務結束、工具升級、偏好改判、policy 翻轉各有不同更新入口；沒有失效日期也須知道失效事件。

裁定標籤只需：保留／拆分／合併／下沉按需／上提最小 bootstrap／回任務載體／引用現有源／退役候選／待查。**標籤不是自動 apply 許可。**

## 常見誤置與正確形態

| 內容 | 正確 owner／處置 |
|---|---|
| 「AIR-X 尚待 Muse 回覆，job=…」 | Card Notes／EP checkpoint；不進 memory |
| 「某次延遲原來是 provider 問題」尚無證據 | report 待驗假設；不升 memory fact |
| 「user 決定 compact 時機」 | 個人偏好證據可留 memory；跨專案執行核心依 rule 資格放單一規範源，memory 不抄整套流程 |
| 「如何在 compact 後恢復 job／findings」 | 既有 skill/common procedure；rule 只留必要觸發 |
| 「現在 model A quota 5%」 | 當次 AvailabilitySnapshot／DispatchTrace；不進 catalog 或常駐 rule，memory 舊值不能當即時供給 |
| 「特定家族的 token／binding」 | 既有 catalog；skill 指向解析機制，四載體不要各抄一張表 |
| 「這個專案某 API 升級的陷阱」 | 當前 code/docs 能完整說明則引用；跨任務仍有不可推導的實證教訓才進 project memory |
| 「MUST 不得使用 stale snapshot」＋長篇事故史 | 最小核心依 rule 資格常駐；方法與例外到 skill；事故證據到 report/memory（僅已確認教訓） |
| 每個小修新增 skill | 留 task 工單；出現可重用行為與可靠 trigger 才萃取 |
| 刪除 memory 的舊規範全文後仍想保留事故線索 | 方法已移回正確 source，memory 僅留已確認背景與 pointer；先查新源可達再清重複 |

## 善用 LLM 與 tokens 的執行分工

### LLM 做語義，機械工具做清單與驗證

機械側：列檔、來源 hash、重複段候選、broken refs、生成物差異、bundle 尺寸、卡狀態與引用、實際載入／工具結果。相似文字只能提候選，不能自動判語義等價或刪除。

LLM 側：scope、事實／假設、trigger 是否足夠、首個有後果行動、consumer 風險、同義不同責任、保留理由與改判條件。重要搬移需要独立 reviewer 驗是否丟防線，Arbiter 裁取捨；不是每個檔案固定開全套多模型。

Marshal 以主題群／共同 read-set 切有界盤點工單，不按每個檔案開一顆 worker。只讀機械查證可 batch；需要獨立審查的 units 仍隔離。主 session 收精簡分類表＋精確來源，只有爭議才展開全文。不要為產生省 token 報告而掃全 repo 的所有 body。

### 載入策略

- 常駐只保留必要 bootstrap／約束及可靠導航；token 花在防首動錯誤，不花在完整手冊。
- skill metadata、memory 索引也有成本；按需 body 不是零成本。不要把 bundle 瘦下的內容等量塞到常駐索引。
- 先查索引／入口，再讀必要主題全文或相關段；高風險需要的完整契約不能省。
- 同 context 已讀且未變不重讀；fresh worker 仍需取得必要契約。pointer 必須真可達，不能只寫一個路徑便宣稱資訊已傳達。
- 在同一 task 内維持一個 current-state owner；raw evidence 留原處。checkpoint 避免累積成第二份 transcript。
- read 次數少不等於沒有價值；罕見但不可逆的錯誤防線，須看觸發風險而非點擊率。

總成本應看：常駐載入×sessions，加上按需展開、路由／交接、失敗重工與維護成本。若拿不到真 tokens，只報 bytes/chars/read/dispatch 等代理量並標示限制；不同模型 tokenizer/cache 不同，不能把字數直接當可比較成本。

## 實際分類稽核的輸出模板

每個內容單元一列，先做候選清單再核定；不要另造長期 registry：

| 來源錨點 | 內容類型／scope | 目前 owner／載入面 | 建議 owner／CRUD | 理由／失效事件 | consumers／證據 | 驗證／狀態 |
|---|---|---|---|---|---|---|
| 檔案與段落 | fact/procedure/constraint/task | 真源或 projection | 保留／U／遷移／退役候選 | 第一行為前是否必需等 | 已查與未查分列 | 可達性、行為、部署；proposed/verified |

遷移順序：**確認 scope/owner → 在目標源補齊內容 → 更新 consumers/pointers → 驗語義與實際載入 → 清掉舊副本 → 再驗殘留與部署**。寫入／提交／部署權限各自遵守現行規範。有外部並行編輯先重讀，不能全檔覆蓋他人修改。

驗收至少包含：原情境仍找得到規範、wrong-task 不誤載、fresh session 首個動作不漏必要約束、Card 接手能判下一步、memory 不把推測當事實、刪舊源後引用不斷、跨 harness bundle 真正新鮮。僅「檔案更短」不算分類正確。

## 與現行來源的差異注意

本輪讀到 memory-audit 的載體表仍有「projection 機制尚未落地（AIR-85）」註記；目前 user 提供的專案指令／先前讀到 rules/AGENTS 已描述 pointer projection 部署。這是需要核對的 stale 文檔候選，**不能把表裡的歷史狀態直接當目前 runtime**。本報告採其 scope/residency 分類原則，未据此改部署。

下一輪可先挑三個主題群（compact/recovery、review/Marshal、memory治理）依此表抽樣分類，验证判準后再擴範圍；不用立刻全庫搬家。本報告與 compact 新補充一樣，若要寫成新的控制面規範，需回 owning source 做 scoped review／behavior 驗收。
