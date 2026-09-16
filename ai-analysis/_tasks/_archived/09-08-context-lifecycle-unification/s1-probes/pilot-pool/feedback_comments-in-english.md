---
name: comments-in-english
description: 新寫程式碼的註解/docstring/README 一律英文（user 2026-08-25 指示，新 repo 公開導向）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_03a95bfb-afca-4b31-a259-060d932f97ce
---

2026-08-25 user 在 code-reality 新 repo 實作（EP S1）時指示：「另外註解那些都用英文寫」＋「之後那邊的 commit 也是」＋「root AGENTS.md 要寫清楚都用英文，因為這可以給其他人用，且可以 open source 放 remote GitHub」。

**Why**：code-reality 是公開導向 repo（給其他人用、open source 上 remote GitHub）——**全英文化**含 instruction 檔無例外；搬家碼既有 zh-TW docstrings 不回改（搬遷零改動約束）。

**How to apply**：判準＝**repo 是否公開導向**。公開 repo（code-reality）：comments/docstrings/README/**AGENTS.md**/commit message 全英文；私有生態 repo（ai-rules、mosaic）維持原慣例（zh-TW instruction＋commit description）。後續流程定案：S1 後工作目錄轉 `~/Github/code-reality`，先跑 `/instruction-init` 建指令檔再進 EP S2。與 [[cr-live-faces-roadmap]] 搬遷零改動約束相容：只約束新寫內容。
