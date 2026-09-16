---
name: reference_code-reality-mcp-cli-faces
description: code-reality MCP×CLI 雙面——同 binary 同 graph.db、MCP-first 與 agent 地雷、build 傘形、freshness、免新 session
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_5ba3b97a-1c56-4d40-9c98-c5f209f68528
---

code-reality 雙面架構定案（2026-08 查證收斂）：

**核心：MCP 與 CLI 是同一 binary 讀同一份資料的兩個入口**
- MCP 工具 in-process 呼 `crate::cli::run`／`graph_engine::run`（mcp_server.rs header 自述 thin-wrap the SAME lib，drift 是 compile error）
- 資料一律 per-repo `<repo>/.code-reality/graph.db`，`repo_root` 是參數非拓撲（無 session/workspace 綁定）
- plugin `.mcp.json` stdio spawn `code-reality-mcp --stdio`；wrapper bootstrap＝`--version` 前綴比對 plugin pin→miss/stale 時 `uv tool install --force` 三 dist exact pin（`CODE_REALITY_BOOTSTRAP=off` dev 逃逸）→無 uv 時 loud 127＋指引。lsp-bridge wrapper 純 resolve＋bounded wait（不裝東西，防並發首裝互撞）。plugin 只擁有 skills 文件＋spawn config，零資料零索引
- **分發終態＝npm embedded face 已整拆、PyPI 單層**（npm 僅 darwin-arm64 一包撐不起＋鎖步負擔；registry 凍結 0.3.1 作廢）。release＝鎖步單段式（五版號面一顆 commit＋tag→CI PyPI×3）。「最新」＝release tag；dev 機 HEAD 永遠超前＝stale WARN by design

**覆蓋對照**：
- MCP（v0.6.0 起含資料面）＝查詢＋資料**全覆蓋**：scip_refs 家族＋graph_query 子面＋`get_community`（MCP 獨有）＋資料面 build/snapshot/delta_tour/project。工具數不記憶——`rg -c 'Self::.*_tool_attr' <CR repo>/crates/code-reality/src/mcp_server.rs`
- CLI-only：`snapshot`／`hub_refs`／`graph_db build`／`boundary*`／`runtime_edges`／`delta_tour`／`chain_tour`／`tour_*`×3／`sidecar_migrate`＋外部 producer（pyrefly-index、scip index ~8 分）——設計決策非缺口（plugin timeoutMs 60s 結構性排除長操作）；MCP 1MiB text cap 超載自建議轉 CLI face（`graph_query … | grep/jq`）

**路由（user T2-3 裁決：agents 都開 CR MCP 白名單、非必要不用 CLI）**：主 session MCP-first（現狀）。**agent 面 MCP-first 有三地雷**：①plugin face MCP 全名＝**連線中可注入可呼叫**（d32ddb0 推翻早期「不注入」中間結論——當時白名單只掛過萬用字元非全名）；②MCP 全名白名單在 server 未連線時整顆拒絕 spawn（claude/ 面須先驗 .mcp.json 接線在場）；③tools 萬用字元 `mcp__…__*` 靜默 no-op（spawn 正常但工具不掛）。CLI 形態（`scip_refs <sym> --repo <repo>`＋旗標）是 agent-safe fallback＋CLI-only 面唯一入口；外 harness（muse 等 bash 面 runtime、無 MCP 白名單）同樣經 PATH cargo face 直接消費 CLI（09-08 實證 binary 在 PATH）——muse 工單要符號查證時按需指名 CLI 即可，勿假設它無 CR。兩種 serve：stdio（harness spawn）＋HTTP 常駐 127.0.0.1:8200（launchd 共享）。詳 [[agents-registry-split-design]]（MCP 全名三態邊界）。

**本機 binary 權威（終態）**：PATH cargo-first 行在 `.zshenv:5`（全殼覆蓋，harness tool shell 也讀）→三殼 cargo face 權威；uv-pinned 五顆（`~/.local/bin/`）＝全路徑後門。**binary 查證一律當下殼 `command -v`＋`--version`，勿跨殼假定**；版本現值不記憶（歷史版本快照必過時——以實查為準）。

**新 repo build 鏈**：`code-reality build --repo <repo>` 一鍵傘形（v0.4.0 起主入口；`--producer rust|python` 顯式覆蓋；mixed repo 兩腿 cat-merge 單一雙語言 graph）。手動兩段＝除錯用（真相源 CR plugin skill）：Python＝pyrefly-index→scip_refs --stamp-meta→--build-cache→graph_db build；Rust＝repo-pin rust-analyzer 全路徑 scip（~8 分、**傳目錄非 Cargo.toml**——後者 exit 0 空輸出，傘形有空索引守衛）→graph_db build。`.code-reality.toml` 可選（無 profile fallback：top-level dirs 為模組／exclude 只 `.venv/`／claims 恆 NONE）。**refs/callers/closure 只需 scip index 不需 graph.db**（graph.db 是 audit＋graph_query 家族需求）；smoke＝`snapshot --label smoke`。

