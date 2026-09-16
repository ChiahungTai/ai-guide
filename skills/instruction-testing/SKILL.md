---
name: instruction-testing
description: "Instruction artifact 行為驗證方法。建立或修改會約束、塑造 agent 行為的 rule、skill、AGENTS.md、CLAUDE.md，或懷疑 guidance 會被 rationalize、忽略、誤套時載入。觸發詞：instruction testing、skill-as-TDD、壓力情境、behavior test、rationalization、micro-test、wording、form-to-failure、surface gate、四態分類、機械觀察面、premature-action。"
---

# Instruction Testing — Instruction Artifact 行為驗證

本 skill 驗證的是「instruction artifact 是否真的改變 agent 行為」，不是文句看起來是否合理。靜態 authoring 規範仍由 [instruction-writing](../instruction-writing/SKILL.md) 擁有；證據強度與驗收宣稱遵循 [acceptance-evidence](../../rules/acceptance-evidence.md)。

方法論概念吸收自 superpowers `skills/writing-skills/SKILL.md` 與 `skills/writing-skills/testing-skills-with-subagents.md`，並依 ai-guide 的 diff 觸及面分型、A/B 軸與 L1–L6 證據語彙重寫；來源決策脈絡見 [sp 借鑒分析](../../ai-analysis/reports/_done/superpowers/02-sp借鑒到ai-rules.md)。不引入 superpowers 的 bootstrap／drill eval harness／plugin 分發結構；自研 validated adapter（scripts/skill_activation_probe.py）與 scenario 配方由本 skill 擁有，易漂移細節住 scripts/／durable report，body 只留跨 harness invariant。

## 何時載入

在下列情況載入本 skill：

- 新增或修改會要求 agent「必須／禁止／只有在某條件下」採取行動的 instruction。
- 修改輸出 contract、recipe、template slot，目標是讓 agent 產生不同形狀的結果。
- instruction 已經清楚，但 agent 仍在 deadline、sunk cost、authority、exhaustion 等壓力下繞過它。
- 想判斷一段 wording 是有效 guidance，還是只是作者覺得「看起來更清楚」。

若只是 typo、斷鏈修復、格式整理或不改變可觀察語義的文字修正，維持 [instruction-writing](../instruction-writing/SKILL.md) 的靜態檢查即可，不啟動完整行為迴圈。

## 先判 surface，再決定測試型（四 surface gate）

以 **diff 觸及面**機械判定測試型，不以檔名、`rule`／`skill` 類型或主觀風險感覺判定：

| diff 觸及面 | 判定特徵 | 測試型 |
| --- | --- | --- |
| **activation 面** | name、desc、trigger 詞、frontmatter、bootstrap pointer——改的是「skill 會不會被找到／觸發」 | positive＋nonmatch activation test（依機械觀察面 protocol） |
| **decision 面** | must／禁止／gate／authorization／fail-closed——改的是「agent 該做什麼選擇」 | behavior scenario；**discipline 類**（agent 通常知道規則，但速度、sunk cost、authority、方便性等誘因會推它違規；失效會破壞 workflow gate／安全邊界／驗收可信度）升完整 RED → GREEN → REFACTOR，pressure scenario 每個關鍵案例合併至少 3 種壓力；重要 wording 同時塑造輸出時可先跑 micro-test 篩措辭 |
| **output 面** | required field、template slot、recipe——改的是「輸出長什麼形狀」 | micro-test |
| **僅 typo／link／格式** | 不改變可觀察決策／輸出／觸發 | static-only：五維自洽、引用存在性與必要的 single-source drift 檢查（[instruction-writing](../instruction-writing/SKILL.md)） |

非三面關鍵詞、但寫得出可觀察失敗的語義編輯（典型＝technique／pattern／reference 類：風險是找不到、誤解、套錯方法，沒有「明知故犯」誘因）——至少輕量 retrieval／application scenario（代表案例＋一個 variation／counter-example），不降級 static-only。

判面不確定時，先寫一句可觀察失敗：「沒有這次修改，agent 會做 X；正確行為是 Y」。寫不出 X/Y，通常表示這不是行為驗證問題。

## 機械觀察面 protocol（跨 harness invariant）

判分紀律，適用 activation test、behavior scenario、輕量 retrieval／application scenario 與 micro-test：

