# scripts/ — 機件腳本（responsibility cluster 導航）

> 本目錄＝跨流程機件（watcher／installer wrap／receipt／probe），多數由 skill/workflow 在特定步驟調用。單檔導航、responsibility cluster 分組（**非 per-script AGENTS**——AIR-164 已決策③）。正規入口一律 `uv run python scripts/<name>.py --help`（bash 腳本 `<name>.sh --help`）；參數與語義真相源＝腳本自身 docstring，本檔只回答「哪個 cluster、幹什麼、何時用」。

## Clusters

- **WT lifecycle**：`wt-open.sh`／`wt-close.sh`／`wt-sweep.py`——persistent card WT 開（identity contract＋池/inbox symlink）、收（preflight→rebase→ff-only 吸收→移除）、孤兒 WT TTL sweep。何時用：kanban 開工 `wt-open`、收線 marshal `wt-close`（先 `--preflight` 全檢查）、夜間維護 `wt-sweep`（回收語義＝複用 wt-close，禁複製）。
- **bridge＋waiter＋liveness**：`bridge_waiter.py`／`harness_waiter.py`／`watcher_rearm.py`／`child_heartbeat.py`——bridge 派工 fan-in wait（124 內部消化、CollectionReceipt）、ZCode 子 agent timebox 監視＋收割、watcher 死亡辨識＋單次 auto-rearm、child 端心跳 sidecar。何時用：bridge dispatch⇄collection 配對（dispatch 後必配 wait）與長任務 liveness 接線——契約單一源＝[bridge-dispatch rule](../rules/bridge-dispatch.md)。
- **governance＋bootstrap**：`bootstrap.py`／`enroll_repo.py`／`deploy_agents.py`／`sync_agents.py`／`scan_skills_desc.py`／`governance_health_monitor.py`——新機器冪等全裝編排、repo 一命令收編 admission guard、rules bundle 部署、agents registry 生成、skills desc 契約機械掃、五面 governance health 排程。何時用：安裝動詞正典走 `uv run python governance/install.py`（見下方部署關係）；直接裸調僅限 installer 支援面之外的旗標需求。
- **checkpoint＋receipt**：`compact_checkpoint.py`／`segment_receipt.py`／`handoff_delivery.py`——compact 前交接 checkpoint 格式驗證＋restore-proven＋cleanup guard、EP 段落 receipt 機械欄生成＋freshness 鏈、handoff completion 分類＋直送組裝。何時用：`/compact-prep`（checkpoint）、implement 段落收斂（segment_receipt）、`/handoff`（delivery）；restore 注入面＝`hooks/compact-restore-inject.py`（hook 面，不在本目錄）。
- **scan＋probe**：`agent_liveness_sweep.py`／`skill_activation_probe.py`／`probe_entitlements.py`／`ping_matrix.py`（＋宿主在 skill 下的 [scan_project.py](../skills/scan-project/scripts/scan_project.py)）——bridge job liveness 唯讀 sweep、skill activation 機械觀察（instruction-testing protocol adapter）、model 額度探測管線、ZCode worker 五態×查詢面真機矩陣、專案知識快照。何時用：instruction-init Phase 1.5（scan_project）、autonomous liveness 檢查、model-routing availability 查證。
- **結算／稽核腿**：`decisions_pending.py`／`improvement_signals.py`／`arc_behavior_audit.py`／`reconcile_memory_pool.py`／`consolidation_preflight.py`／`projection_freshness.py`／`check_report_shells.py`／`lint_card_markers.py`／`gen_projection.py`／`at_ticket.py`——pending-decision 台帳、improvement 訊號機械掃描、弧結算審計（一行 JSON）、memory 池唯讀對帳、收斂波前置 tri-state preflight、投影 freshness gate、Report Shell 回源 lint、卡標記 lint、卡投影段生成、`/at` ticket 狀態機。何時用：post-build 收尾鏈（improvement 收斂／政策翻轉 gate 的 freshness check）、memory-audit consolidation（reconcile/preflight）、commit/metadata 結算的機械腿。

## 覆蓋邊界

- 本目錄腳本經 **Bash 呼叫執行，不在 hook 攔截面**（比照 [hooks/AGENTS.md](../hooks/AGENTS.md)「覆蓋邊界」寫法：admission guard 涵蓋 Edit/Write tool 呼叫，Bash redirect／腳本自身寫入不在其上——定位是提高違規成本＋留審計跡，禁宣稱完整 write security boundary）。腳本自身的寫入範圍由各自 docstring 聲明；調用方（skill/workflow）負責 scope fence。

## 部署關係

- **被 governance installer wrap**（呼叫封裝、輸出透傳、退出碼串接——[governance/README.md](../governance/README.md)）：`deploy_agents.py`（`--surface rules`）、`sync_agents.py`（`--surface agents`）——安裝正典入口＝installer，兩腳本裸調僅限 dev 除錯。
- **被 skill/workflow 鏈調用**（不經 installer）：上表其餘腳本——各自宿主 skill／rule 是唯一調用語義源，本檔不重抄參數。
