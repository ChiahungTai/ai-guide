# EP：memory 系統矯正——CC 對齊四項＋線聚政策

> **ep_type**: implementation
> baseline: 836c645
> 定稿：09-05（雙軸 EP review 15 findings 全採納＋user 兩項 S3 增補——處置表見文末）

## 實作總覽

2026-09-05 診斷（arch-thinking＋池量測＋CC 官方文檔對照）確診 memory 池貼頂運行的兩個根因：**寫法**（條目＝弧編年史——commit hash/session id/日期流水，違反官方「可推導就跳過」memory.md:351）與 **distill**（gate FAIL 拒寫→索引停滯→新條目不可見＝召回斷裂；outflow 三件套無一有觸發時機）。本 EP 落地四項矯正＋線聚政策，對齊官方 memory.md 設計。

**已決策勿重辯**（user 09-05 裁定「全做」＋後續增補）：

1. **S1 gate 失敗模式改 CC 式**：generator 永遠寫出索引（`--check` 除外）；超限改錯誤訊息命令當下 session 縮（官方 memory.md:401-403）
2. **S2 desc 內容契約**：禁 commit hash（desc＝觸發詞＋一句鉤子；≤100 chars 既有紀律保留）＋**存量 3 檔 desc 一併清償**（review 增補）
3. **S3 結案即蒸餾**：弧結案兩步時 owning session 重寫該弧條目為終態 facts；掛點**四處**（kanban 源＋memory-audit＋context-management rule＋execution-plan 收尾段 inline 處）（review F4 增補）
4. **S4 一次性清償＋線聚**：top-14 in-place 蒸餾 ≤8K/條（Phase 1 已先行）＋存量 3 檔 desc-only 清償；Phase-2 語義同線 cluster merge（慣例真相源＝memory-audit 層 3，review F1 修正引用）
5. **線聚政策**：不採固定 30 mega 條目/目錄分群/索引分節；採「弧歸線」——project 弧 journal（實數 55 條）按線聚成 12-15 線條目（30 上限），feedback（64）/reference（23）保粒狀。**條目數學（review F8 覆核）**：索引 overhead 10 行→條目硬頂 ≈**180**（190 行 gate−overhead，非 190）；穩態 144−55＋12~15＝**101~104 條** ∈ 目標 100-110 ✓；索引水位目標 ≤20K chars／≤160 行
6. **寫入第五問**（user 增補）：寫 memory 前判定載體——「每次都要的紀律→rule／on-demand 方法論→skill／跨 session 事實→memory」——手冊形內容不住 memory
7. **承諾不進 memory**（user 增補）：承諾/待辦的載體是 backlog 卡；memory 只收事實與教訓

## UC 盤點（元專業：受影響命令/rules 清單）

| 面向 | 檔案 | 變更 |
|------|------|------|
| 索引 generator | `skills/memory-audit/scripts/generate_index.py`（147 行）＋池內 `_generate_index.py` 副本（cmp 對帳；本機僅 ai-rules 池有部署——mosaic 池無副本，handoff 項附驗證命令零命中即 N/A） | S1 |
| 寫入 hook | `hooks/block-memory-index-write.py`（DESC_LIMIT=100 定義於 **:38**／BODY_LIMIT=12K） | S2 |
| 寫入紀律 | `skills/memory-audit/SKILL.md`「寫入端紀律」段（L110+；marker 語義 :35） | S2/S3 |
| 結案流程 | `skills/kanban-board/SKILL.md`「結案兩步」（源）＋ `skills/execution-plan/SKILL.md:373` inline 處＋ `skills/_common/illustrate-html-mode.md:79` | S3 四掛點 |
| rule pointer | `rules/context-management.md`「Memory 生命周期規範」 | S3 |
| Stop hook | `hooks/memory-index-regen.py:89-96`（`_regen-failed` 唯一消費者：returncode≠0 寫 marker、成功清除、恆 exit 0——與 S1 相容，review 已代掃） | S1 marker 語義 prose 同步 |
| 測試 | `tests/test_memory_lifecycle.py`（`test_generator_e2e_gate_fail_loud`:119、`test_generator_e2e_chars_gate`:159 現斷言「MEMORY.md 不存在」——**S1 需翻轉**；docstring L3-5 同步） | S1/S2 TDD |

