---
name: feedback_delegation-claims-verification
description: 委派 agent 依主 session 調查產出文件（EP/報告）時——調查打包成編號宣稱清單＋不盲從條款（逐項機械驗證、推翻附證據）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_505eb9a4-736e-4e30-b2d5-50cc545b0ad9
---

user 慣例（09-08 AIR-43 弧「一樣不盲從」）：委派 agent 基於主 session 調查寫文件時，prompt 不把調查當事實餵——打包成編號宣稱清單（C1-C7 形態：宣稱＋出處＋建議驗證法）＋明文條款「逐項用自己的命令機械驗證、推翻附證據、禁照單全收」。

**Why**：orchestrator 調查與 agent 產出共享信念來源時，agent 照單全收只會放大既有錯（本例 C7「mosaic 零 flash 牽連」被 EP agent 推翻——docstring 實有 flash lane 字樣）；宣稱清單化讓驗證義務顯式、推翻可對帳。

**How to apply**：委派 prompt＝宣稱清單＋驗證義務＋durable checkpoint（中間發現即時落盤 .agent-tmp/）＋寫入面限縮（只准寫任務產物與暫存區）；回報格式含 C 對帳表（verified／推翻＋證據／unverified）。主 session 回收時 load-bearing 數字仍要親自重跑（agent 的 SQL 我重核過 392/107 才轉述）——不盲從是雙向的。理論＝acceptance-evidence 證據獨立性。

相關：[[feedback_dual-family-review-dispatch]]、[[project_flash-vocab-audit-0908]]
