---
name: review-skill-state-rot-gap
description: 審查鏈 state-rot 針劑弧終態——codex 三輪 7/7 verified；F2＝跨家族解析表全 cell＋降級停下問 user；commit 2 已落地
metadata:
  node_type: memory
  type: project
  originSessionId: sess_f775f7f0-c166-4a08-a570-89f04c09d160
---

缺口實證：codex 全 repo 審查的 Important 幾乎全是跨弧累積 state-rot——diff-review 錨任務弧邊界，每個 diff 各自綠燈、累積錯誤；A 軸機器狀態審查原無席位。user「你就都做」→五針劑：state-review skill、acceptance-evidence「機械閘門環境前提」、judge-review「閘門候選」一問、（原）review-engine 兩節、model-routing codex 甜蜜點。首輪自查＝/consistency 13 檔（3 🟡 已修——**新增節必同步 frontmatter description 觸發詞，它是唯一 discovery 面**）。

**codex 二輪審查（2C+4I+1S）裁決全採納＋修復**（user relay；lesson-first）：

- **F1 read-only 假合約（Critical）**：標 read-only 的 skill 不得內建寫入/建卡副作用——backlog 建卡即 commit＝outward action，skill invocation 不構成授權。修＝state-review/judge-review 只提案（gate 候選清單），mutation 交 user 拍板/後續弧；報告落檔＝顯式 `--persist`。
- **F2 eligibility 結構性不可達（Critical）**：review 形態委派被「主價值＝implementation loop」條件擋死——gate 條件須 profile-specific（model-routing 拆：③④ implement 專屬；review/advisory 用 read-only transport＋跨家族成立＋可重現輸出）；external family 是 caller-relative。**解析表須全 cell 有定義**（codex 二輪抓出 muse caller 無合法候選——相異家族僅剩 codex 而 explicit-only 不可被解析繞過）：GLM/ZCode 與 codex caller→muse；muse caller→fail-loud（顯式指定或降級）；顯式同家族→fail-loud。降級措辭須 caller-neutral（「caller-harness full dual-context」——muse caller 情境寫「in-harness GLM」不精準，codex 終評非阻擋建議）。
- **F3/F4 work-order review variant**：共用十節合約是 implementation 形狀——review 委派需欄位**替換非豁缺**（§4→scope manifest、§10→findings schema 含 remedy 三分類＋驗收設計＋環境前提自曝）。**在 domain skill 宣稱全域輸出合約而不接 schema/消費端＝false-green**——review-engine 兩節撤回，合約落點＝work-order variant 單一源。
- **F5 凍結不凍 dirty／無 coverage 分母**：clean-tree 預設（dirty 記 diff hash＋untracked 指紋）＋結束前後比對 fail-loud 標 stale＋scope manifest 每 path 恰屬一 bucket（沒進 manifest＝未審，不得自稱 full-repo）。
- **F6 元資訊（校準後採納）**：弧內統計（成立率/測試數/日期）入 instruction 檔違禁令——語料庫 dated-case 先例存在（codex 讀法較嚴），弧內計數確屬 snapshot-prone，照裁刪留定性教訓；.py invariant note 的 dated case 屬該檔自身慣例不算違規。
- **F7 近名邊界**：state-review↔project-review 雙向 NOT-for（自然語言「review project state」會撞名路由歧義）。

狀態：F1-F7 全落地＋F2 補正閉合（殘留掃描 CLEAN／git diff --check／151 passed／連結零死鏈）；codex 三輪 followup 終評 6/7 verified→F2 open→修畢。**commit 2＝7 檔（state-review＋skills/CLAUDE.md＋acceptance-evidence＋judge-review＋model-routing＋work-order＋project-review；review-engine 撤回後零 diff 自然退出）＋backlog drafts，已 commit `94a5fc5`（09-06）**。關聯 [[project_codex-fullrepo-review-adjudication]]、[[reference_codex-config-zai-topology]]。