SYSTEM-MAP：無（元專案，正當跳過）。

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | 對應 |
|---|------|------|---------|------|
| SM-1 | 池超限時 regen | chars>22,500 或行>190 | **MEMORY.md 照寫**＋exit 1＋行動訊息（merge or drop stale，可推導歸 repo） | S1 |
| SM-2 | 池超限時 `--check` | 同上 | **不寫入**（pseudo 需 `if not check_only` guard——超限 gate 在 check_only 分支之前，無 guard 照字面實作會寫）＋exit 1＋同訊息；**補 RED 測試**（既有 `test_generator_e2e_check_does_not_write` 是未超限 case，蓋不到此邊界） | S1 |
| SM-3 | desc 含 commit hash 寫入 | `commit [0-9a-f]{7,}` | hook exit 2 擋＋stderr 指引 | S2 |
| SM-4 | desc 含 hash 但 ≤100 chars | 同上 | 仍擋（內容契約獨立於長度） | S2 |
| SM-5 | 弧結案 | 結案兩步 | 同時機第三動：條目重寫終態 facts；無相關條目明示無 | S3 |
| SM-6 | 無 generator 的專案 | hook self-gating | 不攔（不變） | S2 |
| SM-7 | 清償＋線聚後 regen | S4 完成 | 水位 ≤20K chars／≤160 行＋_audit-state 記帳 | S4 |
| SM-8 | **subagent 寫 desc 含 hash** | mem-distill 等 | hook **不攔**（subagent 寫入不觸發——既有邊界明示）；補償＝委派 prompt 約束條款（S4-P1 已含） | S2/S4 |

## 段落 0 研究摘要（已完成——引用不重跑）

- **官方依據**（雙軸覆核屬實）：memory.md :351（skip derivable）、:401-403（超限 write 照成功＋error telling Claude to rewrite）、:397（edit-or-delete）、:458（/doctor 同刀）
- **池現況**：144 條（project 55／feedback 64／reference 23）；磁碟 MEMORY.md＝**152 行/22,664 chars 停滯版**（140 條；`_regen-failed` marker 在場——marker 內容＝最新拒寫嘗試 154 行/22,988，引用時區分兩值）；top-14＝~270K
- **結構事實**：行 gate 190−overhead 10→條目硬頂 ≈180；線聚數學覆核成立（101~104 ∈ 100-110）
- **可複用**：hook 既有 desc 長度檢查（S2 同點加內容檢查）；`_audit-state.md`；mem-distill agent；夜間收斂 cron
- **風險假設**：高——hook stderr 指引送達模型在 ZCode 未證（A3 deferred）→ S1 訊息同時落 stdout；**受眾矩陣**（review F5 結論）：手動跑 generator 的 session 直接收 stdout／夜間 cron automation-751ecce2＝寫手（訊息相容，gate 過才清 marker 不變）／Stop hook stdout 不進模型（索引新鮮度由 S1 保證，縮池壓力由夜間寫手與手動 session 承接）／週日審計禁改條目（只報）

## S1：generator gate 失敗模式改 CC 式（code）

**Context**：官方超限＝write 成功＋錯誤命令重寫；現況拒寫→停滯→召回斷裂（flash-forensic 條目實證）。
**依賴錨點**：`main()` 超限分支 → 定義 `generate_index.py:115-121`（超限 gate）＋`:122-127`（check_only 分支）；消費：夜間 cron regen 腿、`hooks/memory-index-regen.py:89-96`（marker）、週日稽核段 2 層 1、tests。
**要點**：

