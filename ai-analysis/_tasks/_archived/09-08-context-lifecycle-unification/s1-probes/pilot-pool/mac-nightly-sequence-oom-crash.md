---
name: mac-nightly-sequence-oom-crash
description: Mac watchdog panic 根因＝nightly pytest 記憶體常態＋隔夜 session＋swap ENOSPC；修法＝分批跑＋收工結算
metadata:
  node_type: memory
  type: project
  originSessionId: sess_301776bf-83a9-4276-be6e-13a10e01dacc
---

2026-08-15 凌晨 Mac（MacBookPro18,2 M1 Max、32GB、macOS 26.5.2）04:16 強制重開機事件，三輪診斷定案（第三輪 8.59GB 寫入歸因 + git log 翻出隱藏共犯）：

- **根因鏈（最終版）**：nightly op2 test-regression 的 pytest（Polars pipeline 寫 parquet，footprint 879MB→10.1GB）+ **EP session（ep-structure-naming-refactor）隔夜未關**（03:52–03:55 連續 commit S3c/S3d/S3e/S4、04:12:56 crash 前 4 分鐘還在 EP 收尾 commit，自己的 python 5GB+2.2GB）+ 常駐 Parallels/OrbStack/VS Code/Chrome → 記憶體壓力 → 系統狂開 **80 個 swapfile（~160GB）把磁碟吃滿** → pytest 跑到 6% 遇 `No space left on device (os error 28)` 後 hang（tqdm 卡死 + faulthandler Timeout）→ swap 開不了新的 + compressor 100% → 全機 thrashing → kernel `watchdog timeout`（watchdogd 90 秒無 check-in）→ panic 重開（04:17:27 boot）。**直接死因是磁碟滿（ENOSPC）非單純 OOM**。
- **45 天未重開 = 放大器**（`last reboot`：7/1 09:42 boot → 8/15 04:17 crash；diag Time Since Boot 3,866,721s≈44.7 天）。swap 檔在 `/System/Volumes/VM/swapfileN`、每個 1GB 起跳、按壓力開新檔、**上限=磁碟剩餘空間、只有重開機才整批清**；持續壓力下只增不減。磁碟基準 ~750GB used/926GB（剩 ~176GB）→ 80 個 swapfile 剛好吃光。crash 後兩小時即 live 重演：一隻 `pytest tests/unit_tests -q` 跑 17.5 分鐘吃到 16GB，把 swap 從 0.9GB 推到 11.2GB（12 個 swapfile）、磁碟可用 151→128GB——機制常態存在，夜間疊加才爆。
- **時間線 anchor**：op1 daily-maintain agent 03:26–03:46（commit `032c3fab` 落 03:46:34）→ op2 pytest ~03:47 啟動（SJ 連線 03:48:23）→ 04:12:44 jetsam → 04:16:46 panic。jetsam 三隻 python = nightly pytest 10.2GB + EP session 兩隻 5GB/2.2GB（第三輪修正：10.2GB 是 pytest 非op1 agent——op1 已於 03:46 結束）。
- **8.59GB 寫入歸因（第三輪翻案）**：diag microstackshot 的 Rust thread 棧直指 `polars_parquet::write::column_chunk`（parquet writer）+ 主 thread 99.6% 在 write()。8.59GB 是「file-backed memory dirtied」**24h 滾動窗口計量**（限額動態：8/12=24.86KB/s≈2.15GB、8/15=99.42KB/s≈8.59GB，每機/時期不同），非單一檔案——crash 後各目錄找不到對應大檔是正常的（髒頁未落盤即丟失 + parquet 中間產物分散）。別把「寫了 8.6GB」誤讀成「有個 8.6GB 檔案」。
- **df 陷阱**：重開機後 swapfile 全清 → 事後 `df` 顯示 151GB free「看起來正常」——crash 級 ENOSPC 事件若涉及 swap，不能以事後 df 判斷當時磁碟狀態。
- **tdcc-backfill 02:00 ModuleNotFoundError（`features.box_context_feature`）= transient**：EP session rename mid-flight 中間態（檔案已 git mv、registry.py 未改），05:48 launchd 補跑已自癒（exit=0）——與 crash 無關，但它是「EP session 半夜活躍」的 witness。排程任務直接跑 live working tree，in-flight EP 改到一半就會撞（同風險：op1 agent 險些 commit 混入 EP staged renames）。
- **nightly log 位置**：主 log `~/.mosaic/logs/ops/nightly-sequence-YYYYMMDD.log`（正常 ~140-150KB；crash 夜只 16KB 死在 op2 6%）；LaunchAgent stdout/err `launchagent-nightly-sequence*.log`（只有 readiness 行，別誤以為是主 log）。
- **pytest 10-16GB 裁決（第四輪查畢）：結構性常態非 bug**。量級帶：8/12 正常完跑的 nightly python 也 7.2GB（diag 歷史對比）→ 8/15 全量 10.1GB → 當日 unit_tests 16GB，同一行為。成因：① xdist 在依賴但 nightly 未啟用 → 單進程累積、module import 永駐；② nautilus_trader 測試基礎設施（unit_tests/conftest 的 msgbus/Cache/sj_client fixtures、tests/conftest 用 nautilus test_kit 的 TestDataProvider）；③ session-scoped `audusd_quote_ticks` 載真實 tick CSV 全程駐留；④ polars parquet 讀寫散佈多測試模組。`--timeout=300` = pytest-timeout（nightly log 的 thread dump 是其 faulthandler 機制正常作動）。**最有效解法 = 分批跑**（按目錄逐批 subprocess，每批結束釋放全部記憶體）；xdist 不一定划算（多進程各載 nautilus 基礎）。
- **修法裁決（用戶拍板，2026-08-15）**：① 磁碟 gate —— 用戶明確否決「不用啦」；③ pytest ENOSPC fail-fast —— 撤回（前提「pytest hang 是異常」不成立，它是正常工作量被拖垮）；⑤ pytest footprint 查證 —— 已查畢（上方裁決）。**仍有效的只有**：④ 收工時結算/暫停互動 session（EP session 隔夜與 nightly 平行搶資源是本次隱藏共犯）+ pytest 分批跑 + 考慮定期重開讓 swap/compressor 歸零。若用戶再報「半夜重開機」，先查 nightly log 是否又死 op2 + `ls /System/Volumes/VM/` 看 swapfile 數量 + 磁碟可用空間（[[feedback_ep-rename-needs-fullrepo-grep]] 原則：查實際狀態非宣稱）。
- **診斷路徑（可重用）**：`ls -lt /Library/Logs/DiagnosticReports/`（panic-full-*.panic 的 `panicString` + `Compressor Info` 行；JetsamEvent-*.ips 的 `largestProcess` + `processes` 按 rpages 排序；*.diag 的 `Resource Coalition` 指認排程來源 + 「Heaviest stack」/binary images 的 Rust 棧可辨認 Polars/tqdm 等行為）→ `pmset -g log` 電源時間軸 → `sysctl kern.boottime` 對時 → 排程任務 ops log 找 ENOSPC/hang 斷點 → **git log commit 時間戳重建誰在半夜活動**（翻出 EP session 隔夜未關的關鍵）。

