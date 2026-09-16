# skills×harness 觸發路徑盤點矩陣（AIR-107 機械段）

> 事實面產出：rule 錨／AGENTS 錨／名稱語義性皆 rg 機械掃描＋字面判讀；處置欄留主 session。掃描時點 branch=air-107。
> 口徑註記：錨判定以 `rg -ilw`（word boundary）為準——spec 原式 `rg -il`（子串）對短名（at／spec／implement 等）被英文一般詞彙淹沒，子串口徑僅在與 -w 分歧處於儲存格標註「〔子串口徑另有N檔〕」或「無〔子串口徑命中N檔，判子串噪音〕」。底線變體（如 code_review）已併入 pattern。
> AGENTS/CLAUDE 錨掃描宇宙（fd 實測）：root AGENTS.md／root CLAUDE.md／agents/AGENTS.md／ai-analysis/blueprint/AGENTS.md／hooks/AGENTS.md／rules/AGENTS.md；skills/CLAUDE.md 依 spec 排除（--glob !skills/**）。
> 錨語義注意：rg 命中是字面名稱出現，無法區分「指涉 skill」vs「同名 slash command」vs「同詞異義」——明寫「○○ skill」者為強錨；`code-reality` 的命中來自 toolchain 名（skills/code-reality 即該工具用法真相源，效果上仍指向 skill）。
> 抽驗紀錄（-w 命中行實讀）：`at` 兩檔皆真 skill 引用（rules/context-management.md:25「由 at/deep-work 觸發」、rules/outward-action-consent.md:33「投影端〔work-order／model-routing／at〕」）；`context7` 的 rules/AGENTS.md:72「context7 skill」為真錨（故雖非語義仍有觸發路徑）。**疑似噪音錨三例（-w 仍擋不住）**：`spec`→rules/bridge-dispatch.md:21「spec brief」（指規格文件，非 /spec skill）；`consistency`→rules/AGENTS.md:72「self-consistency 五維檢查」（hyphen 複合詞內含）；`implement`→rules/collaboration-constraints.md:25 大寫「IMPLEMENT」（流程步驟，非 /implement；其 rules/AGENTS.md:88 命中才是同名 command 引用）。

| skill | rule 錨 | AGENTS/CLAUDE 錨 | 名稱語義性 | ZCode 觸發路徑 |
|---|---|---|---|---|
| acceptance-evidence | rules/AGENTS.md、rules/acceptance-evidence.md、rules/collaboration-constraints.md、rules/quality-constraints.md | ./AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| agent-workflow | rules/collaboration-constraints.md、rules/tool-discipline.md | ./agents/AGENTS.md | 語義自明 | rule 錨 |
| api-and-interface-design | 無 | 無 | 語義自明 | 名字字面 |
| arch-thinking | rules/AGENTS.md、rules/design-thinking.md | ./rules/AGENTS.md | 語義自明 | rule 錨 |
| at | rules/context-management.md、rules/outward-action-consent.md〔子串口徑另有16檔〕 | ./AGENTS.md〔子串口徑另有4檔〕 | 半語義 | rule 錨 |
| audit-test | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| autonomous-execution | rules/outward-action-consent.md | 無 | 語義自明 | rule 錨 |
| blueprint-bootstrap | 無 | 無 | 半語義 | 名字字面（弱） |
| bridge-dispatch | rules/AGENTS.md、rules/bridge-dispatch.md | ./rules/AGENTS.md | 半語義 | rule 錨 |
| code-reality | rules/symbol-query-routing.md、rules/tool-discipline.md | ./AGENTS.md、./ai-analysis/blueprint/AGENTS.md〔子串口徑另有1檔〕 | 非語義 | rule 錨 |
| code-review | 無 | ./AGENTS.md、./agents/AGENTS.md | 語義自明 | 名字字面 |
| code-review-and-quality | 無 | 無 | 語義自明 | 名字字面 |
| commit | rules/AGENTS.md、rules/bridge-dispatch.md、rules/collaboration-constraints.md、rules/must-execute-before-complete.md、rules/outward-action-consent.md、rules/python-standards.md | ./AGENTS.md、./agents/AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| compact-prep | 無 | 無 | 半語義 | 名字字面（弱） |
| consistency | 〔噪音——見處置節〕rules/AGENTS.md 原列 | ./AGENTS.md、./agents/AGENTS.md、./rules/AGENTS.md | 半語義 | rule 錨 |
| context7 | rules/AGENTS.md | ./agents/AGENTS.md、./rules/AGENTS.md | 非語義 | rule 錨 |
| conversation-dispatch | rules/context-management.md | 無 | 半語義 | rule 錨 |
| corrections-weekly | 無 | 無 | 半語義 | 名字字面（弱） |
| cr-query | rules/symbol-query-routing.md | 無 | 非語義 | rule 錨 |
| cross-verify | 無 | ./agents/AGENTS.md | 語義自明 | 名字字面 |
| daily-maintain | 無 | 無 | 語義自明 | 名字字面 |
| debrief | 無（AGENTS.md 錨——見處置節） | ./AGENTS.md、./CLAUDE.md | 半語義 | 名字字面（弱） |
| debugging-and-error-recovery | rules/tool-discipline.md | 無 | 語義自明 | rule 錨 |
| deep-thinking | rules/AGENTS.md、rules/design-thinking.md | ./rules/AGENTS.md | 語義自明 | rule 錨 |
| deep-work | rules/context-management.md、rules/outward-action-consent.md | ./AGENTS.md | 語義自明 | rule 錨 |
| diagram-selection | 無 | 無 | 語義自明 | 名字字面 |
| doc-health | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| ep-review | 無（AGENTS.md 錨——見處置節） | ./AGENTS.md | 半語義 | 名字字面（弱） |
| ep-validate | 無（AGENTS.md 錨——見處置節） | ./AGENTS.md | 半語義 | 名字字面（弱） |
| execution-plan | rules/AGENTS.md | ./AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| fix-test | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| flow-feedback | 無 | 無 | 半語義 | 名字字面（弱） |
| flow-review | 無 | 無 | 半語義 | 名字字面（弱） |
| followup-review | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| frontend-ui-engineering | 無 | 無 | 語義自明 | 名字字面 |
| handoff | 無 | ./AGENTS.md、./ai-analysis/blueprint/AGENTS.md | 語義自明 | 名字字面 |
| illustrate | 無（AGENTS.md 錨——見處置節） | ./AGENTS.md、./ai-analysis/blueprint/AGENTS.md | 半語義 | 名字字面（弱） |
| implement | 〔噪音——見處置節〕rules/AGENTS.md、rules/collaboration-constraints.md 原列 | ./AGENTS.md、./agents/AGENTS.md、./rules/AGENTS.md〔子串口徑另有1檔〕 | 半語義 | rule 錨 |
| instruction-clean | 無 | 無 | 半語義 | 名字字面（弱） |
| instruction-init | 無 | 無 | 半語義 | 名字字面（弱） |
| instruction-sync | 無 | 無 | 半語義 | 名字字面（弱） |
| instruction-testing | 無 | 無 | 半語義 | 名字字面（弱） |
| instruction-writing | rules/AGENTS.md、rules/_ai-behavior-constraints.md、rules/instruction-writing.md | ./AGENTS.md、./CLAUDE.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| judge-review | 無（AGENTS.md 錨——見處置節） | ./AGENTS.md、./agents/AGENTS.md | 半語義 | 名字字面（弱） |
| kanban-board | rules/outward-action-consent.md | ./AGENTS.md、./agents/AGENTS.md、./ai-analysis/blueprint/AGENTS.md | 語義自明 | rule 錨 |
| kbar-form-analysis | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| lint-fix | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| llm-output-convention | rules/AGENTS.md、rules/llm-output-convention.md | ./rules/AGENTS.md | 語義自明 | rule 錨 |
| maintain | 無 | 無 | 半語義 | 名字字面（弱） |
| memory-audit | rules/AGENTS.md、rules/context-management.md | ./AGENTS.md、./CLAUDE.md、./ai-analysis/blueprint/AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| mermaid | 無 | 無 | 語義自明 | 名字字面 |
| metadata-sync | 無 | ./AGENTS.md、./agents/AGENTS.md | 語義自明 | 名字字面 |
| model-routing | rules/AGENTS.md、rules/model-routing.md、rules/outward-action-consent.md | ./AGENTS.md、./agents/AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| modern-cli-preference | rules/AGENTS.md、rules/modern-cli-preference.md | ./rules/AGENTS.md | 語義自明 | rule 錨 |
| nt-query | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| nt-v1-query | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| post-build | 無 | ./AGENTS.md、./agents/AGENTS.md、./hooks/AGENTS.md | 語義自明 | 名字字面 |
| python-type-gap | 無 | 無 | 半語義 | 名字字面（弱） |
| rebase | 無 | ./AGENTS.md、./ai-analysis/blueprint/AGENTS.md | 語義自明 | 名字字面 |
| review-engine | rules/_ai-behavior-constraints.md、rules/instruction-writing.md | ./agents/AGENTS.md | 半語義 | rule 錨 |
| rules-reminder | 無 | 無 | 語義自明 | 名字字面 |
| scan-project | 無 | 無 | 半語義 | 名字字面（弱） |
| self-contained-prompt | 無 | 無 | 語義自明 | 名字字面 |
| smell-detector | 無 | ./AGENTS.md | 語義自明 | 名字字面 |
| spec | 〔噪音——見處置節〕rules/bridge-dispatch.md 原列〔子串口徑另有5檔〕 | ./AGENTS.md、./agents/AGENTS.md〔子串口徑另有3檔〕 | 半語義 | rule 錨 |
| standup | rules/collaboration-constraints.md | 無 | 半語義 | rule 錨 |
| state-review | 無 | 無 | 半語義 | 名字字面（弱） |
| swing-analysis | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| symbol-query-routing | rules/AGENTS.md、rules/modern-cli-preference.md、rules/python-standards.md、rules/symbol-query-routing.md、rules/tool-discipline.md | ./AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| sync-sources | rules/AGENTS.md、rules/_ai-behavior-constraints.md | ./AGENTS.md、./rules/AGENTS.md | 半語義 | rule 錨 |
| test-driven-development | 無 | 無 | 語義自明 | 名字字面 |
| tool-discipline | rules/AGENTS.md、rules/bash-hard-rules.md、rules/code-edit-constraints.md、rules/python-standards.md、rules/tool-discipline.md | ./hooks/AGENTS.md、./rules/AGENTS.md | 語義自明 | rule 錨 |
| tour-bootstrap | 無 | 無 | 半語義 | 名字字面（弱） |
| trading-analysis | rules/design-thinking.md | 無 | 半語義 | rule 錨 |
| ui-collab | 無 | 無 | 半語義 | 名字字面（弱） |
| ui-visual-verify | 無 | 無 | 語義自明 | 名字字面 |
| upgrade-nt | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| upgrade-sj | 無 | 無 | 非語義 | （無——僅明示 invoke） |
| usage-ping | 無 | 無 | 半語義 | 名字字面（弱） |
| validation-strategy | rules/quality-constraints.md | 無 | 語義自明 | rule 錨 |
| voice-notification | 無 | 無 | 語義自明 | 名字字面 |
| zcode-session-query | 無 | 無 | 語義自明 | 名字字面 |

## 統計

- 總數：82
- 有 rule 錨（-w 口徑）：31／82（子串口徑：31）
- 無觸發路徑（僅明示 invoke）：6——kbar-form-analysis、nt-query、nt-v1-query、swing-analysis、upgrade-nt、upgrade-sj（**口徑註**：此欄＝「無自主觸發路徑」總面還有 16 支「弱名字＋無 AGENTS.md 錨」者——見下方名字字面（弱）分類；它們同樣無 autonomous path，差別僅在政策上接受現狀（fail-driven）。統計拆兩軸呈現＝tri 終審 codex 腿 P2 修正）
- 名字字面（弱）：21——blueprint-bootstrap、compact-prep、corrections-weekly、debrief、ep-review、ep-validate、flow-feedback、flow-review、illustrate、instruction-clean、instruction-init、instruction-sync、instruction-testing、judge-review、maintain、python-type-gap、scan-project、state-review、tour-bootstrap、ui-collab、usage-ping
- 名字字面：24——api-and-interface-design、audit-test、code-review、code-review-and-quality、cross-verify、daily-maintain、diagram-selection、doc-health、fix-test、followup-review、frontend-ui-engineering、handoff、lint-fix、mermaid、metadata-sync、post-build、rebase、rules-reminder、self-contained-prompt、smell-detector、test-driven-development、ui-visual-verify、voice-notification、zcode-session-query

## 處置（主 session 判讀層——AIR-107 AC#2）

> 事實表（上節）＝flash 機械掃描；主 session 已抽驗（六支零路徑複核、context7 真錨、三噪音錨確認——全吻合）。本節為逐群處置，事實表不逐行改寫。

### 錨點修正（抽驗發現——2026-09-16 主 session）

三支「rule 錨」降級為噪音（字面誤中）：`spec`（bridge-dispatch.md「spec brief」指規格文件）、`consistency`（rules/AGENTS.md「self-consistency」複合詞）、`implement`（collaboration-constraints.md「IMPLEMENT」流程步驟）。三者 root AGENTS.md 命令表／開場導引皆在場（session 載入面即錨），觸發路徑實質不受影響。

### 無觸發路徑六支 → 兩類處置（tri 終審 codex 腿修正拆分）

- **補錨（2 支）**：`nt-query`、`nt-v1-query`——自身 when_to_use 即要求「調查 NT runtime 行為前自主載入」（`Load BEFORE diving into v2 source`），user 不會點名 skill 名——照「補錨只為 session 必須自主觸發的 skill」原則**應補錨**；錨落 root AGENTS.md（ai-guide 專屬工具鏈行，不進全域 bundle——2026-09-16 tri 終審後補）。
- **接受明示 invoke（4 支）**：`kbar-form-analysis`、`swing-analysis`、`upgrade-nt`、`upgrade-sj`——事件驅動／user 點名語境（升級程序、特定分析），補錨＝以 always-on bundle 預算購買事件驅動觸發，違反寫入門檻（預設少寫）。合法終態，非缺口。

### 名字字面（弱）21 支 → 兩類

- **AGENTS.md 錨在場（5 支）**：`debrief`、`ep-review`、`ep-validate`、`illustrate`、`judge-review`——命令表在場，開場載入面即觸發路徑，無需補錨。
- **無 AGENTS.md 錨（16 支）**：`blueprint-bootstrap`、`compact-prep`、`corrections-weekly`、`flow-feedback`、`flow-review`、`instruction-clean`、`instruction-init`、`instruction-sync`、`instruction-testing`、`maintain`、`python-type-gap`、`scan-project`、`state-review`、`tour-bootstrap`、`ui-collab`、`usage-ping`——處置＝**接受現狀（無 autonomous path、政策性接受——鏈內 skill 互指＋slash 明示可達）**，補錨留待實際觸發失敗實證（fail-driven；無觀察到失效前補錨＝投機加稅）。本矩陣使這 16 支機械可查，後續 activation probe 失敗時按 instruction-testing 判讀基準升級處置。

### 處置原則（單一源）

補 rule 錨只為「session 必須在 user 未點名時自主觸發」的 skill；事件驅動／viewport／slash 命令／鏈內互指形態的 skill，接受明示 invoke 是正確終態。
