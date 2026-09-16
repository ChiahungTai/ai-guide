---
name: memory-cc-alignment-diagnosis-0905
description: memory 治理線終態——AIR-25 CC 對齊矯正（gate 先寫出＋desc hash 契約＋結案蒸餾＋寫入六問）＋三件套/symlink 拓撲/治理教訓
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

merged_from: memory-lifecycle-governance

### memory-lifecycle-governance

memory 治理線（mosaic 56.6KB 索引事故→三件套→memory-audit skill→共用池 symlink→AIR-25 CC 對齊，後者見 [[memory-cc-alignment-diagnosis-0905]] 段）終態。前身 project_memory-audit-skill-landing＋cross-harness-memory-symlink 已併入本條。機制真相源＝`skills/memory-audit/SKILL.md`＋`scripts/generate_index.py`＋`hooks/`（rollback doc＝`hooks/memory-hooks-rollback.md`）；波次流水查 EP `_done/` 與 git log，索引現值查 `--check`。

**三件套**：①generator（frontmatter 投影；雙單位 gate chars/bytes/lines；超限＝照寫出＋fail-loud 行動訊息——不停滯）②PreToolUse hook（擋手寫 MEMORY.md＋desc 長度/hash 契約＋body 膨脹）③Stop hook regen（`__file__`-relative byte 比對 ASSET_SOURCE 防植入；`_regen-failed` marker；手動跑 generator 成功不清 marker＝by-design）。

**memory-audit skill**：兩級稽核（full 四層／lite git log 增量）、反模式警示（索引整潔≠記憶健康）、狀態戳 `_audit-state.md`（獨立檔不入 frontmatter；base_commit 用 sha）、advisory→核可→執行三分離；寫入端紀律（寫入問＋desc 三不＋結案即蒸餾）的承載體。cluster-first 落 `rules/context-management.md`——「one file = one fact」的 fact＝主題教訓群（cluster）非單一事故；量化觸發歸 skill、兩層分治，否決專案 meta-memory。

**共用池 symlink 拓撲（平台事實）**：ai-rules 的 ZCode memory 指向 Claude 實體池，命名 `<目錄名>-<sha256(絕對路徑)[:16]>`；權威來源＝session system prompt 開頭的 memory 路徑（算出 hash 與 prompt 不一致以 prompt 為準——mosaic 踩過少 hash 後綴→一直讀空目錄）。方向＝ZCode 路徑→Claude path-encoded 實體目錄；載入時機＝session 啟動一次性（建/改 symlink 的 session 讀不到，須新 session）；per-project 隔離是 ZCode 原生機制（v3.6.4+、預設關）。mosaic 池單一實體、三 project dir 全 symlink 共指＝**同一 inode 三視圖**（非 symlink 鏈——readlink -f 各回自身、MEMORY.md 同 inode）；telemetry part 表記 ZCode 側路徑，LIKE pattern 用 Claude 側路徑會撈空。雙 harness 下 generator 固定 tmp 檔名 race 已修（`os.getpid()` unique tmp）。

**治理教訓**：
- subagent 寫入不觸發 PreToolUse hook（11.8K→39.7K/天實證）——subagent 寫 memory 唯一防線＝prompt 紀律（mem-distill 上限即此理；平台事實 [[multi-harness-architecture-direction]] hooks 段）
- 真實膨脹源在治理覆蓋外：活躍弧線逐段加段（單檔 98 Edit→84KB）；流入 ~700-1,000 chars/天 vs 舊餘裕 ~700＝「audit 完隔天又滿」——治理是減速非斷源（AIR-25 S4 線聚即對此的結構性收斂）
- 清理後餘量是健康指標：清到 <2%＝隔日半天正常流入即爆；收斂要有目標水位非「過 gate 即停」
- 蒸餾載體＝mem-distill agent（flash pin）——general-purpose 誤派 3.5 分鐘燒 16.5M input tokens 觸限流；多 agent 平行寫記憶時 gate 數字是移動目標，波收斂後統一 regen
- 外部 LLM 建議查證式採納：併檔建議實測推翻一半（「零損失」被 wc 證偽）——尺寸/緊迫宣稱與方案都要機械驗證後才採納
- 併檔判準：可併＝合計低於預算＋刪前 rg 零反引用＋merged_from 標記；不可併＝併後超預算（等知識退役再一次併）；共用 artifact 須輪次前綴（F-ID 命名空間碰撞會 join 出相反結論）
- gate 實戰價值：索引超限從靜默超載（mosaic 事故型）變 fail-loud，治理要防的迴圈在第一環被斷
- AIR-9 結案＝不建 near-dup 機械防護（prose 寫入問＋週期 audit cluster merge 已實證收斂；機械防護最大盲區＝subagent 寫入——勿重評，除非平台讓 subagent 寫入觸發 hook）
- ZCode hooks log 只記 `hook.run.failed`——驗 hook 是否 fire 靠副作用證據（mtime/md5/內容）；CC transcript 直讀 `~/.claude/projects/<encoded-dir>/<uuid>.jsonl`

