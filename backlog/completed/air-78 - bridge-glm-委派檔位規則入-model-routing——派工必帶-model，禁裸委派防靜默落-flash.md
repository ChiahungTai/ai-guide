---
id: AIR-78
title: bridge glm 委派檔位規則入 model-routing——派工必帶 --model，禁裸委派防靜默落 flash
status: Done
assignee: []
created_date: '2026-09-11 23:38'
updated_date: '2026-09-12 06:01'
labels:
  - model-routing
  - bridge
  - governance
dependencies: []
references:
  - skills/model-routing/SKILL.md
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕把「bridge 派工給 glm 家族必須用原生 model 名指定檔位（旗艦 GLM-5.3、省額度 GLM-5.3-Flash）」寫進 model-routing skill 與全域 guide 詞彙規則——bridge alias 層已退役，混用 CC 詞彙（sonnet/opus）派 glm 會直接被拒。設計 v3 定案（09-12 晚），動工暫停等 user 觸發。

〔baseline：ai-rules 93b5c5a〕
〔已決策勿重辯：①落點＝skill external-runtime family 表加 glm row＋3 行 glm 專節（倣 webgpt 模式）；rules/ 零改動（M1 下沉後 rule 只剩詞彙＋必載條款，family enum 已含 GLM）②檔位語義：sonnet→flash 別名、opus→GLM-5.3 旗艦；lite 派 --model sonnet、full-tier 派 --model opus；裸委派禁止作為 routing contract（09-12 實測落 flash＋ledger effectiveModel null 無證明力）——delegate-bridge d4 default pin 落地前連 lite 都要顯式 --model（codex 收緊：provenance 論證）③審計語義：以 dispatch/requested model flag 為 authoritative evidence；carrier effectiveModel 現不具證明力④唯讀 carrier v1（寫入走 muse）＋--effort/--steps/--yolo 不適用——放專節不放表（表不塞肥）⑤resume/fork 定向接續表不加 glm row（session identity 連續性未證）——專節明寫 resume/fork semantics unverified; do not infer continuation support from muse/codex⑥in-harness 對照句寫條件式：「若 in-harness full dispatch 會繼承 Flash，則 full-tier GLM 工作改走 bridge --model opus」——AIR-76 落地後條件自然失效不留歷史特例⑦時序：嚴格兩弧兩 commit——M1 下沉弧完整落地並 re-read post-M1 skill 實際形態後才開工（root cause 不同：M1 收斂既有真相、本弧新增 family runtime contract，acceptance boundary 與 review identity 不同）⑧arc home 依當下已部署 task topology（legacy 頂層），AIR-77 遷移時搬——不提前走 YYYY-MM/（script depth 假設未翻轉＝false-green 風險：script 成功退出卻沒掃到新弧）；不在本弧順手修 scanner（第三 root cause 不混弧）。源工單＝delegate-bridge f821ca7 跨 repo 交接〕
〔驗收：①family 表 glm row＋專節在場②三 invariant 機械可驗——full 派單必產 --model opus、lite 必產 --model sonnet、unsupported flags 零送出（instruction 層能控制且能獨立驗證者；ledger effectiveModel != null 不屬本弧驗收——那是 delegate-bridge d4 責任邊界）③enum 反查：掃 muse/codex/--family/family switch/generic bridge command builder 暗含二值（只有兩家）假設處逐檔處置——agents/ 零改動須由反查證明而非 glm 零命中證明④rg -i family glm 每個委派指引點帶檔位語義；instruction sync/deploy 完成〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 family 表 glm row＋glm 專節落地（值域／native 檔位政策／審計語義（含 ledger model/effectiveModel 兩欄例外條款）／resume-fork unverified 句）
- [x] #2 三 invariant 機械驗證：full→`--model GLM-5.3`、lite→`--model GLM-5.3-Flash`（呼叫端顯式 tier→native 映射，bridge 不代解）、unsupported flags 零送出
- [x] #3 enum 反查完成（muse/codex/--family 二值假設全掃）；agents/ 零改由反查證明
- [x] #4 時序證據：M1 弧 commit 在前＋post-M1 skill 形態 re-read 記錄
- [x] #5 vocabulary invariant 進全域 guide Model Routing 段（always-on）：prose/doctrine 一律 native ID；CC 詞彙僅限 CC harness 接線；bridge 委派一律 native；禁 native+alias 複合
- [x] #6 機械 guard 入 instruction/doc 檢查鏈：compound-slug lint＋bridge 委派範例掃 `--model opus|sonnet` 殘留（alias 退役後這些字串＝bug）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-12 v2 工單修訂（源 delegate-bridge f821ca7 同 baseline、事實面翻新，含 file:line）——修訂原決策②③④、新增兩毒型〕
◆撤銷：原②「d4 default pin 落地前連 lite 都要顯式 --model」——前提消失：bridge 已 pin（glm.rs:39 DEFAULT_MODEL=sonnet），裸委派確定性落 flash。修訂後核心規則＝full-tier（judge/EP 規劃/重型裁量）必帶 --model opus；flash 段（機械/研究/findings）可不帶。禁裸 full-tier 委派不變。
◆修訂③審計語義：effectiveModel 於 job finalize 才落帳——running 中 runs 顯示 - 屬正常非未 stage；原「carrier effectiveModel 不具證明力」句撤銷（v1 live 觀察係 mid-run 誤讀）。
◆擴充④flag 表面（glm.rs:1010-1031 validate_flags，exit 2 fail-loud）：拒收 --trust-workspace/--steps/--yolo/--effort/--allow-workspace-switch/--network；收 --model/--background/--caller-session/--json/--resume＋positional prompt。「--trust-workspace --steps 800」形＝muse 專用，glm 照抄即炸——skills 內 bridge 委派範例須標 family 差異。
◆新增毒型A（fail-silent，最危險）：glm 載具恆 --mode plan（唯讀，R4 安全決策）——寫入型工單派 glm＝status=completed 但零檔案落地（live 實證：EP 規劃輪）。「GLM 寫」目前只有 orchestrator 直做；寫入型一律走 muse。專節重點標。
◆新增毒型B（三家族通用）：bridge spawn 面 one-shot、child stdin 恆 null（task.rs:610）——muse MSP turn/steer、codex turn/steer+queue、zcode app-server session/send 的 protocol 級 steer bridge 全不可達。操作語義：委派出去不能改道，只能 stop 殺了重派。muse/codex row 同步帶此句（通用事實非 glm 專屬）。
◆不變：落點（family 表 glm row＋專節）、rules/ 零改動、resume/fork 表不加 row（v2 收單含 --resume 但 session identity 連續性仍未證——維持 unverified 句）、兩弧時序（M1 後 re-read post-M1 形態再開工）、arc home legacy 頂層（AIR-77 遷移時搬）、enum 反查、驗收三 invariant（full→opus／lite→可不帶或 sonnet／unsupported flags 零送出——第二項依 v2 放寬）。

