---
name: spec-self-contained-foreign-handoff
description: 給外部 LLM 的 spec 必須自足（spec＋repo 唯一輸入）：痛點附後果、UC 三件、SM 自包含、findings 蒸餾成設計約束節（防重踩）；籌備期凍結下游
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 09-05（AIR-29）：「痛點，use cases, sm 補上跟寫清楚，背景也寫清楚。待會我會用 codex 來執行 /execution-plan，你不要亂動」——EP 的產生器將是 codex，不是本 session。

**Why**：外來 LLM 沒有任何人類對話 context——spec 的每個缺口＝它自行腦補或重新發明；本 session 已知的坑（雙家族 review 30 findings）若不蒸餾進 spec，codex 會原樣重踩（例：`--check` 先寫後讀偽碼 bug、fork 條款衝突、「rule 零改動」假前提）。對話裡的裁定（user 逐項指定的旗艦清單）也只存在對話裡——必須落成檔內權威表。

**How to apply**（寫跨 LLM handoff 文檔——spec／工單同構）：
- 自檢問句＝「對方只讀這份檔＋repo，能否正確執行不問問題」——背景現況（機制約束、實測行為）、痛點（列全＋每條後果）、UC 三件（消費者/行為/成功樣態）、SM（觸發→預期行為自包含，不引 EP 編號）、權威分類表直接內嵌（下游只引用）
- **findings 蒸餾節**：既有 review 結論以「設計約束」形式編入（分組列條），不是附 review 原文——下游 LLM 要的是「不要這樣做」的約束，不是 find­ings 歷史
- **scope 凍結**：handoff 籌備期只改 spec，下游產物（EP／殼）不碰——EP 舊稿宣告作廢待對方重寫，避免兩個來源競爭
- 權威表先成型（[[feedback_harness-model-orthogonal-axes]]「整理這張表先」）再同步引用物，禁散文版補丁

相關：[[feedback_work-order-contract-point-to-source]]（工單指向單一源——本條是它的姊妹：工單/spec 本身要自足）、[[agents-registry-split-design]]（首用實證）
