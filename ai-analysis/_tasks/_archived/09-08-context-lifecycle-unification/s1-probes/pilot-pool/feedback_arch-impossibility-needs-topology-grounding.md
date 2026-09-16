---
name: feedback_arch-impossibility-needs-topology-grounding
description: 「架構上不成立」級宣稱前必查依賴拓撲實態——引擎 in-process link vs 外部 server 包裝，成本結構完全不同
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

2026-08-28 實例：我宣稱「CR 完全取代 LSP 架構上不成立（build-time index 結構上給不出型別面）」——user 指出 `crates/pyrefly-producer` 是 **link Pyrefly 引擎本體**（非外包 server），宣稱被迫翻案為「分期可達」。

**Why**：類別假設（build-time 工具 vs live 引擎）掩蓋依賴事實——引擎在進程內，live 面只是「長出 per-repo 分析態」的標準工程；「不成立」的成本被我的分類直覺虛構出來。

**How to apply**：下架構結論（可行/不可行/單向門）前，機械查依賴形態——rg `Cargo.toml`/import 看引擎是 linked library、spawn 的 child process、還是外部協定服務；分類直覺不能替代拓撲事實。與 [[settlement-scripts-are-code]] 同族（正負宣稱同等查證），軸向＝對自己的「不可能」宣稱查證。

**2026-08-29 第二實例（變體：現狀接線 ≠ 架構邊界）**：對 user「plugin 一裝好自動經 PyPI 裝好 CLI」提案我列四個「辦不到」；user 要求「一個個拆解」後三個消解——PATH 順序一條命令可測卻先下了宣稱（實測 ~/.local/bin 先於 ~/.cargo/bin，shadow 方向與我說的相反）、`.mcp.json` /bin/sh wrapper 本身就是任意 shell 鉤子（就在眼前跑著卻說「沒有 install-time hook」）、「CLI 面只能手動裝」是把現狀接線誤當架構邊界。**How to apply**：宣稱「辦不到」前把障礙逐條列出、可機械測的先測（PATH 順序／存在性／既有鉤子的能力面）；「現在沒這樣接」≠「不可能這樣接」。