### memory-cc-alignment-diagnosis-0905

AIR-25 主弧（前弧治理與平台事實見 memory-lifecycle-governance 節）。09-05 user 質問「寫法/distill 有問題」→ arch-thinking 診斷＋CC 官方文檔對照（鏡像 `ref-docs/harness/claude-code/docs/en/memory.md` auto-memory 段），兩假設皆成立。**寫法（根因）**：條目＝弧編年史（commit hash 入 desc、session id、日期流水）違反官方「skip anything derivable from codebase/git history」；narrative 由多 session「同主題加段」累積、無人在弧結案時轉 facts——flash-forensic 條目（結案一次寫成終態）是正確形態。**distill（放大器）**：gate FAIL＝拒寫→索引停滯→新條目不可見（召回斷裂比原病糟）；官方 over-limit＝write 照成功＋錯誤訊息含 merge/drop 行動。outflow 無排程、池貼頂震盪（日增>日清）。

**AIR-25 落地（user「全做！」；主體 commit 55d128a，41→91 測試綠）**：S1 generator 超限改先寫出再錯誤（exit 1 保留＋訊息含 merge/drop 行動指令；--check guard 釘住——三停滯條目當場回索引）／S2 hook 第三檢查 desc 禁 commit hash（`\bcommit[s]?\s+[0-9a-fA-F]{7,}`；後補 HASH_RE digit-lookahead `(?=[0-9a-fA-F]*[0-9])` 防「feedbac」恰 7 純字母 hex 偽陽性）／S3 結案即蒸餾五掛點（kanban 結案兩步第三動；kanban 源＋execution-plan/implement/metadata-sync/illustrate-html-mode 四消費端；rg 全掃勝 review）＋寫入第五問（載體判定）＋承諾不進 memory＋desc 三不／S4 top-14 清償 224K→75K（−66%）＋P1b 存量 desc 3 檔去 hash＋線聚。穩態目標 ~100-110 條／≤20K chars／≤160 行。

**Stop hook「不生效」根因＋`_regen-skipped-stale`（09-06 handoff 承接查證）**：「ZCode 端自動再生不生效」非未接線（config Stop 段實掛 regen hook）——池 generator 副本與資產源 bytes 不符時，byte 比對信任邊界跳過重生成且 stdout 不進 context＝靜默停滯；跳過路徑已補 marker（fail-visible，附刷新指引），副本相符成功 regen 自清。同批：generator 檔頭補部署操作說明（資產源/原子刷新）；「文件稱 l.py」名稱 drift 議題＝rg `-r` 顯示替換幻覺不成立（見 [[rg-r-flag-display-replacement]]）。

**「分 30 群」裁定（user 提案→修正採納）**：不採 30 mega 條目（平均 20K+ 爆 hook 12K、加劇同主題加段、desc 觸發詞蓋不住混合內容）、不採索引分節（行數本就是約束）、不採目錄分群（破壞 CC 扁平模型＋hook/generator 同目錄假設）；採「弧歸線」語義聚類——project 弧 journal 按線聚 12-15 條線條目（30 為上限非目標）、feedback/reference 保粒狀。條目數是結構天花板：兩端 200 行載入上限→~190 條硬頂。

**載體切分評估（rule↔skill↔memory 邊界）**：rule↔skill 分層與 hook 載體判準成熟；memory 邊界三缺口——①rule↔skill 語義引用同步靠自覺（三態×3/carve-out×2 drift 全靠手動 rg）②寫入問缺「該住哪層」判定（手冊形 reference 條目 14.8-17.1K 住 memory＝與 skills 雙真相源）③承諾與事實混居（「共識只在 memory＝斷鏈」實證）。修法：第五問＋承諾不進 memory 已併 S3 落地；手冊形條目歸宿待逐條裁（zcode-platform-facts/muse-cli-facts 已壓至 7-7.5K 事實集合形態）；語義引用同步機械化＝後續弧候選。

**AIR-27 errs 路徑 CC 化（DRAFT-1 後議同日落地）**：frontmatter 違規從拒寫改「壞條目跳過、合法條目照寫出＋exit 1 列名壞檔」（--check 對稱 guard）——原拒寫＝一個壞檔擋全部合法條目投影，與「拒寫＝召回斷裂」自相矛盾（fresh-eyes F1）；marker 語義統一「雙因皆已寫出」（超限＝全部條目、違規＝跳過壞條目）。

