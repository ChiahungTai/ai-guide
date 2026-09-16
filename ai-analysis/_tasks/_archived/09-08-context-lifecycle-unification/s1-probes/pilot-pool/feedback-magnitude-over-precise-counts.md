---
name: feedback-magnitude-over-precise-counts
description: 文件顯示 codebase 統計整數(importer/模組/test/node 數)用 magnitude 不用精確值;method(如實計數)與 display 分離
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4530f193-ff20-4127-a1c2-eacccaab4119
  modified: 2026-07-27T13:25:25.894Z
---

文件顯示 codebase 規模統計(importer 數、模組數、test 數、graph node 數)用 magnitude(數十/數百/幾乎全 codebase/上萬),**禁寫精確整數** — 精確整數每次 sweep/rebuild 必 drift,且「342」與「數百」對讀者決策零差異。精確計數只進機器檔(state.yaml)。

**Why**: 我曾提議「保留一個精確數當 grounding 證據」(hedge),user 糾正:magnitude 不損 grounding 誠實性 — 要說「數百」就非得真的 `rg -l | wc -l` / CRG `importers_of` 算過不可。所以「如實計數」(method,不能放 — 防 `rg -l | head` 截斷陷阱,見 [[modern-cli-preference]] truncation 段) 與「寫出精確整數」(display,該放) 是兩回事。該留的是結構事實(「enums 是 keystone」);該丟的是會 drift 的精確整數(「342」)。這是 `_ai-behavior-constraints`「禁統計快照」的延伸 — 該 rule 禁格式快照(行/字數),沒處理「結構但 drift-prone」的整數(如 importer 數),本原則補上。

**How to apply**: 任何文件產出(smell-detector baseline / code-review / illustrate / architecture doc)出現 codebase 規模整數 → 改 magnitude。判斷「精確 vs magnitude」:問「這數字會因 codebase 演化而過時嗎?讀者決策依賴精確值嗎?」兩者皆否 → magnitude。例外(保留精確):file:line 行號引用(精準定位非統計)、git sha(build provenance,tracked)、歷史定值事件(不 re-update)。真實案例:common/architecture.md 把 enums 342 / cash 16 / dfu 11(同檔又寫 12,矛盾)全改 magnitude,11/12 矛盾一併消失。baseline mode step4 圖2 已 encode 本原則。

**散文列舉內嵌計數同型 drift（2026-09-04 補）**: 手動維護的列舉清單內嵌精確計數（如 rules/AGENTS.md「…七組 rule+skill 分層」）在新成員加入時必漏 bump——AIR-22 添 modern-cli-preference 分層對後「七組」沒跟。修法＝成員補進清單＋拆計數詞改開放列舉（「…等 rule+skill 分層」）；同檔第二處「三組同模式分層」同批處理。列舉清單的計數是 display 非 method，寫下即開始腐化。