〔09-12 補裁決——sonnet 語源查證（glm.rs:50-51,442-455 源碼實查）〕sonnet/opus 與 GLM 無本質關聯——係 bridge 自 V1 JS 原型沿用的內部別名慣例（借 Anthropic 檔位詞彙）；解析順序＝裸委派→DEFAULT_MODEL sonnet→alias 表轉原生 id→才 stage 給 carrier；alias 表外值 pass-through 且不分大小寫——原生名 --model GLM-5.3／--model glm-5.3-flash 直接可用（僅擋非 GLM 模型）。zcode provider table（~/.zcode/v2/config.json）全為原生名鍵、零 sonnet/opus 鍵。**instruction 層詞彙裁決：原生名為 canonical**（full＝--model GLM-5.3、lite＝裸或 --model GLM-5.3-Flash，與 in-harness registry pin 詞彙一致）；sonnet/opus 降為「存在的別名」記載（辨識用不推薦）。user 09-12 提問促成此查證。

〔09-12 詞彙邊界裁定（user）〕glm family 詞彙面＝原生名專用：full＝--model GLM-5.3、lite＝裸（bridge 內建預設落 flash）或 --model GLM-5.3-Flash。sonnet/opus 係 CC 詞彙，禁混入 glm family 指引（opus 要用就走 CC）；bridge 內部 alias 映射（glm.rs MODEL_ALIASES）屬 delegate-bridge 實現細節，住該 repo docs、不進 ai-rules doctrine——與 CC 接線抽樣化同一原則（詞彙面進規範、接線 machine-local）。修正先前「sonnet/opus 降為存在的別名記載」條款：連別名記載都不留。驗收不變：full 派單必產 --model GLM-5.3（非 opus）。