**生命週期**：plugin 從不寫 repo——uninstall/reinstall 不動 per-repo `.code-reality/`（唯一重建觸發＝schema/版本過期守衛，loud＋derived cache 自動重建）。deferred-install 設計：wrapper resolver 找不到 binary→`uv tool install code-reality==<plugin 版>` 後 exec＝「plugin 裝好→下一 session 自動五顆到齊」（**exact pin 非 latest**——plugin 版驅動工具版、零觸網、無 supply-chain 漂移）；uv-first 禁 pip 自動 fallback（PEP 668 externally-managed）。

**refs/index 新鮮度語義**：refs 族回傳行號＝index 生成時快照——**引用行號前 rg 源檔核對**（[[line-anchors-rg-before-handoff]]）。兩 WARN：①「僅 N 文檔可能截斷」＝`documents<100` 啟發式，小 repo 全量重建仍響＝永存噪音非真截斷；②「meta 未 stamp」＝HEAD 已離開 index 生成點的守衛（stamp 後 stale 自動報警；producer 落後版無此旗標→先重建 producer）。stale index 對新檔符號回「查無 DEF」假陰性——先 reindex 再下結論。

**regen/heal 語義（09-06 dry run 實測）**：stale-guard 重生成＝**同步 per-query**——查詢就地重生成、失敗 fail-loud（panic exit 101＋「以現存索引作答」），無背景重建在跑、不存在「查太早／等它跑完」的時序問題（user「太早查詢？」challenge 已用 stamp 相符複測否證）。**v0.6.4（f75b86a，2026-09-06）修復 AIR-33 三缺口（owning 側 L4 驗收）**：①Python **class DEF 可查**（ConditionBase 15 callers/22 sites、CLI＝MCP 同結果；修前 b30af73 只文檔化「class 名非可查 key」限制）；②CJK char-boundary panic 修（emit TOCTOU）；③heal churn 冷卻——stamp 相符重複查詢 0.08–0.11s 零 heal，且**索引缺場改快速 `[FAIL] 預設索引不在` fail-loud**（不再靜默百秒重建；`refresh` 只對既有 index 做過期更新、不從缺場建）。手動全量重建＝`pyrefly-index --repo <root>`（mosaic 實測 ~85-100s）後**必須補 `scip_refs --repo <root> --stamp-meta`**——直接生成不 stamp＝`[SRC]` 缺 index 版本 WARN。`<repo>/.code-reality/refresh.log`＝watcher 日誌：歷史 panic 行判修前修後＝log 行時間 vs binary 安裝時間（修前 panic 全在舊址 emit.rs:171）。stamp-meta 旗標掛 `scip_refs`、與查詢互斥須單獨跑。v0.6.1 起 runtime stale WARN＝**dev-face gated**（僅 `$CARGO_HOME/bin` 執行檔 WARN；uv pin 面/plugin pin 靜默——plugin pin＝唯一版本權威）＋**crates-relevant**（docs-only commit 不跳；git 無法解析 rev 保守 WARN）。project 工具輸出小不一致：WIRED 行只印文字無 `[WIRED]` 前綴（MISSING/HOLE 有 bracket tag）——機械解析 verdict tag 會漏抓 WIRED。**plan.toml schema 四輪踩坑點（08-30 dogfood＋09-05 重測實證——`--help` 不含 schema，範例在 CR repo `crates/pyrefly-producer/tests/overlay_gen.rs`）**：①`[meta]` 區塊必需（name〔僅 A-Za-z0-9_-〕/project/version/graph_rev）②`[[claims]]` 每條必帶 `to_kind`（缺字串欄位即 fail）③`[[edges]]` 的 `needle` 必須含 callee 名且其所在行經 py_calls 驗證是真 call site（宣告與程式碼不符＝一致性 gate fail）——fail-loud 會逐步指引但三輪才通，首次寫 plan 先抄測試範例形狀。④**identity join 鍵 gotcha（WIRED 縫根因，09-05 CR 端已修 fail-loud）**：`[meta]` 的 project/version 必須**等於目標 repo 的 pyproject identity**——symbol ID 內嵌此前綴，不符＝鑄造成功（minted_edges>0）但查詢面零歸因＋claims 誤判 HOLE（靜默，08-30 實證）；現版本 identity 不符直接擋並說明。三態輸出契約：`[projected][MISSING]`（宣稱符號不存在）／`[projected][HOLE]`（有 DEF 零呼叫邊＝未驗證假設非 bug）／`[projected][WIRED]`（已接線）——接線消費點＝execution-plan 段落 0（EP 作者填 plan）＋ep-review F3（判讀）。

相關：[[project_cr-live-faces-roadmap]]（分發軸；兩面對照表真相源＝CR plugin skill）、[[cr-live-faces-roadmap]]（資料面所有權＋生產鏈）、[[agents-registry-split-design]]（agent MCP 全名限制）
