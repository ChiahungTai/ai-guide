# 主 session EP 獨立審查 findings（staged，待外部審查＋裁定）

> 來源：獨立 subagent read-only 審查（F1–F5）＋主 session 合成裁決；完整報告見 `../../reports/2026-09-15-development-workflow-ep-review.md`
> 審查對象：`../ep.md` @`01eca3d`（EP sha `5b8f93…`；現版經 codex compact 指針後為 `c497…`，語義錨未變）
> 狀態：**pending-external-review**——user 明示先經其他 LLM 審查＋裁定才回寫 EP；本檔即裁定輸入，逐條可採納／拒絕／改寫
> 先前輪次：F1–F6／M1–M4 抽驗仍 resolved，不重開

## N1｜🟡（F4/F3）｜「AIR-96 dirty」過時＋缺 #3 協調

- EP 段落：`:42`、`:334`、`:344`、`:358`、UC `:105`
- 問題：`f68e77b`（17:10）＋`b9eaab6` 落地於末輪審查（16:57）之後，`git status` 已 clean，「dirty」無指涉物；AIR-96 卡仍 In Progress，#3 bundle 瘦身（36KiB gate 89%→目標 ≤80%）與 S3/S4 同改同一個 bundle，無順序／base 協調條款（EP 僅有 AIR-60 對帳）。
- 證據：`git log --oneline 0bbddb1..HEAD`；`backlog/tasks/air-96…md:4`（In Progress）、`:19`（#3 條文）、`:26`（AC 未勾）
- 建議寫法：①「dirty」→「持有中（#1/#2/#5 已 commit，#3/#4 未落地）」；② 開工 prerequisite 加 #3 範圍／順序確認＋size gate 不擠壓條款
- 驗證式：`rg -n "dirty" ep.md` 全改；`rg -n "AIR-96 #3|bundle 瘦身" ep.md` 非空

## N2｜🟡（F1）｜S3 缺 `autonomous-execution` 修改指令

- EP 段落：S3 `:267`＋manifest `:329` vs 修改要點 `:271–279`
- 問題：列入寫入集合但零指令（`rg -n "autonomous" ep.md` 僅 :86/:267/:329）；其 crash-only reconciliation（真相源＝git＋EP 段落定義、不依賴 done 標記、非動態進度檔，`skills/autonomous-execution/SKILL.md:96–120`）與 S3「讀 EP 進度 checkpoint」需顯式調和
- 建議寫法：S3 補 bullet——Session Recovery 引用 `task-recovery.md` 順序；intent 維持 EP 段落定義，另加讀 S2 EP:219 欄位；deep-work 無 EP 弧沿用 journal
- 驗證式：S3 修改要點節有 autonomous 指令句（含「改為引用／加讀」）

## N3｜🟡（F1）｜S4 manifest 列名無指令（`deep-work`/`debrief`/`illustrate`＋S3 `state-md-write`）

- EP 段落：S4 manifest `:330`、修改要點 `:299–304`；S3 manifest `:329`
- 問題：`illustrate` 無強制產圖 mandate（opt-in；強制源 `illustrate-html-mode:76` 已排入），`debrief` 頭段與新設計已一致——列寫入集合會讓 implementer 空轉；`deep-work`（:88–89 pipeline、:155 pointer、:157–163 judge 流）缺處置；`state-md-write:13` 已一致，應 verify-only
- 建議寫法：manifest 拆「寫入集合」vs「verify-only」；debrief/illustrate/state-md-write（＋`commit`「只對帳引用」）歸後者；deep-work 補一條處置
- 驗證式：manifest 每列名有指令句或歸入 verify-only 清單

## N4｜🟡（F3）｜EP:204「由 S2 接完」與 S4 權責矛盾

- EP 段落：S1 驗證 `:204` vs manifest `:328/:330`
- 問題：sweep 四 pattern 命中含 S4 擁有的 `skills/CLAUDE.md`（`max-agents`）＋`skills/deep-work/SKILL.md`（`max-agents`；`3-perspective` 僅含 deep-work，**不含** CLAUDE.md——原報告此子句已由主 session 訂正，矛盾本體不受影響）；S2 不可能接完 S4 的檔
- 建議寫法：:204 改「按 manifest 分段承接（S2 接主鏈檔，S4 接 CLAUDE.md/deep-work；pointer-only 記免改），不得有無主 consumer；S2 出 disposition 清單，S4 開工核對」
- 驗證式：`rg -n "由 S2 接完" ep.md` 零命中；sweep 命中全覆蓋（exceptions 具名）

## N5｜ℹ️（F3）｜review JSON 內 `model-routing` 行錨漂移 +10

- `f68e77b` 淨 +10 行（numstat 11＋/1－，主 session 複驗）；references JSON 的 `:116/:172/:232` 已漂移。EP 本文 20 處行錨全準、錨定檔 baseline..HEAD 零變更。EP 免修；回查 JSON 行號時 +10 或直接 rg。

## N6｜ℹ️（F3）｜EP:56「S3 並行設計」易誤讀

- 句尾加「（設計可並行；**S3 實作待 S2 EP:219 欄位定稿**）」。

## N7｜ℹ️（F1）｜EP:222 主語模糊

- 改為「**judge/followup 均同步 identity 讀取指針**（judge 裁決前核對 `coverage` 未驗項，見 SM-12）。」

## N8｜ℹ️（F5）｜pilot（:317）未含 autonomous 路徑

- :317 加「若 deep-work 有改，pilot 加一 autonomous 小弧或顯式記未 pilot 維持舊語義。」（N3 判定 deep-work 免改則本條自動失效）

## S1｜ℹ️（F4，主 session 補充）｜compact 機制改善選項無處置交代

- EP compact 設計止於 S3 checkpoint-first＋恢復驗證；背景報告選項（codex §10 代際鏈／摘要存檔／pre-post 標定／換模型紀律；memory §8 verification 輕量版／semantic 指引／ZCode tail／transcript 錨／memory 半自動化）既未採納也未寫不做理由
- 建議：在 S3 Context 或範圍節加 disposition 表（選項／採納或不做／一句理由），或附「其餘背景選項未入本 EP，留待 compact 專弧」

## 回寫執行備忘（裁定通過後）

- N1–N4＋N6–N8＋S1 按上列驗證式逐條落地；跑完 lite followup 即可，無需重審
- 回寫改動 EP→同步重算 projection hash（HTML 兩欄＋planning-validation 換版記行，沿 `01eca3d` 模式）
- 開工三門維持：user implement 指令、AIR-60 對帳、HEAD/dirty＋治理檔核對