- 超限分支改：**`if not check_only:` 先走 tmp+replace 寫出**，再印 `[FAIL] gate 超限 N chars (限 22,500)——索引已寫出（不停滯）。當下 session 需縮：merge or drop stale 條目（可推導內容歸 repo/git——官方 skip-derivable），縮後重跑`＋exit 1 保留
- `--check` 超限＝**不寫**＋同訊息＋exit 1（SM-2）
- 檔頭註解 gate 說明同步（「fail-loud 不寫入」→「寫出＋fail-loud 行動訊息」；`--check` 仍不寫）
- **marker 語義 prose 同步**（review F4）：`memory-audit/SKILL.md:35`「regen 失敗待修」→「池超 gate 待縮（索引已寫、非停滯）」；`memory-index-regen.py:89` 註解同步
- **TDD**：①翻轉既有兩斷言（`not exists`→`exists`＋訊息斷言）＋tests docstring 同步；②新增 RED——超限 regen 三斷言（寫出+exit1+行動訊息）；③新增 RED——超限 `--check` 不寫＋exit1（既有 check 測試未超限，補邊界）

**驗證**：`uv run pytest tests/test_memory_lifecycle.py`；池副本覆蓋＋cmp 綠；暫存 fixture 池手跑 SM-1/SM-2。
**整合**：夜間 cron 相容（結構軸機械驗證：marker 唯一消費者 memory-index-regen.py L92-96，returncode≠0 寫 marker、成功清除、恆 exit 0）。

## S2：desc 內容契約——hook 第三檢查＋紀律條款（code＋prose）

**Context**：desc＝索引行＝召回觸發面；hash 屬 git 可推導。存量違規 3 檔（見 S4 清償腿）。
**依賴錨點**：`DESC_LIMIT` → 定義 `block-memory-index-write.py:38`／消費：同檔 entry 檢查函數＋`generate_index.py:29` TRUNCATE_DESC（cross-layer 錨 test_memory_lifecycle.py:456-458）。
**要點**：

- hook 加第三檢查（與長度檢查同函數同點，同 self-gating 界）：desc 匹配 `commit\s+[0-9a-f]{7,}` → exit 2＋stderr「desc 禁 commit hash——desc＝觸發詞＋一句鉤子；hash 屬 git log 可推導（官方 skip-derivable）」；**不檢 body**（歷史合法引用；body 已有 12K 膨脹治理）
- **regex 誤傷註記**（review F6）：字元集含純十進位（「commit 1234567」形態會誤擋）——實測池內 12 desc 含 "commit"、3 命中全真 hash、零誤傷；同長度檢查同界延拓（入口非單一：Bash redirect/subagent 不攔——既有邊界，SM-8 明示），不改 regex
- memory-audit「寫入端紀律」加內容契約：desc 三不（hash／日期流水／session id——皆 git/DB 可推導）
- **TDD**：SM-3（擋）、SM-4（短 desc 含 hash 仍擋）、body 含 hash 放行、**folded `>-` desc 含 hash 放行**（review F7——釘住「同界」承諾的反例測試）

**驗證**：pytest＋暫存池手動觸發。

## S3：結案即蒸餾＋寫入端載體判定（prose，docs mode）

**Context**：narrative 多 session 加段累積、結案時無人轉 facts；結案 session 最知道什麼是教訓。**掛點四處**（review F4：execution-plan:373 inline 重述兩步——照它跑的 session 會跳過蒸餾）。
**要點**：