- **修復落地（2026-08-15/16，main 分支；研究收案，取代「已 handoff 研究中」狀態）**：兩層手法。① `df30538c` nightly pytest **按目錄分批 subprocess**（~69 批、每批新進程結束即釋放記憶體；`deploy/scripts/run-nightly-sequence-inner.sh:196-217`；配套 `tools/merge_junitxml.py` junit 逐批合併 + collect-only 覆蓋 guard（合併數≠收集數即 FAIL，防新目錄漏批）+ 每批 `/usr/bin/time -l` 峰值 RSS 落檔）；② `f4989396` DatasetGenerator `data_window` 加性參數貫通 generator→WorkerConfig→worker，四支 8-10GB 怪獸 integration 測試降為 607-792MB（10-16×，三層 cache 防護）+ `e963967e` data_pipeline/features 測試 37 年全史收為 5 年窗。**驗證**：8/16 nightly 全量跑完（69 批、merge/覆蓋 guard 過，僅 SJ 非交易時段假值一支失敗，翌晨 `5fba9015` 修）。**殘留**：現存最大單批 = batch 50（`tests/unit_tests/datasets/test_*.py`）**7.86GB**——不在原已知限制清單，下一個怪獸候選。op2 worktree 已除名，nightly 改自 main worktree 執行。

相關：[[ai-rules-dual-role-mosaic-shared]]（nightly 屬 mosaic 消費端）、[[feedback_ep-rename-needs-fullrepo-grep]]（nightly real-data scan 是既有 observation loop）。
