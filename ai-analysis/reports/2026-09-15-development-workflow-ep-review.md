# 開發流程重設計 EP 審查報告（獨立審查＋主 session 合成）

> 檔案：`ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md`（@`01eca3d`，EP sha `5b8f93…`）
> 模式：`[EP Review Mode] effort=standard, workflow=false, agent=true`（單一獨立審查 agent 跑 F1–F5，主 session 合成裁決）
> 先前輪次：F1–F6／M1–M4 抽驗仍 resolved，不重開（抽驗錨：F1→SM-16/EP:218、F2→EP:191/SM-19、F3→EP:336、F4→EP:192/SM-13、F5→EP:303、F6→EP:273、M1-B1→EP:243、M2-B1→EP:247、M4-B1→EP:223）
> 回寫狀態：⏸️ **PENDING**——user 指示先不改；本報告 findings 尚未入 EP，EP 與 hash 鏈未動

## Findings（N1–N8 獨立審查 ＋ S1 主 session 補充）

### N1｜🟡 建議（F4/F3）｜「AIR-96 dirty」陳述已過時＋缺 AIR-96 #3 協調｜主 session：✅採納

- EP 段落：`:42`、`:334`、`:344`、`:358`、UC 盤點 `:105`
- 問題：`f68e77b`（17:10）＋`b9eaab6` 落地於末輪審查（closure 16:57）之後，`git status` 已 clean——「dirty」無指涉物。更實質：AIR-96 卡仍 In Progress，殘項 #3 muse bundle 瘦身（33,013B＝36KiB gate 89% WARN，目標 ≤80%）與本 EP S3（改 `rules/context-management.md`）＋S4（導航同步）同改同一個 bundle——EP 只有 AIR-60 對帳條款，無 #3 順序／base 確認。
- 證據：`git log --oneline 0bbddb1..HEAD`（5 顆）；`git status --short` 空；卡片 `backlog/tasks/air-96…md:4 status: In Progress`、`:19` #3 條文、`:26` AC 未勾。主 session 複驗命中。
- 建議修法：① 全文「dirty」→「持有中（#1/#2/#5 已 commit `f68e77b`/`b9eaab6`，#3/#4 未落地）」；② 開工 prerequisite 加「確認 AIR-96 #3 範圍／順序——若 #3 已重構 `context-management.md` 則 S3 以新版為 base；S3 改動後跑 size gate 不得把 #3 推過 80%（超限先找 owner 協調，不靜默擠壓）」。
- 驗證式：`git status --short | wc -l`＝0；`rg -n "dirty" ep.md` 全改為持有中表述；`rg -n "AIR-96 #3|bundle 瘦身" ep.md` 非空。

### N2｜🟡 建議（F1）｜S3 manifest 列 `autonomous-execution` 但無修改要點｜✅採納

- EP 段落：S3 Context `:267`＋manifest `:329` vs 修改要點 `:271–279`
- 問題：ownership 表（:86）列其為消費者，manifest 列入寫入集合，但九條修改要點無一指名（`rg -n "autonomous" ep.md` 僅 :86/:267/:329，主 session 複驗）。且其 crash-only reconciliation（真相源＝git＋EP 段落定義、不依賴顯式 done 標記、非動態進度檔，`skills/autonomous-execution/SKILL.md:96–120` 主 session 複驗原文）與 S3「讀 EP 進度節 checkpoint＋已驗/未驗證據」需顯式調和，否則 implementer 自行調和＝唯一真相源破口。
- 建議修法：S3 補一條：「Session Recovery 改為引用 `task-recovery.md` 恢復順序；intent 來源維持 EP 段落定義，另加讀 S2 EP:219 段落結果欄位作已驗/未驗輸入；deep-work 無 EP 弧沿用 journal，不新造進度檔。」
- 驗證式：`rg -n "autonomous-execution" ep.md` 在 :269–279 有指令句（含「改為引用／加讀」）。

### N3｜🟡 建議（F1）｜S4 manifest 列 `deep-work`/`debrief`/`illustrate`（＋S3 `state-md-write`）但無對應指令｜✅採納

- EP 段落：S4 manifest `:330`、修改要點 `:299–304`、EP:300；S3 manifest `:329`
- 問題：① `illustrate/SKILL.md` 無強制產圖 mandate（opt-in；強制源是 `illustrate-html-mode:76`，S4 已排入），`debrief/SKILL.md` 頭段與新設計已一致——兩者無需改卻列「寫入集合」（主 session 複驗 debrief 頭段、illustrate opt-in、deep-work :88–89/:155/:157–163 皆命中）。② `deep-work` 至少需一條處置，現為零。③ `state-md-write:13` 已與 S3 一致，應為 verify-only。
- 建議修法：manifest 拆「寫入集合」vs「verify-only」；debrief/illustrate/state-md-write 歸後者；deep-work 補處置（pipeline/judge 流引用 S1/S2 新語義；:155 pointer 免改；:157–163 judge 傳入改 S1 profile findings＋coverage；S4 pilot 決定 autonomous 路徑，見 N8）。`commit/SKILL.md`「只對帳引用」同歸 verify-only 節。
- 驗證式：manifest 每列名在對應段有指令句，或歸入顯式 verify-only 清單。

### N4｜🟡 建議（F3）｜EP:204「由 S2 接完」與 S4 擁有 `CLAUDE.md`/`deep-work` 矛盾｜✅採納（證據修正一處）