〔09-12 晚 增量 v3（user 定案，取代稍早 transport-vocabulary 版本）——scope 擴編＋alias 層退役〕
◆①vocabulary invariant 進全域 guide Model Routing 段（always-on）——推翻原決策①「rules/ 零改動」：「Model references use native IDs in prose/doctrine (GLM-5.3, GLM-5.3-Flash)；CC 詞彙（sonnet/opus）僅限 CC harness 自身接線；bridge 委派一律 native ID——glm `--model GLM-5.3`／`GLM-5.3-Flash`（alias 已由 delegate-bridge d4 VR-1 退役→exit 2）；never compose a native name with an alias」。
◆②glm 檔位規則 native 版：full-tier 經 bridge＝`--family glm --model GLM-5.3`；省額度＝`--model GLM-5.3-Flash`；**呼叫端負責 tier→native 映射（bridge 不再代解**——d4 VR-1 alias 退役後 DEFAULT_MODEL（alias）不復存在，v2「bridge 已 pin、裸委派確定性落 flash、lite 可不帶」條款隨之失效——habits 漂移歸 doctrine 層改動，便宜）。
◆③ledger transport-token 例外條款：`model`＝caller 原始拼法、`effectiveModel`＝concrete native（parsed-success attestation）；analytics 鍵＝`(family, model, effectiveModel)`、身份認 `effectiveModel`；兩欄不合并。
◆④機械 guard：instruction/doc 檢查鏈加 compound-slug lint（native+alias 複合表達）＋bridge 委派範例掃 `--model opus|sonnet` 殘留（d4 落地後這些字串＝bug）。
◆⑤alias 層處置修訂：不再「歸 delegate-bridge 內部」——**已退役**（d4 VR-1，exit 2）；CC 詞彙邊界照舊。
◆時序狀態：M1（95831fb）已落地、post-M1 skill 形態已 re-read（09-12 本 session——skill 現形態含 22de4cb CC 詞彙面抽象化）；開工 metadata 已落 air-78 branch（ed80177：In Progress＋ref）；**動工暫停——user 09-12「先不要動工，要動工我會跟你說」**，恢復時在 air-78 branch 續行（先 rebase main 吸收本卡修訂）。

〔09-12 晚——delegate-bridge 2.0.3（39b6964）handoff 承接：AC#1 family 面先行落地〕model-routing skill 已補 glm（bridge）family row＋glm 專節（native-ID-only、裸委派預設 GLM-5.3-Flash、--write-mode edit、flag 面、ledger 語義、resume unverified 句）。**2.0.3 事實修正先前裁定**：①毒型A（glm 恆唯讀、寫入一律走 muse）過時——寫入委派＝--write-mode edit（headless 唯一寫檔檔位）、build 反而收緊為唯讀；②alias fail 形態＝exit 1 terminal failure entry（非 exit 2）；③裸委派語義再修＝預設落 GLM-5.3-Flash（非 error）——v3「呼叫端顯式映射」收斂為「呼叫端擁映射（tier 表即映射），bridge 不代解但 default 落 flash」。**剩餘 AC 待 user 觸發**：#5 vocabulary invariant 進全域 guide、#6 compound-slug guard 入檢查鏈、#3 enum 反查（muse/codex/--family 二值假設全掃）。另 rules-reminder relay closure 已裁定 N/A by design（[fg] 屬 orchestrator 側 Agent 派發語義，歸 tool-discipline＋agent-workflow，皆已同步；rules-reminder 職掌 Bash 命令紀律）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
glm bridge 委派檔位規則入 model-routing——family 表 glm row＋專節五條（native-ID-only VR-1/write-mode edit/flag 面/ledger effectiveModel 身份/resume unverified）、vocabulary invariant 進全域 guide、bridge_model_vocab 機械 guard（--family 行級 gate＋compound-slug 掃）、enum 反查 9+2 處（含 root AGENTS delegate-bridge 段、跨家族解析表補 glm）；雙審（codex job-mtxyjb0l＋flash code-reviewer）4🟡2ℹ️+1🟡5🟢 全採納修正；360 passed、deploy 3/3、活面掃描零殘留
<!-- SECTION:FINAL_SUMMARY:END -->
