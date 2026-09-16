# 工單：memory 池存量收斂波（移交 muse 執行；user 逐項核可）

> **執行結果（09-08 晚，ZCode session 代跑——muse 未執行本單，user 轉交）**：EXIT 15 全刪（錨點逐項驗證）＋MERGE 3→1（**keeper 改判＝`project_memory-cc-alignment-diagnosis-0905`**——外部引用 5 處已指向它、內容最厚，優於原提 #9 air40-42；merged_from 標記＋兩成員教訓收編）＋DISTILL 2 派 mem-distill 執行中＋HOLD 2 未碰＋新條目 desc 違規順手修（多行→一行情境句）。全檔備份 `memory/_trash-0908/`（20 檔）。索引 22,947→**20,001 chars gate PASS**（137 行）＋8 處 wikilink 斷鏈修復＋keeper 自身 2 dangling 清除。mem-distill 完成後 Stop hook 自動 regen 終值。

> 性質：**維護波次，非 AIR-45 EP 段**（結構修法在 AIR-45 S1 裁定＋S4 機制化；本波只做存量止血）。
> 治理合約單一源＝`skills/memory-audit/SKILL.md`（寫入端紀律／層 3 清理／蒸餾形態）——本單不重抄規則，只給範圍、證據與逐項建議。
> 治理三分離：本單＝advisory；**逐項 user 核可後才執行刪除/合併**（user 在場，逐項問）。

## 標的

- 池：`~/.claude/projects/-Users-ctai-Github-ai-rules/memory/`（ZCode 端 symlink 同源，兩端單一真相）
- 現值：索引 **22,780／22,500 chars gate FAIL（101.2%）**、153 行（軟上限 150）——本波目標 **chars <20,250（留 ≥10% 餘裕）**，硬底線過 22,500
- 順帶任務：兩條 >12K 肥條目蒸餾（body 面與索引面獨立結算）

## 逐項裁決表（22 條終態標記條目；分類＝建議，user 逐項核可）

分類：**EXIT**＝退出候選（repo 完全覆蓋→刪檔）｜**DISTILL**＝肥條目先蒸餾（蒸後再議 EXIT/壓縮）｜**MERGE**＝cluster 併入 keeper｜**HOLD**＝活躍線不動

| # | 條目 | 建議 | repo 錨點（核對用） |
|---|------|------|---------------------|
| 1 | project_ai-analysis-restructure-design | EXIT | done/09-02-ai-rules-three-pool、done/09-03-backlog-governance-design、air-14 卡 |
| 2 | project_air-38-routing-feedback-tier | EXIT | done/09-07-routing-feedback-tier、air-38 卡；旗艦資格條款已入 model-routing skill |
| 3 | project_codex-fullrepo-review-adjudication | EXIT | remediation a102f8e＋followup 11/11（git log --grep codex review） |
| 4 | project_air-26-push-collection | EXIT | done/09-05-external-runtime-push-collection、air-26 卡 |
| 5 | project_agents-registry-split-design（**12,697 chars**） | DISTILL | done/09-03-air13-unified-subagent-arch、done/09-05-agents-two-axis-refactor、air-28/29 卡 |
| 6 | project_card-branch-rule-proposal-pending | **HOLD** | 09-08 進行中（主場反轉案未收） |
| 7 | project_archify-illustrate-html-mode-eval | EXIT | done/09-04-illustrate-shell-template、air-23/30 卡 |
| 8 | project_codex-quota-death-durable-checkpoint | EXIT | rules/context-management.md durable-checkpoint 段＋部署 commit（git log --grep durable） |
| 9 | project_memory-governance-air40-42 | MERGE | done/09-07-memory-governance、air-40/41/42 卡——**keeper 候選**（memory 治理 cluster） |
| 10 | project_flash-vocab-audit-0908 | EXIT | done/09-08-model-vocab-governance、air-43 卡（新鮮但已收） |
| 11 | project_deep-work-cc-workflow-pipeline | EXIT | air-34 卡（結案） |
| 12 | project_flash-forensic-0905 | EXIT | air-24 卡＋model-routing skill 分工律段 |
| 13 | project_memory-card-lifecycle-gate | MERGE | done/09-07-memory-card-lifecycle-gate、air-37 卡——併入 #9 keeper |
| 14 | project_instruction-init-blueprint-scope | EXIT | skills/instruction-* 本體＋skills/CLAUDE.md 索引 |
| 15 | project_gate-severity-solidification-queue | EXIT | 治理/bundle commits（git log --grep gate/bundle） |
| 16 | project_memory-cc-alignment-diagnosis-0905 | MERGE | done/09-05-memory-system-recalibration、air-25 卡——併入 #9 keeper |
| 17 | project_post-build-command-dual-context | EXIT | skills/post-build＋review 鏈 skills 本體承載 |
| 18 | project_memory-redesign-read-path-0908 | **HOLD** | AIR-45 本弧（活躍） |
| 19 | project_postbuild-tour-repair-loop-0907 | EXIT | git log --grep postbuild tour（已 commit 閉環） |
| 20 | project_review-skill-state-rot-gap | EXIT | git log --grep state-rot / F2 解析表 |
| 21 | project_rebase-skill-nowt-ff-fix | EXIT | commits 0f6291e／33d6aa6／250f716（純歷史可推導） |
| 22 | project_cr-live-faces-roadmap（**13,004 chars**） | DISTILL | air-32/33 卡＋CR roadmap 文檔 |

預期結算：EXIT 15 行＋MERGE 3→1（−2 行）≈ 索引 −2,500~−3,500 chars → 落點 ~19,300-20,300；DISTILL 另結算 body 池 −15K+。

## 執行紅線（指針，規則本體在 memory-audit skill）

- **mtime 全池近期被重置**（備份還原指紋）——「近 7 天活躍 HOLD」規則失效，**改用弧收案狀態判活躍**（本表已標）
- EXIT 執行前逐條 `rg` 驗證 repo 覆蓋（宣稱「repo 已承載」須逐項附驗證路徑——**找不到證據的保守留**，降級為壓縮）
- 刪檔前 `rg "\[\[<name>\]\]"` 全池反向引用；MERGE 帶 `merged_from`；backref 修復
- desc 三不（不 hash／不日期流水／不 session id）＋≤100；body 蒸後形（教訓領頭、禁 timeline）
- 每步後 `python3 <pool>/_generate_index.py`——gate 值以輸出行為源，不信 prose
- **沙箱邊界**：pool 在 home——**寫不進就停手回報**（輸出逐條處置文本＝final body，不繞 /tmp、不降級路徑）；由 ZCode/CC session 落盤＋regen
- 禁碰：HOLD 條目（#6/#18）、`_generate_index.py` 本體、`MEMORY.md`（投影禁手寫）、本表外檔案

## 收尾與回報

1. regen 輸出行（含 gate 值）回報 user——目標 chars <20,250
2. 逐條差異摘要（EXIT 15＋MERGE 3→1＋DISTILL 2 的蒸前/蒸後 chars）
3. repo 面（本單＋EP 進度結算指針行）一併 commit；池本身不在 repo、無 repo diff
