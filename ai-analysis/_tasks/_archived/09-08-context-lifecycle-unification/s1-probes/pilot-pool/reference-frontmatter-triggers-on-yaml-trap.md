---
name: frontmatter-triggers-on-yaml-trap
description: skill/command frontmatter YAML 兩 trap——description 裸值含「: 」須 quoted；收尾 --- 必須自成一線（muse 嚴格拒收黏行）
metadata: 
  node_type: memory
  type: reference
  originSessionId: 16b8d8ba-41b8-40e0-85f8-4507a96004b2
---

skill / command frontmatter 的 `description:` 若**未加引號**且值含 `: `（colon-space，如「Triggers on: ...」），是 **invalid YAML** —— parser 把 `Triggers on` 當 nested mapping key，報「Nested mappings are not allowed in compact mappings」。

**實證**：`autonomous-execution` + `agent-workflow` 兩 skill 的 description 用裸值 +「Triggers on:」—— 潛伏 bug，某次 edit 觸發 Claude Code 重 parse 才浮現（skill 載入失敗）。修法：description 加雙引號 `"..."`（對齊 flow-review / at / handoff 慣例）。

**Why**：YAML plain scalar 不能含 `: `（colon+space = key-value 分隔符）。quoted string 可含任意 `:`。其他 skill 若有同 pattern 會同樣炸。

**How to apply**：改/建 frontmatter description 時，若值含冒號（尤其「Triggers on:」「Use when:」），**一律雙引號**。

## trap 2：收尾 --- 黏在內容行（2026-09-02 muse 實測）

`paths: ["**/*.py"]---`（closing delimiter 跟最後一個 frontmatter 值同行）——各家 harness 容忍載入，**muse 的 SKILL.md 驗證嚴格拒收**（錯誤訊息 "frontmatter must end with ---"）。

**實證**：ai-rules `python-type-gap` 長期如此、CC/ZCode 無感；muse 啟動掃跨 agent skills（`~/.agents/skills` 等共 91 個）時判 malformed。拆行修復後 `muse skills list` 乾淨載入（skills list 是本機操作不耗請求，可當 lint 用）。

**Why**：muse 是目前遇到最嚴格的 frontmatter validator；skill 一旦部署進 `~/.agents/skills` 就會被它掃到——「其他家容忍」不是安全依據。

**How to apply**：frontmatter 收尾 `---` 一律自成一線；跨 harness 部署的 skill 可用 `muse skills list --source all` 當驗證器。

關聯：[[cjk-char-corruption-rg-verify]]（同屬 instruction 檔品質 blind spot）、[[agents-registry-split-design]]。