- **control／treatment 對照**：treatment 只差待驗 guidance，其餘 context 與真實消費場景一致；沒有 control 的綠燈無法歸因。
- **判分只看 consumer-visible state**：agent 實際做了什麼（選擇、行動、載入了哪個 skill、必要欄位是否在場），不是它複述了什麼。
- **premature-action 檢查**：activation 判準＝「首個 consequential action 前 skill 是否已實際載入」——載入前出現實質 tool_use 即未觸發。
- **四態分類**：PASS／FAIL／UNEXPECTED（行為可觀察但非目標失敗——不與 FAIL 混淆）／INCONCLUSIVE（判分條件未被觸發，如環境故障）。
- **RUNS 統計 ≠ retry-to-green**：重複取分布（≥5 reps 是發現 instability 的最低門檻）；flaky 是訊號不是 regression，挑綠燈重跑是造假。
- **recall ≠ behavior 分層**：skill 清單出現、description 被複述＝recall 證據，單獨不構成 PASS。
- **present／missing 對稱**：positive（該觸發）與 nonmatch（不該觸發）場景同等公民——只測 positive 會漏誤觸發。
- **機械 matcher 只當 locator**：逐筆人工讀 flagged case——prompt 引用、反例文字、template echo 都會被誤計命中。
- provider／環境故障（session 起不來、stream 中斷）＝INCONCLUSIVE 或時間盒順延，**不在故障窗 retry-to-green**。

### per-harness activation 判讀基準（AIR-107）

activation 路徑是 per-harness 的——同一個 PASS 在不同 harness 的觸發機制不同，判分必須標注歸因 channel：

- **ZCode 端**（headless `--json` 實測，AIR-99 A5 取證）：available-skills 呈現**僅 name＋path**，desc／when_to_use 不進模型決策面。合法觸發路徑＝①rule 錨（rule 文本指向 skill，session 載入 rule 後按指引載入）②名字字面命中（user 輸入恰為 skill 名）③明示 invoke（Skill tool 點名）④**AGENTS.md 錨**（root／開場載入面的命令表在場＝session 起始即知，等價 rule 錨——tri 終審補，AIR-107 矩陣五支即此類）。**PASS 歸因紀律**：probe 綠燈若實際由名字字面命中造成，不得記為「desc 觸發 PASS」——AIR-87 舊四 PASS 重解讀＝名字字面命中非 desc 觸發（判讀錯誤的實證）。
- **CC 端**：desc 全文消費——desc 觸發為合法路徑，activation probe 可直接驗 desc 命中。
- **主路徑判準（ZCode 新 skill 驗收）**：以「rule 錨（或等價 AGENTS.md 錨）在場」為可觸發判準；名字語義弱（非自明）又無錨＝ZCode 端無觸發路徑——處置二選一（補 rule 錨／接受明示 invoke），矩陣治理＝AIR-107（`ai-analysis/_tasks/09-16-air107-skills-activation-matrix/`）。

## RED → GREEN → REFACTOR

這裡的 TDD 對象是 agent behavior。程式碼 TDD 的細節仍由 [test-driven-development](../test-driven-development/SKILL.md) 擁有。

### RED — 先取得 baseline failure

1. **固定 claim 與判分條件**：先寫「情境中什麼行為算 fail／pass」，避免看到輸出後移動標準。
2. **建立真實壓力情境**：discipline 類每個關鍵案例同時放入至少 3 種壓力，例如 time + sunk cost + authority；要求 agent 做選擇或採取行動，不問「規則怎麼寫」。
3. **拿掉待驗 guidance**：新 artifact 用 no-guidance baseline；既有 artifact 編輯以修改前內容作 baseline。其餘 system／project context 保持與真實消費場景一致。
4. **fresh context 執行**：每個樣本＝獨立 subagent 或單發 call（新 session）——guidance 放 system/project context、壓力任務放 user message；**禁在同一 session 連跑多樣本**（前一次的 rationalization、答案或評語會污染下一次）。整組樣本固定同一 model/family，跨 arm 才可比。
5. **逐字 capture**：保存 agent 的選擇、實際行動與 rationalization 原句至 `.agent-tmp/<弧>/`（scenario 編號＋逐字輸出＋判分），跨 session REFACTOR 弧才有原句可回收；不要事後替它概括成作者原先預期的理由。
6. **確認 RED 真的紅**：baseline 沒出現目標 failure，就沒有證據顯示這段 guidance 解了真問題。先重查 scenario 是否有代表性；仍不失敗就縮小或取消修改，不為了完成 TDD 人工製造失敗。

