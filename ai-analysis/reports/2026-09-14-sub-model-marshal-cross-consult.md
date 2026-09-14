# sub+model 派工考古 × Marshal 框架——三家顧問雙輪交叉諮詢報告

- **日期**：2026-09-14 晚；**baseline**：main `936a5cb`（tracked tree 全程 clean）
- **任務源**：user 指令——考古材料各自丟 muse／codex／glm 5.3 → 收回分析異同 → 再丟回取意見 → 再收斂 → 本報告 → `/illustrate`
- **顧問載體**：muse（muse-spark-1.3，bridge 預設 pin）、codex（chatgpt-web/high，adapter 預設）、GLM-5.3（bridge native ID 顯式）——全經 delegate-bridge 2.0.5，read-only advisory 工單形態，兩輪六 job 全部 completed exit 0
- **性質**：顧問材料非結論，最終裁決歸 user；討論歸宿＝[AIR-91 卡](../../backlog/tasks/air-91%20-%20model-派工詞彙整體治理——vision-旗艦-最強檔三題軸清理（先整體討論再動手）.md)（開放問題①–⑤）

## TL;DR

1. **覆蓋判定**：考古 17 模式中 **15 項已在 HEAD 條文化**（當天 15:46 的 commit `17a4fff`，標 "(air-91)"，補齊了最後一批）；**唯一真真空＝P11 Marshal 六角色框架**；現行條文間無結構性衝突——三家一致＋caller 機械複驗。
2. **落地載體收斂**：**agents/AGENTS.md 角色模型對照節**（詞彙層映射、派工行為零變化、單一源指針不重抄）；三家皆反對獨立 skill（無獨立方法論必淪空殼）與 rules 一句（裝不下六定義）。
3. **對照節「必寫」共識**：①三層同名 disambiguation（功能角色≠registry 載體≠家族 profile——防第二個「旗艦雙義」）②主 session 兼任兩職聲明（Marshal 職＋Policy 執行者；角色≠坐位）③CONFLICT→Arbiter 觸發句（框架唯一真增量——現行 contract 表是靜態 stage→owner，無狀態機）。
4. **待 user 裁決三項**（見 §五）：Arbiter 詞彙與坐位（三家三種立場）、verdict 三態 vs Decision 四態對齊聲明（2:1 傾向可省）、retry/escalation 歸屬行文。
5. **流程自身四項實證教訓**（§六）：外部 runtime 輸出截斷實況、多輪工單「摘要＋錨點」形態有效、effort 軸不對稱使橫向比較歸因不可靠、caller 過時判定被兩家顧問獨立糾錯（三家交叉的價值實證）。

## 一、背景與材料

| 材料 | 說明 |
|---|---|
| [考古報告](../../.agent-tmp/sub-model-usage-audit.md) | flash agent 產品（09-14 14:15）：user 派工指令 17 模式（P1–P17，逐字語錄＋固化三態）＋重複交代 Top8 |
| Marshal 框架原文 | user 09-14 清晨 selection side chat 貼入的 ChatGPT 討論框架（corpus L66113–66522）：Role 定 What／Policy 定 Who／Marshal 定 When；Role≠Model≠Harness≠Provider；六角色＝Marshal／Planner／Implementer／Reviewer／Verifier／Arbiter（Reviewer≠Arbiter：意見權 vs 裁決權） |
| 現行設計四檔 | [rules/model-routing.md](../../rules/model-routing.md)、[skills/model-routing/SKILL.md](../../skills/model-routing/SKILL.md)、[agents/AGENTS.md](../../agents/AGENTS.md)、[skills/agent-workflow/SKILL.md](../../skills/agent-workflow/SKILL.md) |
| 時序要點 | 考古報告（14:15）之後、本諮詢（21 時許）之前，`17a4fff`（15:46）已把 Top8 大半落地（post-build 標準收斂鏈、deep-work 自主授權形態、rules fleet 預設等）——round-1 工單因此帶了兩條過時判定（caller 漏讀 post-build／deep-work），GLM／muse 於 round-1 抓出並舉證，codex 於 round-2 修正 |

## 二、流程與方法

- **雙輪設計**：R1＝三家同一工單（必讀全量材料＋Q1 異同盤點／Q2 Marshal 落地／Q3 P13+P3 該不該固化／Q4 家族盲點）→ caller 逐題交叉分析（[round1-cross-analysis.md](../../.agent-tmp/marshal-consult/round1-cross-analysis.md)）→ R2＝交叉分析回派（R1 表態／R2 修正／R3 對照節最小草案 ≤15 行零 model 名／R4 家族盲點表態）。R2 工單只帶摘要＋錨點、不帶全量材料——GLM round-1 盲點建議（多輪 payload 經濟學）當場採納。
- **派發與收法**：背景 Bash 直呼 bridge 阻塞式（承載者契約）、派發確認行 `[Bridge] family=… model=…`、stdout 重導 `.agent-tmp/marshal-consult/round{1,2}-{muse,codex,glm}.out`、ledger 落 repo `.delegate-bridge/`；bridge pin 由 `installed_plugins.json` 當場 re-resolve（delegate@2.0.5）。read-only 舉證：三家皆附 `git status --porcelain` 前後一致。