- `skills/kanban-board/SKILL.md`「結案兩步」（源）：增第三動（同時機、隨弧）——「**弧結案蒸餾**：owning session 將本弧 project_/feedback_ 條目重寫為終態 facts（刪日期/session/進度流水與 git 可推導內容，留決策教訓與終態結論，敘事指向 repo 檔案）；無相關條目明示無」（規則引用 memory-audit，不重抄）
- `skills/execution-plan/SKILL.md:373` 收尾段：inline 兩步處改純 pointer 至 kanban（單一源）＋提第三動存在
- `skills/_common/illustrate-html-mode.md:79`：掃描確認是否需同步（inline 形態則同 pointer 化）
- `skills/memory-audit/SKILL.md`「寫入端紀律」：加對應條款（掛點指向 kanban）＋**寫入第五問**（user 裁定）：「這是每次都要的紀律→rule／on-demand 方法論→skill／跨 session 事實→memory——手冊形內容不住 memory」＋**承諾不進 memory**：承諾/待辦載體＝backlog 卡，memory 只收事實與教訓
- `rules/context-management.md`「Memory 生命周期規範」pointer 補「結案即蒸餾＋寫入第五問」

**驗證**：`rg "結案兩步" skills/ rules/` 全掃無漏掛點；`/consistency` 各檔；rules 變更後 `deploy_agents.py` 重跑＋gate 綠＋3/3。

## S4：一次性清償＋線聚（操作型——Phase 1 背景進行中）

**Context**：top-14＝~270K 弧 journal 群；線聚政策（總覽第 5 點）。
**要點**：

- **Phase 1（並行、清單內 in-place、禁跨檔合併）**：mem-distill×3 各 4-5 檔 → ≤8K/條（規則＝mem-distill 紀律＋desc 遵 S2 契約）；**批C 已完成**（4 檔 51.6K→20.5K，−60%）
- **Phase 1b（review F2 增補——存量 desc 清償）**：3 檔 desc-only 重寫（`project_air-13-unified-subagent-architecture`、`project-skill-invocation-discipline-rule`、`project_kbar-form-analysis-landing`——皆 <2KB，只改 desc 去 hash，body 不動）
- **Phase 2（P1 完＋定稿後，主 session 主持）**：語義同線 cluster merge——**慣例真相源＝`skills/memory-audit/SKILL.md` 層 3**（cluster ≥3 閾值、併入最大條目、merged_from 標記、刪檔前 rg backref 手術——review F1 修正：非 kanban）；候選線：code-reality 線／muse 線／流程治理線（開放清單，主持時定）
- 完成後 regen（S1 新語義）→ 水位 ≤20K chars／≤160 行；`_audit-state.md` 記帳

**Phase 1 清單**（14 檔三批；批A/B 跑中）：批A＝relay-claims 28.8K／agents-registry 28.2K／mcp-unification 23.3K／memory-lifecycle-governance 18.8K／gate-severity-queue 17.7K；批B＝archify-illustrate 17.5K／cr-mcp-cli-faces 17.1K／zcode-platform-facts 15.2K／muse-cli-facts 14.8K／session-topology 14.8K；批C＝pyrefly-producer／backlog-md-integration／own-graph-db／consistency-gate（✅完成）

**驗收**：每檔 ≤8K＋desc 合 S2 契約；水位 ≤20K；`flash-forensic-0905` 等新條目不在清單；merged_from 全保留。

**執行狀態（09-05 定稿後實作）**：Phase 1 ✅（批A −76%／批B −50.4%／批C −60%——14 檔 224,134→75,446 chars，全 ≤8,192＋desc 契約）＋P1b ✅（3 檔 desc 去 hash）。**勘誤（實測）**：Phase 1 蒸餾 body **不縮索引**——索引＝每條一行，尺寸由條目數驅動；regen 後 23,133 chars/155 行（行 ≤160 達標、chars ≤20K **未達**）。chars 水位目標依賴 **Phase 2 弧歸線**（55 project 條→12-15 線 ≈ −40 行 ≈ −6K chars → ~17K）。**Phase 2 ＝本弧剩餘步**，建議新 session 執行（合併手術含 merged_from＋[[backref]] 修復＋刪檔；本 session context 已深，語義手術宜新鮮 context）。

## 整合策略