RED 的產物是「可重播 scenario + 預先固定的判分條件 + 真實 failure/rationalization」，不是一張「agent 理解規則」的問答卷。

### GREEN — 只補能對症的最小 guidance

1. 將每個 RED failure 對到一個具體缺口；沒有 baseline evidence 的假想例外先不加。
2. 依下方 **Match the Form to the Failure** 選 guidance 形式，避免用同一種 prohibition 解所有問題。
3. 用同一批 scenario、同一判分條件、fresh context 重跑；除了待驗 guidance 外不要偷偷增加提示。
4. GREEN 要看 agent 是否做出正確行為；只會引用／複述 instruction 不算通過。

若 GREEN 仍 fail，先做三分診斷再動手（照失敗形態選修法，非一律加字）：**清楚但故意無視**→加 foundational principle／權重；**內容漏了**→照缺口補；**組織上沒看到**（規則在場但被埋沒）→調結構與位置。修完再以同條件重跑；不要改判分條件讓既有輸出變成 pass。

### REFACTOR — 堵真漏洞，再保持 GREEN

GREEN 後只對已觀察到的新 loophole 重構：

- discipline failure：把新的 rationalization 加成明確 counter 或 Red Flags，再重跑原 scenario。**counter 只封已觀察到的 loophole**——禁為顯得 bulletproof 腦補假想藉口；無 baseline 證據的條款只增加噪音與新的協商空間。
- output-shaping failure：收緊 positive contract／recipe，不用更多「不要 X」堆成禁令牆。**recipe 贏了之後不再加但書**——實證警示：winning recipe 加一條 nuance clause 即可能讓行為退化。
- omission：把要求搬成 producer 必填的 structural slot，而非在遠處再提醒一次。
- conditional drift：把例外改寫成 observable predicate 對應 action，避免「全域規則 + 一串 exemptions」。
- technique／reference gap：補實際漏掉的判斷步驟、適用條件或 retrieval anchor（找得到、套得對、知道何時不該用）。

每次 REFACTOR 後都要重跑原本 RED scenario；修掉新 loophole 卻讓舊案例退化，仍未完成。

## Micro-test wording

Micro-test 用來比較措辭是否穩定塑造行為，尤其適合 output-shaping 或高風險 discipline guidance。先取得代表性的 RED baseline；進入 GREEN／REFACTOR 後，再用 micro-test 篩 wording，最後回到完整 pressure scenario 驗 treatment。它不取代完整行為驗證（output 面編輯以 micro-test 為指派測試型即收斂；本節『回到完整 pressure scenario』的適用範圍＝discipline 類 wording）。

1. **一定有 no-guidance control**：control 與 variant 使用相同真實 context／task，只差待測 guidance。control 不出現目標 failure，先停止加規則；**control 不失敗、既有 wording 卻失敗→優先懷疑既有 instruction 引入 regression**，考慮刪除或重寫而非疊加。
2. **每個 arm 至少 5 個 fresh-context reps**：每次都是獨立樣本（獨立 subagent 或單發 call——禁同 session 連跑）；固定 model/family/context，避免把模型差異誤判成文字效果。
3. **先定判分條件再看輸出**：用可觀察結果判定，如「是否輸出必填欄位」「是否先執行再宣稱完成」，不要用模糊的「感覺更遵守」。
4. **逐筆人工讀 flagged case**：引用 prompt、反例文字、template echo 都可能被機械 matcher 當命中；計數只能當 locator。
5. **variance 本身是訊號**：平均結果相近但 5 次各自解讀不同，表示 wording 還不 binding；優先調整形式與結構，不先加更多散文。

`5+ reps` 是發現 wording instability 的最低操作門檻，不是統計顯著性的宣稱。若要比較 provider／model，分成獨立實驗軸，不混進同一 wording 結論。

## Match the Form to the Failure

guidance 形式由 RED failure 決定。尤其是 **shaping 問題，禁止把 prohibition 當主要修法**：agent 需要的是「輸出應長什麼樣」，不是更多可協商的「不要做什麼」。

