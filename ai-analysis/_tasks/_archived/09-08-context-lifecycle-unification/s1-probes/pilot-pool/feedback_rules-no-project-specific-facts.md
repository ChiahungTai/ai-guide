---
name: rules-no-project-specific-facts
description: "通用規則:例子可領域特定(除權息等穩定概念 OK),規則邏輯才要通用;drift-prone 的是數字/現狀斷言/可改名符號/規則特化"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c850f69b-17e9-4015-92df-68e606aacae3
---

寫 `rules/`、`commands/` 等通用規則時,先區分**例子**與**規則邏輯**。

**核心 test:拿掉專案特定內容,規則還成立嗎?**
- **成立 → 例子,OK 領域特定**。除權息、dividend、`<domain edge>` 等穩定 domain 概念當 illustration 沒問題(具體有助理解)。掃描時別把例子當違反。
- **不成立 → 規則特化,要修**。規則邏輯本身就是專案 specific,如 llm-output-convention 的「NT Logger format」是 spec 內容本身(拿掉規則就空)→ 泛化或搬專案文檔。

**真正 drift-prone(要避免寫進通用規則)**:
- **數字 / 現狀斷言**(「15+ hits」「零覆蓋」)— 程式碼演進後過時,看起來仍像現狀
- **可改名的特定符號**(`_load_bars`)— 重構後 stale
- **規則邏輯特化**(spec 本身是專案 specific,見上)
- **專案命名慣例被泛化成通用慣例**(2026-08-23 實例:mosaic `callstack-v1/` 的 `-v1` 是 v2 cutover 需求的版號命名,被寫成「輸出目錄 callstack-v<N>/(版號=重生成世代)」通用慣例——user 抓到「一般 repo 就 callstack/,這是 mosaic 要弄 v2 才有的名字」。修法:通用預設 `callstack/`,版號後綴標「僅平行版本需求+mosaic 先例」;案例引註(golden sample)可留原名)——隱蔽型:不是數字不是符號,是**從單案例反推時把案例的環境巧合升級成規則**,起草抽象化 skill 時最容易犯
- **二階形態——例句自我激活**(同日連發:慣例修正後,例外例句寫「如 mosaic v1→v2 cutover 特例」——M2 在 mosaic 上實跑,executor 照例句合理推出 `callstack-v2/` 落點,錯)。教訓:**例外例句若把消費 repo 名為案例,會在該 repo 執行時自我激活**——通用 skill 的例外說明要寫成反例明示(「不是 X」)或抽象條件(新舊 code 並存跑),不要點名會執行這條 skill 的 repo 當「適用案例」

**Why**:通用規則要跨專案/跨時間適用。數字/現狀/可改名符號會隨專案演進漂移。實例:2026-06 build.md scope 例子用 mosaic_alpha 的 `_load_bars` +「15+ hits 全在 catalog」「零覆蓋」,但 tz bug 修復後已加 integration test,現狀非零覆蓋 → 漂移(acceptance-evidence 角度 6「測試過時」的文檔版)。但**穩定 domain 概念**(除權息)不漂移,當例子 OK。

**How to apply**:
- 例子:穩定 domain 概念可直接用(除權息、dividend);**數字/現狀/可改名符號**用抽象佔位(`<符號>`、`<param>`)或歷史標記(「曾發生於」+ 不用現在式斷言)
- 真實案例引用:歷史標記 + 不斷言現狀;數字必寫時標時點
- 抄其他 AI 的 dry-run 描述進通用規則前,查證當下現狀(該 AI 描述可能來自 memory 歷史狀態)
- 寫前自問:這符號/數字/狀態 5 個月後還對嗎?不會 → 抽象化。但 domain 概念(除權息)5 個月後仍對 → OK

關聯:[[ai-rules-dual-role-mosaic-shared]](mosaic skills 在 ai-rules 是 by design,非漂移)、[[feedback_verify-wt-before-commit]]。
