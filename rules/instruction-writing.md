---
harness-scope: neutral
paths:
  - "**/*.md"
bundle-projection: pointer
pointer-target: instruction-writing
bootstrap-pointer: "新增或修改 AGENTS.md、CLAUDE.md、rules 或 SKILL.md 等 instruction 檔前，先載入 `instruction-writing` skill；frontmatter、載體選擇、引用、Signal/Noise 與自洽檢查以該 skill 為準。條文語義變更（decision／authority／gate／authorization／acceptance 面）落地前依 review-engine 風險 profile 分類並完成所需審查腿；static-only 豁免（機械 predicate）與 deferred 回執以該 skill「落地前審查閘」節為定義源。"
---

# Instruction File 撰寫規範

修改任何 instruction 檔前必載入 **instruction-writing skill**；frontmatter、章節、引用、導航/Decoder Test、映射 drift、自洽五維與元資訊禁令以該 skill 為單一源。條文語義變更落地前依 review-engine 風險 profile 分類並完成所需審查腿（細節見 skill「落地前審查閘」節）；控制面修改在隔離 worktree（persistent card WT；canonical 主樹留 main）authoring、審查回執齊後才 merge canonical；canonical main 上控制面 commit 由 pre-commit guard 機械擋（ai-guide 形態＝`.githooks/control-plane-guard.sh`；per-clone 需設 `core.hooksPath`，未設＝閘未上線；他 repo 無 guard＝此防線退為純 LLM 紀律，以各自隔離慣例為準）。

## Always-on 核心

- 雙檔：每層 `AGENTS.md` 是 harness-neutral source，body 禁 Claude 專屬散文；`CLAUDE.md` 是 `@AGENTS.md` thin wrapper。全域 guide 獨立於專案 root；`@` 僅 Claude 展開，AGENTS.md 禁 transclude。
- Signal/Noise：保留設計理由、約束/邊界、失敗教訓、型別區別、Pipeline/慣例映射、共用基建、負空間、行為校準；易被合理化動搖的規則保留「補充論證／第一性原理」。
- 可推導簽名/參數/欄位、Class→檔案表、重複導航、>5 行完整範例屬噪音；泛用 rule 用 placeholder，真實失敗案例可保留專案實例但須標「真實案例」。
- **禁統計（行數/字數）、版本號、更新日期、Changelog**。
- 導航只負責概念→symbol 種子；symbol→位置交 LSP；Decoder Test 見 instruction-writing skill。