## 三、Round-1 異同要點

**覆蓋面**（muse 逐項錨點表最完整；codex 同方向；GLM 報告頭部 transport 截斷、tail 表態同向）：

- 已覆蓋（代表錨點）：P1＝rules:19 seat 非 full 外派；P5＝skill:44 影像 flash；P6＝tool-discipline:34＋agent-workflow 背景 gate；P7＝agent-workflow:66-68 fan-out 三上限；P9＝skill:72-83 effort 對譯；P10＝skill:48＋失敗態表；P12＝skill:45＋webgpt 專節；P15＝skill:230/264 `[Bridge]`/`[Agent]` 確認行＋歸因紀律；P17＝role→requirement 表。
- 17a4fff 落地（round-1 當下即已含於 base）：P2＝rules:28 fleet 預設 lite；P3＝post-build:19-28 標準收斂鏈（角色鏈、不寫 model 名）；P4＝skill:155-159 顧問兩層語義；P8＝rules:29 主 session 不跑機械段；P13＝deep-work:167-170 顧問共識授權；P14＝skill:50 arc 內改判；P16＝deep-work:170 對抗驗證 opt-in。
- **真空**：P11 Marshal 框架——muse 實測 `rg "Marshal|Arbiter|Verifier" rules/ skills/ agents/` 零命中（唯一命中＝ui-visual-verify 同形異義）。

**Round-1 分歧（D1–D4，round-2 全數終結，見 §四）**：D1 P4 顧問語義（codex「intent 真空」vs muse 條文反駁）；D2/D3 P2/P8「已覆蓋 vs 該再抽象一層」；D4 P16「opt-in 是否該預設化」。

**Q2 落地（round-1 即高度收斂）**：反對獨立 skill（codex：非操作方法，skill 會削弱 invariant；muse：無獨立方法論必淪空殼或複抄）、不進 rules（裝不下）、不做暫不落地（user 已兩次採用宣告）；主張＝agents/AGENTS.md 對照節。Reviewer≠Arbiter 事實層已成立（review 產 findings→judge 裁決＝主 session full，contract L43-44），詞彙/schema 層未固化。真增量＝Marshal 的 state/retry/escalation/CONFLICT→Arbiter 語義。主要風險＝三層同名異物（Implementer 功能角色 vs impl-lite registry vs implement family profile；codex 同義：role 一詞雙義 workflow role vs registry role）。

**Q3（已終結）**：P3/P13 皆已固化（17a4fff），維持現狀不加碼；P13「共識判定規則」（全員一致 vs 多數）缺席但三家皆主張不補（會膨脹）。

**Q4 家族盲點（三家互補）**：

- codex：Role 層未描述 Role→Profile→Family→Bridge transport→quota/session 鏈；「跟codex討論」可對應三種 workflow（獨立 review finding／architecture advisory／multi-party debate）——同 model 不同流程
- muse：①輸出上限無預檢（webgpt 有三約束、muse 無對稱條款）＋ledger 只存 summary→截斷誤判 completed；②muse `--session-id` 續問 token 無實測值；③Agent-vs-bridge 禁令屬教育面；④transport 三態表缺「holder-session 死亡」第四行
- GLM：①多輪顧問輪數×payload 經濟學零條文（round≥2 帶摘要——本流程已採納）；②glm 無 effort 軸＝三家比較的不受控變因；③跨家族執行腿 write-mode flag 不對稱（`--write-mode edit` vs `--yolo`，照抄即炸）

## 四、Round-2 收斂結果

- **§0 機械修正被三家全數接受**：codex R2 自列三項修正（P3／P13／顧問語義）；muse 以 `git merge-base --is-ancestor` 機械重驗 17a4fff 並追認自家 C1–C3；GLM 補齊 round-1 遺失的 D1–D4 判定（結論不變）。
- **D1 終局**：P4 已覆蓋（skill:155-159 兩層語義含主次答案：常態經 bridge＝直接派、bridge 不可用＝paste-ready 轉貼備用）。muse 對 caller 糾錯成立——codex 是「標準之爭」（L157 答案算不算統一語義）非漏讀；codex Q4 的 profile/phase 細化＝未來 Marshal workflow 語義的增補候選，非缺口。
- **D2/D3 終局**：已覆蓋；codex 的「抽象一層」訴求＝對照節本身（命名不動條文），非現行缺陷。
- **D4 終局**：opt-in 為設計事實；**三家皆反對預設化**（GLM：對抗驗證的價值正在稀缺性，寫進標準鏈會稀釋且違「勿套會議儀式」精神）；落點＝對照節補一句「Arbiter／CONFLICT 觸發是例外路徑非預設鏈」。
- **R3 草案**：三家皆交（muse 7 行映射＋取捨理由；codex 極簡 prose；GLM 表格型）。「必寫」共識＝三層 disambiguation、兼任兩職、CONFLICT→Arbiter（＋retry/escalation 併句或註 a 指針）。單一源紀律共識：對照節只寫映射＋差異聲明，構件細節各歸其主（post-build「只鎖序與 gate」為先行範例）。

