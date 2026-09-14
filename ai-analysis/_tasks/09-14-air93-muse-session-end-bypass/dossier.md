# AIR-93 dossier：muse session-end 原生記憶寫入繞閘——機制調查（2026-09-14）

> 調查者：ZCode flash 主 session。本文檔＝codex／GLM-5.3 討論用 self-contained 素材。所有機械證據附路徑與指令；判讀與猜測分開標註。

## 0. 背景一分鐘

ai-rules 的 muse memory governance（AIR-54 起）：所有 muse memory 寫入（`add_memory`/`edit_memory` tool）被 PreToolUse hook 攔下 deny 並代存 repo `.agents/memory-inbox/`，consolidation（夜波/手動）六問審核後才入池。前提＝「所有寫入走 tool 層」。2026-09-14 mosaic_alpha 發現 muse 在 session 結束時以**非 tool 路徑**直寫池，繞過 hook——本調查確認該路徑的機制，收斂修法。

## 1. 事件時間線（機械證據）

| 時刻（09-14，+0800） | 事件 | 證據 |
|---|---|---|
| 10:41:03 | consolidation 流入快照 commit（88b1ae6，池乾淨態） | `git -C ~/Github/mosaic_alpha/.agents/memory log -- model-quota-status.md` |
| 10:41:36 | muse session 開啟：`security_mode: "yolo"`、workspace_kind=git；bridge 派發的 edit_memory 工作單（MOS-104 弧 memory 蒸餾稿） | session log `~/.local/share/muse/sessions/2026/09/14/01a09dca-9bd7-7fa0-a4ef-7c32719be6d7/session.jsonl` seq:session.opened payload |
| 10:41:54 | governance PreToolUse hook deny `edit_memory`→inbox 代存（job-mu0mzo98）；rejected receipt 在場 | mosaic journal＋`.agents/memory-inbox/rejected/` |
| 10:41:56 | assistant_message_committed（model 回覆完成） | 同 session.jsonl seq:137 |
| 10:42:08 | `session.end` payload 寫入；**全進程樹 log 關閉**（subagent logs 同秒） | 同 session.jsonl seq:169＋`stat` 兩 subagent session.jsonl |
| **10:43:51** | **mosaic_alpha 池 working tree 直寫 3 檔**（model-quota-status／model-routing-four-family-comparison／**project-tpex-nightly-gate-pollution＝被拒工作單的目標條目**）——**session log 已關閉 103 秒，無任何 tool 事件、無 inbox receipt**。同日另有 08:45:48 波（mos98／muse-behavior／zcode-platform 三檔，當晨另一 muse session teardown）——非孤立事件 | 池檔 mtime（codex advisory 獨立 stat 複核；1f8f6e3 commit message「trip 寫入」為兩波合併敘事） |
| 10:48:28 | consolidation regen commit（1f8f6e3）收編 muse 寫入＋蒸餾終態 | `git show --stat 1f8f6e3`（7 檔：5 muse 寫入＋_inventory＋tpex 蒸餾） |

補充：同日另一 session 01a09dd8（10:58 更新）＝consolidation 發現 CAS 衝突的後續 session（mosaic journal 記載，未逐行鑑識）。

## 2. 機制結論

**已確認（文檔＋binary＋現場證據）：**

1. **寫入者是 muse runtime 自身的 post-session 原生路徑**（writer component unverified——「teardown 再跑一次總結 LLM」是推斷非實證，103 秒 gap 與之吻合但 log 無記錄）：發生在 `session.end` 事件寫入後 103 秒、全進程樹 session log 關閉後；內容＝工作單委託的蒸餾內容（**被拒 edit_memory 的目標條目 project-tpex-nightly-gate-pollution.md 也在 10:43:51 波**——工作單內容被 teardown 套用）＋muse 自行增補的學習。非 shell tool、非 model tool call（log 內零 memory tool 事件）。
2. **PreToolUse hook 天然攔不到**：hook 綁 tool 事件（`muse-code/extending.md:94` 事件清單）；teardown 寫入不經 tool 層。
3. **sandbox 防線不涵蓋 incident lane**：`permissions.md:77`——sandbox 只約束 shell 工具（「agent can't rewrite its own memory」指 tool 面）；本寫入非 shell tool。incident session `security_mode: "yolo"`（bridge implement 委派通則＝--yolo，全關 sandbox）確定不受保護；**non-yolo 下 native writer 是否受 sandbox 約束＝unverified**（文檔未證明 runtime 內部寫入受 sandbox 管）。**兩道既有防線對 incident lane 皆無效。**
4. **官方文檔無開關**：`ref-docs/harness/meta/muse-code/configuration.md` settings 全鍵清單無 memory learning/sync 項；實機 `~/.config/muse/settings.json` 無相關鍵；feature-config gates（`~/.local/share/muse/feature-config/*.json`）僅 voice/monitor/plugins 等十項，無 memory 學習 gate。
5. **binary 字串表有候選 env vars**：`MUSE_EXPERIMENTAL_MEMORY_REPOSITORY_SYNC`、`MUSE_EXPERIMENTAL_MEMORY_REMINDER`（`strings` 級證據，語義未實證）。bridge muse runner 不注入任何 MUSE_* 變數、僅剝 META_API_KEY（`delegate-bridge/rust/crates/bridge-families/src/muse.rs:260` env_strip＋:302 env 組裝）——**incident session 未設這些 var 仍發生寫入＝預設行為含 repo sync**（或 var 是 enable-only、寫入另有預設路徑——未定）。
6. **非每 session 必觸發**：同日兩個 canary-ws 瑣碎 session（printf hello，10:05/10:11）結束後 workspace 無 `.agents/` 目錄＝零寫入。觸發條件候選假說：〔H1〕session 內有 memory 意圖/操作（incident session 有被拒的 edit_memory 工作單＋池內容）→ teardown 學習觸發；〔H2〕池目錄在場＋session 有實質內容即觸發。canary 無池無意圖，兩假說皆相容——未區分。
7. **`SessionEnd` hook 存在但 observational**（`extending.md:94`：「its output cannot block termination」）——攔截不可行，**偵測可行**。