| RED 看見的 failure | 優先形式 | 不要用 |
| --- | --- | --- |
| 明知規則仍在壓力下跳過／違反 | **Prohibition + rationalization counter + Red Flags**；把實際藉口逐一封住 | `prefer`／`consider` 類軟建議 |
| 有做事，但輸出 shape 錯、重點埋沒、過度展開 | **Positive recipe／output contract**：直接定義組成與順序 | prohibition list；`不要重述／不要太長` 這類 shaping 禁令 |
| 既有產物漏掉必要元素 | **Structural slot**：REQUIRED field／template position | 離 template 很遠的 prose reminder |
| 行為應依情況切換 | **Observable conditional**：`if <predicate> → <action>` | unconditional rule 再附多個 exemption clause |

若一條 guidance 同時有多種 failure，拆成可分別判分的 contract；不要用一段「既禁止、又建議、又例外」的混合散文。

## A 軸證據天花板

subagent／fresh-context pressure test 仍是 **A 軸機器自驗證**。它能證明「在這組模型、context、scenario 下，instruction 對可觀察行為有影響」，不能證明需求本身正確，也不能取代 B 軸人類 viewport。

[acceptance-evidence](../../rules/acceptance-evidence.md) 的 L1–L6 名稱按**實際證據來源**分類；不要因 scenario 帶「對抗性」就把純 LLM pressure probe 自稱 L5。獨立 context 可降低 prompt contamination，但同家族模型仍共享偏誤，quorum 也不是獨立智能。

因此：

- 行為 loop 綠燈不得寫成「B 軸已驗收」或「production behavior 已證實」。
- 需要 L4–L6／人類觀察／runtime invariant 的 claim，仍按 [acceptance-evidence](../../rules/acceptance-evidence.md) 補對應證據。
- 高保護面的 instruction 即使 A 軸 pressure test 全綠，也只能降低「規則會被直接繞過」的風險；它不消除作者與 tester 共用錯誤前提的風險。

## 與靜態文件檢查的分工

| 載體 | 回答的問題 | 不證明 |
| --- | --- | --- |
| [instruction-writing](../instruction-writing/SKILL.md)「文檔自洽五維檢查」 | instruction 本身術語、結構、引用、前後邏輯、格式是否自洽；定義源變更是否有 single-source drift | agent 讀到後是否真的照做 |
| [consistency](../consistency/SKILL.md) | 單一 Markdown 的自洽、矛盾、順序、自包含、精準度與 Signal/Noise | guidance 在壓力下是否有效 |
| [doc-health](../doc-health/SKILL.md) | repo 文件的路徑／清單／Capabilities／SYSTEM-MAP 等準確性與 drift | 某句 instruction 是否造成預期行為 |
| **instruction-testing** | instruction 的可觀察 behavior effect、rationalization 與 wording stability | B 軸驗收、需求方向或 runtime invariant 本身正確 |

四者可串接，但不得拿靜態綠燈冒充 behavior GREEN，也不得拿 behavior GREEN 取代文件真相源／引用檢查。

## Pilot 草案：[must-execute-before-complete](../../rules/must-execute-before-complete.md)

設計稿（三個壓力情境＋兩個 harness 前提，**未執行、不構成 RED/GREEN 證據**）已遷至 [must-execute-pilot-scenarios](../../ai-analysis/_tasks/done/09-14-skills-corpus-contract-governance/materials/must-execute-pilot-scenarios.md)；執行時依本 skill 的機械觀察面 protocol 跑，結果由 pilot 弧承接。

## 完成判準

只有在對應深度真的跑完時，才可宣稱 instruction behavior 經驗證：

- [ ] 已按 diff 觸及面判測試型（四 surface gate）：沒有把瑣碎 edit 升格成全套壓力測試，也沒有把寫得出 X/Y 的語義編輯降級 static-only。
- [ ] 判分走機械觀察面 protocol：control/treatment 對照、四態分類、present/missing 對稱、RUNS 統計非 retry；activation 判準用 premature-action，recall 未單獨計 PASS。
- [ ] RED 的 failure／判分條件在看 treatment 前已固定，且 rationalization 為逐字 capture。
- [ ] GREEN 用相同 scenario 驗可觀察行為，不以規則複述代替 compliance。
- [ ] REFACTOR 只封實際 loophole，並回歸原 scenario。
- [ ] shaping guidance 使用 recipe／contract，沒有以 prohibition 作主要形式。
- [ ] 重要 wording 有 no-guidance control、每 arm 5+ fresh reps，並人工讀過 flagged cases。
- [ ] A 軸結果沒有被升格成 B 軸／L4–L6／runtime acceptance 宣稱。
- [ ] 靜態五維、引用存在性與 single-source drift 仍由既有文件工具另行完成。