## 五、待 user 裁決清單（AIR-91 討論入口）

1. **Arbiter 詞彙與坐位**（三家三種立場）：(a) codex 草案以 Judge 取代 Arbiter（向現行 judge 詞彙對齊，六角色變五＋Judge）；(b) GLM 草案 Judge／Arbiter 分列——Judge＝findings→處置（主 session full，現行 judge-review），Arbiter＝共識破裂時最終裁決＝**user**（顧問僅意見權）；(c) muse 草案 Arbiter＝主 session 直做（findings→處置表，Decision 四態）。user 原框架：Arbiter 於 reviewer 衝突／重大異議／release gate 做最終判決。
2. **verdict 三態 vs Decision 四態對齊聲明**：muse＝必寫（已知 drift 點）；codex＋GLM＝可省（不引入第二套 schema、未決事項不宜挾帶）——2:1 傾向可省。
3. **行文取捨（低風險）**：retry/escalation 歸屬（併 CONFLICT 句 vs 引 contract 註 a 即可）；Verifier 界線句（獨立聲明 vs 表格列內帶過）。

## 六、流程自身的實證教訓（AIR-91／bridge roadmap 候選素材）

1. **外部 runtime 輸出完整性無預檢**：GLM round-1 報告頭部（Q1 逐項＋Q2 前半）在 transport 層截斷——stream `.out`、ledger `finalText`、per-job jsonl 三處一致缺失，caller 只能拿到半份報告。muse round-1 的盲點預言（輸出截斷→誤判 completed）被本流程實況命中。候選對策：比照 webgpt 三約束，為各 family 補輸出上限預檢條款／完整性訊號（round-2 完整到貨對照）。
2. **多輪顧問工單攜帶規範**：round≥2 改帶「前輪摘要＋特定追問＋錨點路徑」而非全量材料——本流程 round-2 實證有效（GLM：「我只需精讀 cross-analysis＋抽查五個錨點即完成表態」）。建議固化為 caller 端顧問流程慣例。
3. **effort 軸不對稱**：glm bridge 不收 `--effort`，三家顧問投入檔位不受控——**橫向「哪家報告更深」的歸因不可靠，本報告的比較面結論亦受此限**。三家 round-2 皆同意此限制。
4. **transport 三態表缺 holder-session 死亡行**：muse 建議增補一行（CC 側派長跑後關 session→他側誤判 interrupted），屬一行增補、零行為變化。
5. **三家交叉的價值實證**：caller 工單的兩條過時判定被 GLM／muse 獨立舉證糾錯——單一家族審查會漏掉的時序差，交叉即現形。

## 七、限制

- 顧問意見非結論；Arbiter＝user（§五待裁事項尤然）。
- GLM round-1 Q1/Q2 頭部遺失不可復原（§六-1）；其存活表態經 round-2 重驗維持。
- 橫向深度比較受 effort 軸不對稱影響（§六-3）。
- 語料面：考古報告僅掃 ZCode 端 user 原話（CC／codex／muse 端未掃）；muse 續問 token 量無實測值。
- 本報告 caller（主 session）座位＝GLM-5.3-Flash；報告整理係 user 明示交辦，judge 級裁決事項仍外推 §五由 user 裁定。

## 附：檔案與 job 索引

- 工單與中間產物：`.agent-tmp/marshal-consult/`——`work-order-round1.md`／`work-order-round2.md`／`round1-cross-analysis.md`／`round{1,2}-{muse,codex,glm}.out`／`round1-glm-full.json`／`session-journal.md`
- bridge job：round1＝`job-mu19arj3-r8ggkf`（muse）／`job-mu19arlh-vl0mdg`（codex）／`job-mu19arz3-eckgz2`（glm）；round2＝`job-mu19lavk-uc1tzu`（muse）／`job-mu19laxt-qqitaf`（codex）／`job-mu19lf8a-hj5skw`（glm）——ledger：`.delegate-bridge/jobs.json`
- 相關卡：[AIR-91](../../backlog/tasks/air-91%20-%20model-派工詞彙整體治理——vision-旗艦-最強檔三題軸清理（先整體討論再動手）.md)；相關 commit：`17a4fff`