**未知（需 live 實驗或討論裁定）：**

- 精確觸發條件（H1 vs H2）；`MUSE_EXPERIMENTAL_MEMORY_REPOSITORY_SYNC=0/1` 語義；teardown 寫入是否受 sandbox 狀態影響（非 yolo session 會不會也寫）。

## 3. 修法候選現狀評估

| 候選 | 現狀 | 約束 |
|---|---|---|
| ① muse 設定關閉原生寫入 | 官方設定面**無開關**；env var 候選存在但語義未證。若 `MUSE_EXPERIMENTAL_MEMORY_REPOSITORY_SYNC=0` 有效，**bridge muse runner 注入一行 env 即可落地**（我方控制面，不動 user 的 --yolo 通則） | 需 live 實證；experimental 前綴＝上游可隨時移除，不能是唯一防線 |
| ② 偵測網（池對帳） | 掛點候選：(a) muse `SessionEnd` hook（observational 但 fire）做 teardown 對帳；(b) 池 watcher（現有 governance hook 的 inbox 代存層延伸）——池檔 mtime/新檔無對應 inbox receipt→flag，併 memory-audit 機械層 | 偵測不攔截；事後补救路徑要定義（flag→consolidation 補審？直接 reject+regen？） |
| ③ sandbox `.agents` read-only | 對本路徑**無效**（結論 3）——runtime 內部寫入非 shell tool；且 --yolo 全關 sandbox 是 user 通則不可動 | 幾乎出局，除非上游未來把 teardown 寫入也納入 sandbox 政策 |

硬約束：implement 委派一律 --yolo 是 user 通則，**動不得**；修復不得破壞 bridge muse 委派主鏈。

## 4. 討論問題（codex＋5.3）

- Q1 修法組合：①（env var 實證後 bridge 注入）＋②（偵測網）並行？還是只②？①的 experimental 依賴風險怎麼對沖？
- Q2 偵測網掛點：muse SessionEnd hook vs 池 watcher vs memory-audit 機械層併入——哪層最穩（考慮 muse session 不只 bridge 派發，也有 TUI 互動 session 直開）？
- Q3 觸發條件要不要先做 live 重放實驗區分 H1/H2（成本：每次 muse exec＝LLM 額度＋teardown 學習可能 100s+），還是直接上對帳網（不管觸發條件，無 receipt 即 flag——條件無關）？
- Q4 驗收重放設計（卡 AC③）：如何機械化驗證「偵測網對 teardown 寫入會 fire」（造一個假 teardown 寫入？還是真跑一次 muse session-end？）
- Q5 現有池檔已被 regen 收編，偵測網上線後的存量對帳基線怎麼定（全池盤點一次 receipt 覆蓋？）

## 5. 相關檔案索引

- 卡：`backlog/tasks/air-93-*.md`；mosaic 證據 journal：`~/Github/mosaic_alpha/.agent-tmp/session-journal.md`（[09-14 遞延清償] 段）
- governance plugin：ai-rules `muse-plugins/memory-governance/`（hook 主體 `hooks/muse_memory_governance.sh`、def_hash 輪替、adversarial 回歸釘；測試 `tests/test_muse_memory_governance_plugin.py`）
- 過往 live 驗證 receipt：`ai-analysis/_tasks/done/09-12-muse-memory-governance-plugin/poc/live_receipt_20260914.md`
- muse 文檔鏡像：`ref-docs/harness/meta/muse-code/{configuration,permissions,extending}.md`