- 依賴序：S1/S2/S3 獨立；S4-P1 獨立（進行中）、P1b 隨時、P2 依賴 P1 完＋本定稿
- baseline: `836c645`
- 部署連動：S1 改 skill 源→ai-rules 池副本覆蓋＋cmp；mosaic 池副本＝handoff 增補（附驗證：`for d in ~/.claude/projects/*/memory; do cmp <skill 源> "$d/_generate_index.py"; done`——零部署副本即標 N/A 收項）；S3 觸 rules→deploy_agents.py

## 收尾步驟

1. 卡 AIR-25 結案兩步（pre-commit、無 hash）＋本弧條目 `flash-forensic-0905` 已終態＝S3 首 dogfood 樣本
2. post-build：S1/S2 code 鏈（review＋pytest）；S3/S4 docs 鏈（consistency＋`rg "結案兩步"` 全掃）
3. 部署驗證：bundle 3/3 綠＋池副本 cmp 綠
4. 任務 brief 殼（基礎款）＋badge 隨進度

## EP Review 處置表（09-05 定稿——雙軸 15 findings）

| 軸 | # | 嚴重度 | 摘要 | 處置 |
|----|---|--------|------|------|
| 結 | F1 | P2 | S4-P2 引 kanban merge 慣例→實在 memory-audit:61-64 | ✅ S4 修正＋沿用 ≥3 閾值/併最大規則 |
| 正 | F1 | P1 | 存量 3 檔 desc hash 無清償路徑 | ✅ S4-P1b 增腿 |
| 正 | F2 | P1 | 超限寫出缺 `if not check_only` guard（--check 會寫） | ✅ S1 pseudo 明示＋SM-2 RED |
| 結/正 | F5/F3 | P2/P1 | 既有兩測試斷言 not-exists 需翻轉＋docstring | ✅ S1 TDD 三步 |
| 正 | F4 | P1 | 漏第四掛點（execution-plan:373 inline 兩步） | ✅ S3 四掛點＋rg 全掃驗證 |
| 正 | F5 | P2 | 錯誤訊息受眾鏈未閉合（Stop hook stdout 不進模型） | ✅ 受眾矩陣入段落 0；機制不變（stdout+exit1） |
| 結 | F3 | P2 | 缺 subagent 寫入場景 | ✅ SM-8 |
| 結 | F4 | P2 | marker 語義 prose 兩處 drift | ✅ S1 同步清單 |
| 正 | F6 | P2 | regex 誤傷面＋載體判準張力 | ✅ S2 註記（實測零誤傷，不改 regex） |
| 正 | F7 | P2 | folded 同界承諾無測試 | ✅ S2 補 folded 反例測試 |
| 正 | F8 | P2 | 條目硬頂 190→≈180；磁碟/marker 值未區分；線聚數學 ✓ | ✅ 總覽第 5 點改寫 |
| 正 | F9 | P2 | DESC_LIMIT 錨 :32→:38 | ✅ UC 表修正 |
| 結 | F2 | P2 | 同正 F1（3 檔存量） | ✅ 併 S4-P1b |
| 結 | F6 | P2 | mosaic 池副本本機不可驗 | ✅ handoff 附驗證命令＋N/A 收項 |
| user | — | — | 寫入第五問＋承諾不進 memory | ✅ S3 增補 |

**judge 自查（三防線②）**：全採納→否證抽查三件（--check guard 對源碼覆核屬實／3 檔存量雙 agent 收斂／regex 誤傷採「註記不改」而非過度修正）——通過。

**實作期 fresh-eyes review（09-05）**：5 findings 全 P2——①regex 邊界修 `\bcommit[s]?\s+[0-9a-fA-F]{7,}`＋docstring ②Edit 分支 hash 檢查補測試 ③regen hook marker 註解改雙因（池超限已寫出/frontmatter 違規未寫出）④hook docstring 四問→五問 ⑤generator 註解 scope 限定——** errs 路徑 CC 化（壞條目跳過照寫＋列名，現仍拒寫）列後議**：行為變更且動 marker 測試面（`test_regen_failure_marker_written_and_cleared` 用 frontmatter 違規觸發），待新 session 隨 Phase-2 一併評估。
