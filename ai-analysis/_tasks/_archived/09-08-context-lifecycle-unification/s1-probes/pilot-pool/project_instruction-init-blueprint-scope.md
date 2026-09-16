---
name: project_instruction-init-blueprint-scope
description: instruction/skill 體系線終態——init×blueprint 定案、commands→skills 遷移、調用紀律、arch-thinking 中性、sync 慣例
metadata:
  node_type: memory
  type: project
  originSessionId: sess_d8de15e8-a98d-4c74-b58e-b5ba869564d7
  merged_from: [project_commands-to-skills-migration-debate, project-skill-invocation-discipline-rule, project_instruction-sync-consistency-0904, project_arch-thinking-family-neutral-contract]
---

instruction/skill 體系線：instruction-init×blueprint 範圍（主體）＋commands→skills 遷移＋skill 調用紀律＋arch-thinking 家族中性契約＋instruction-sync 慣例，全收案。

## instruction-init × blueprint（核心定案四項）

1. **instruction-init 不直接產 blueprint**：受眾二分（instruction-init=軌道①機器導航 vs blueprint=軌道②人類合成視角）、生成策略相反（bottom-up 導航 vs top-down 敘事）、**ghost blueprint 風險**（無治理契約的結構快照落地即 rot，頂 blueprint 名義給虛假信心）、可生成切面窄
2. **骨架＋人機協同模型**（化掉 ghost 風險）：骨架生成（機械：目錄＋治理模板＋section 骨架）→協同完成（狀態標記＋**半滿落地原則**——半滿文檔誘導力強於空清單）→持續保鮮（**更新鉤子掛既有流程**：build 5a→daily-ops-map、arc 收尾→align 覆核——防骨架淪為永久空清單的唯一可靠機制）
3. **blueprint-bootstrap 獨立 skill 已落地**：不併 tour-bootstrap（三異質切面＋**時序做反**——blueprint 先成熟 tour 後消費，合併強迫「用一半」）；不建編排層（pointer 鏈模式足夠）；既有 repo 走 audit 模式（drift 盤點不重建；既有內容是人類策展資產 AI 只報缺口不代寫）
4. **callstack 生成章節＝tour-bootstrap 斷點③解法**：user 糾正關鍵事實＝callstack-v1 是 LLM 一天額度產生——斷點③是「程序未固化」非「人寫不可再生」

- **觸發拓撲＝成本分層服務鏈**：callstack 高成本＝獨立觸發＋停點報價（~146M tokens/2h vs 單 session 一天額度）；tour-bootstrap 無 callstack＝不產任何 tour、只枚舉入口鏈（~3M ≈2%）；**成本紀律＝副作用紀律的資源版**——skill 不把高成本操作藏在流程建議裡
- **三軌準則（D-e 翻案 D-a 入口錨定）**：錨定問句＝「這條鏈回答什麼**使用者問題**」——D-a 的「機械收斂性」是生產者視角（使用者不在意你怎樣做）；呈現解綁＝callstack（md 給人讀）與 tour corpus（.tour JSON 機械約束）不必同構，唯一硬耦合＝資料流邊
- **兩 UC 框架**：UC-A 理解既有／UC-B 變更伴隨；盤點入 plan、生成仍獨立觸發（定案詳 [[cr-live-faces-roadmap]] UC 段）
- 方法論教訓：**決策翻案後已發 handoff 必須整份重製 self-contained v2，不可 errata 附錄**；壓縮規則行時語義優先於 bytes；驗證矩陣——fresh 生成 session 禁 git log（commit message 洩題＝最大污染源）、成功判據＝正確留白非重現內容

## commands→skills 遷移（完結，單一載入點定案）

- **兩事實**：① ZCode 端 AI 經 Skill tool 調不到 commands（跨命令編排鏈自主調用會斷）② Claude 官方已把 custom commands 合併進 skills。乾淨路徑＝全面遷移＋刪 commands/（不留相容層）
- 36 命令遷移；`build` 定名 `implement`——**ZCode 有未文件化保留名**（probe 改名實驗定案），命名新 skill 避開 `build`；遷移腳本序列 replace 會二次匹配——序列改寫後必跑全 skills 相對連結解析驗證兜底
- **How to apply**：新工作流一律 `skills/<name>/SKILL.md`；改動後 settings.json `Skill(<name>)` 同步（skill_allowlist_coverage 閘門會抓）

## skill 調用紀律（固化 rules/tool-discipline.md）

- **觸發案例**：mosaic 一日三 EP 全由 agent 裸寫、未載 execution-plan skill → hook 殼/delta tour/post-build 階段 5 整線**靜默**缺席（下游合法跳過，事後不可見）。user 裁定：問題在編排者跳過方法論，不在 agent 載體
- **固化形態**：意圖對應既有 skill → 主 session 必先載入再分派；用 agent 做 X 只換載體不換方法論（自寫遵循，或把 skill 路徑注入 agent prompt 令其先讀再做）

## arch-thinking 家族中性契約（09-04 定案）

- **方法論綁角色、不綁家族**——implementer 與 reviewer 讀同一份；禁拆 GLM 版/muse 版（定義源漂移、muse findings 回 GLM judge 無共同語義可裁決）；注入點跟角色走，互換零改動
- **結論權不互換**：muse review 補視角、in-harness 主審＋主 agent judge 定結論；**證據強度不對稱 by-design**（external runtime 無 LSP/MCP 面→天生 rg 級；GLM judge 用 LSP/CR 補驗證＝互補迴路非缺陷）
- **反模式（禁重辯）**：不拆家族版方法論；skill 內不寫家族/model 名（數字型號只在 model-routing skill）；工具教學不塞 skill（由工單「工具接線」承載）

## instruction-sync 慣例（09-04 收束）

- 核心層全過的機制面：agents registry shared 拷貝 cmp 一致＋claude 差異僅 MCP 行（符合文檔預期）；**「漏 mem-distill」finding 是 agentsMd 快照過時假象**（session 開始注入的快照取於並行 commit 前——快照過時教訓入 [[feedback_relay-claims-verify-current-state]]）
- 拆「七組」「三組」精確計數改開放列舉——添新分層對後清單沒跟（精確計數的散文版陷阱）
- **流程事實：instruction-sync 做完不自動跑 /consistency**（工作流僅 instruction-clean→instruction-sync；consistency 只在 /post-build docs 段）——要接跑需明示
- 並行 session 落地驗證：user 裁定後 rg 現值驗證攔下重複編輯、零動手；commit message 明示排除本 session 檔（工作目錄紀律運作正常）

關聯：[[archify-illustrate-html-mode-eval]]（軌道②模型＋layer 3）、[[cr-live-faces-roadmap]]（UC 框架）、[[agents-registry-split-design]]（家族 dispatch）、[[feedback_llm-native-no-skill]]、[[feedback_dual-family-review-dispatch]]