**P2 弧歸線＋全弧結案（commit 75d4221）**：fork session 派 mem-distill——agent 死於帳號級暫態（Model request failed，非任務錯）但死前完成 10 線合併；驗屍收編：半套偵測（宿主已寫入但成員檔在）→驗宿主吸收完整→刪成員＋regen。終態 11 線／條目 145→113／索引 18,205 chars gate PASS（餘量 163→4,295）、零懸空 backref。agent 教訓：重試帶已知事實（池形態/已完成項）省發現成本；UI「像在 loop」多半是分析期長讀取——判據看檔案系統副作用（.py/.md mtime）非 agent 狀態。lite-verify EP 驗證策略接線首跑 5/5 PASS。

**勘誤**：Phase-1 蒸餾 body 不縮索引——索引＝每條一行，尺寸由條目數驅動；chars 水位依賴弧歸線（body 蒸餾只還質量債）。

**MOS-36 反饋消化（user 拍板三項）**：①handoff `--comment` 是幽靈功能（AIR-14 設計時假設、CLI 實測不存在，懸兩日被 MOS session 實戰踩到）→六處改 `--append-notes`；教訓＝設計引用 CLI 功能面必先實測 flag 存在性。②寫入六問（五問＋新首問「任務終態 or 活知識」——弧歷程/session 流水/處理軌跡→卡不進 memory、活知識才進；分類判準先於 repo 可推導判準）＋蒸餾形態定案：刪 repo 已承載（宣稱須逐項附 rg 驗證路徑）＋軌跡記卡 final-summary＋不新建歸檔檔（MOS-36 實證 149K+37K+17K→5.1K，−96%）。③mem-distill 配方：>30K 肥條目派 agent 隔離消化（主 session 零 token）、backref/regen 留主 session、清單外禁碰。

**W605 handoff 判例**：docstring 內 regex 範例在非 raw 字串觸發 W605，存活三筆 commit——code commit 跳過 ruff 閘門（pre-commit hook 只跑 pytest 被當完整閘門）；修法＝模組 docstring 改 `r"""`。本 repo 閘門組合＝ruff＋pytest（mypy 環境未裝）；發現者是 AIR-26 並行 session 的 post-build lint 閘門——閘門跨 session 互咬是體系常態。

**D1 對時原則**：夜收斂 cron 報告標頭錯植「手動觸發」誤導 user＋AI 各一次——標頭時間用 `date '+%Y-%m-%d %H:%M'` 實際執行時間、禁自稱手動；log 標頭不可信時以 `_audit-state` 記帳／動作檔 mtime／log birthtime 機械對時（零產物≠沒跑；對時靠機械證據）。

**disposition 線**：marking 弧（149K monster）仍開（B2 refit gate 掛 pending-decisions）→建 DRAFT-12 草稿載體＋pending-decisions 指針掛 B2 結案條件正下方——觸發即 promote；mosaic generator 已同步 AIR-27 版（cmp MATCH）、B2 收案弧蒸餾 2 檔 −76%/−74%、git-commit-feedback desc「commit feedback」偽陽性已修。

**desc 夜修晝覆循環判定（09-07 arch-thinking 盤點）**：desc 三寫入路徑——主 session（PreToolUse hook DESC_LIMIT >100 硬擋）／subagent（繞 hook）／夜波掃尾（壓縮改寫 ≤100）。「夜修→晝覆」＝上游節流缺口＋下游兜底的預期收斂形態非治理失敗——弧收案蒸餾重寫 desc 時自終止；掃尾在索引逼近 gate 時是 load-bearing，不可因「重複修剪」停掉。上游寫入自律已三層在場（hook／寫入六問第五問 ≤100／mem-distill role＋夜波 cron 的 spawn 注入義務），殘餘缺口＝ad-hoc subagent 合規率——不另設機制（hook 單一入口判準對 subagent 不成立，勿重評）。待裁決：姿態句「活躍 owner 檔重複修剪＝預期、不升級處理」進 skill 夜間收斂段（lite audit 降噪用）。

相關：[[feedback_inflow-needs-outflow]]（本條只記門檻常數不記現值）、[[symlink-alias-before-two-entities]]（inode>readlink 增量）、[[flash-forensic-0905]]、[[commit-finalization-gate]]、[[memory-index-load-truncation]]、[[gate-severity-solidification-queue]]、[[feedback_inflow-needs-outflow]]、[[feedback_backup-unversioned-live-configs]]、[[reference_zcode-platform-facts]]、[[multi-harness-architecture-direction]]