- EP 段落：S1 驗證 `:204` vs manifest `:328/:330`
- 問題：:204 寫 sweep 四 pattern 命中「由 S2 接完」，但 `max-agents` 命中含 S4 擁有的 `skills/CLAUDE.md`＋`skills/deep-work/SKILL.md`（主 session 重跑確認）；S2 不可能接完 S4 的檔，且真改即與 N3 雙 writer。
- 證據修正：原報告稱 `3-perspective` 亦含兩者——主 session 複驗 `3-perspective` **不含** `skills/CLAUDE.md`（僅 deep-work 等 10 檔）。矛盾本體不受影響（max-agents 11 檔命中兩者無誤）。
- 建議修法：:204 改「按 manifest 分段承接（S2 接主鏈檔，S4 接 `skills/CLAUDE.md`/`deep-work`；pointer-only 命中記免改），不得有無主 consumer；S2 結段前出 disposition 清單，S4 開工核對。」
- 驗證式：`rg -n "由 S2 接完" ep.md` 零命中；sweep 命中 ∩ manifest 並集全覆蓋（exceptions 具名）。

### N5｜ℹ️ 提醒（F3）｜review JSON 內 `model-routing` 行錨漂移 +10（EP 本文不受影響）｜✅採納

- `f68e77b` 在 `skills/model-routing/SKILL.md:71` 後插入 inherit 節（numstat 11＋/1－，淨 +10，主 session 複驗）；review JSON 引用的 `:116/:172/:232` 等已漂移。EP 本文 20 處行錨逐一實測全準，且錨定檔在 baseline..HEAD 零變更（主 session 複驗 `git diff --name-only 0bbddb1..HEAD`：僅 hook／任務家／reports／sync_agents／model-routing×2／tests，無錨定 skill 檔）。EP 免修（:183 重定位條款已覆蓋）；回查 JSON 行號時 +10 或直接 rg。

### N6｜ℹ️ 提醒（F3）｜EP:56「S3 並行設計」vs EP:265「依賴 S2」易誤讀｜✅採納

- design/implement 分層嚴格一致，但「並行」易被讀成可先於 S2 實作；S3 checkpoint 欄位消費 S2 的 EP:219 格式，先做＝返工。修法：:56 句尾加「（設計可並行；**S3 實作待 S2 EP:219 欄位定稿**）」。

### N7｜ℹ️ 提醒（F1）｜EP:222 `judge-review` 處置薄｜✅採納

- 「同步 identity 讀取指針」主語可讀成僅 followup；judge 是否需讀新增 `scope`/`review_profile`/`coverage`（:193）未明。修法：「**judge/followup 均同步 identity 讀取指針**（judge 裁決前核對 `coverage` 未驗項，見 SM-12）。」

### N8｜ℹ️ 提醒（F5）｜pilot（:317）未含 deep-work autonomous 路徑｜✅採納（條件式）

- pilot 只列一般變更＋控制面變更；若 N3 判定 deep-work 需改，其 judge 流即無 pilot 覆蓋。修法：:317 加「若 deep-work 有改，pilot 加一 autonomous 小弧或顯式記未 pilot 維持舊語義。」

### S1｜ℹ️ 提醒（F4，主 session 補充）｜compact 機制改善選項無處置交代｜主 session 提出

- EP 的 compact 設計止於 S3 checkpoint-first＋恢復驗證（UC-C 接續半徑，見 SM-08/09/10/11/15/18；:42/:279 明確排除自動 compact、hook 假設、token threshold、SessionEnd 依賴）。
- 但背景報告的機制改善選項——codex §10（window 代際鏈、摘要本體存檔、pre/post 標定、換模型紀律）與 memory §8（verification 輕量版、semantic boundary 指引、ZCode tail 補償、transcript 錨、memory 半自動化）——在 EP 內**既未採納、也未逐項寫不做理由**。範圍裁決本身合理（docs-mode 最小閉合），但缺處置交代＝後人無法判斷是「已評估放棄」還是「遺漏」。
- 建議：在 S3 Context 或範圍節加一段 disposition 表（選項／採納或不做／一句理由），或在 :279 不做清單後附「其餘背景選項未入本 EP，留待 compact 專弧」。

## F1–F5 Verdicts（主 session 同意獨立審查）

- F1 完整性 — conditional（N2／N3 列名無指令；N7 輕症）
- F2 合規 — pass（docs-mode 校準完整；`__all__`/demo/pytest/mypy N/A 明說；部署鏈與 consent gate 在場）
- F3 一致性＋架構 — conditional（N4 內部矛盾、N1 措辭過時；基線漂移＝0）
- F4 遺漏 — conditional（唯一遺漏：N1 的 AIR-96 #3 協調；後於歷輪審查成立，genuinely new）
- F5 場景覆蓋 — pass（SM-01–24 連續；UC 全 ≥3 覆蓋；H1–H5 有對應）

## 方向判斷（主 session 同意，摘要）

值得做（控制面減負＋每項減量附防線與改判條件）；已足簡（拒新 engine/router/hook/registry/狀態庫）；最大風險 H1/H5/H2（省成本機制反噬正確性，驗收看行為實驗與 :316 守門）；不可逆點是錯誤結案污染信任鏈（SM-16/23＋:317 Built-only 緩解；deploy 須 user 明示授權已寫死）。

## 待回寫清單（解凍後執行，本次未動）

N1（措辭＋#3 協調條款）／N2（autonomous 處置 bullet）／N3（manifest 拆寫入 vs verify-only＋deep-work 處置）／N4（:204 分段承接改寫）／N6／N7／N8（一行修法）／S1（compact 選項 disposition 段）。回寫後跑各條機械驗證式做 lite followup，無需重新全文審查。回寫將改動 EP→須同步重算 projection hash（HTML＋planning-validation 換版記行，沿 `01eca3d` 模式）。

## 審查結論

**有條件執行（conditional）**：無 🔴；N1–N4 回寫後即可交 implement。開工前另守 EP 自帶三門：user implement 指令、AIR-60 owner 對帳、HEAD/dirty＋治理檔核對。
