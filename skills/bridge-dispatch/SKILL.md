---
name: bridge-dispatch
description: "delegate-bridge 委派深層載體 — codex web pool（webgpt）大內容紀律（turn body 計算含整個 turn、session 歷史計入；雙軸預算——材料軸 inline 線／整包軸 composer 整包線——與 fat-AGENTS 替代路由；失敗勿原樣重派——carrier 自動重試同 payload 放大限流；觀測值與失敗態分流）與 dispatch⇄collection 完整模式（背景 detach 完成不通知、waiter exit 即通知；單顆短工前景 shell vs N 顆平行 --background＋fan-in wait 場景；wait exit 124 re-arm 禁重派；--stuck-after family 起跳值；重啟後恢復 playbook——runs 禁盲重派、show --json 收完成、重掛 wait；綠 runs 不證健康）。always-on 核心（registry pin 唯一源＋禁手拼 pin／禁第二 pin、glm provision 前置、waiter 收法配對、長輸出檔案承載）在 rules/bridge-dispatch.md；caller surface 完整對照表、glm resume model-match 契約、Brief 動詞紀律在本檔（0924 bundle 瘦身自 rules 收編）；跨 repo 呼叫 delegate-bridge、派工後收結果、背景 job 卡死或 app 重啟後恢復時載入。觸發詞：delegate-bridge、task --background、wait、fan-in、webgpt、codex web pool、chatgpt-web、stuck-after、runner id、re-arm、exit 124、prune、pin resolver、installed_plugins.json、caller surface、dispatch collection、派工回收、bridge_waiter、CollectionReceipt、stalled-advisory、雙軸預算、材料軸、整包軸、fat-AGENTS。"
---

# bridge-dispatch — delegate-bridge 委派深層

> 本 skill 是 `rules/bridge-dispatch.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（registry pin 唯一真相源＋禁手拼 pin／禁第二 pin、glm provision 前置、waiter 收法配對、長輸出檔案承載）；本檔承載 caller surface 完整對照表、glm resume model-match 契約、Brief 動詞紀律、webgpt 大內容段與 dispatch⇄collection 完整模式（0924 自 rules 收編——bundle 瘦身，知識不滅）。事故脈絡與權威細節在 delegate-bridge repo（各節附路徑）。

手拼版本化 cache 路徑事故（rule 端禁手拼的 why）：反覆 GLM 派工摸到 stale 舊版 binary，`Model creation failed` 連敗且被誤分類為額度問題，診斷燒掉一輪——修好的新版就在同一個 cache。「第二 pin」的常見形態另有 `ls | sort -V | tail` 猜最大版。

## Caller surface → 合法入口對照表（registry pin 唯一源的唯一展開；0924 自 rules 收編）

| Caller surface | 合法路徑 |
|---|---|
| ZCode／Claude Code plugin surface | `${CLAUDE_PLUGIN_ROOT}/bin/delegate-bridge`——harness 自動注入並解析 pin |
| Codex plugin context（delegate-codex skill） | `${PLUGIN_ROOT}/bin/delegate-bridge`（`CLAUDE_PLUGIN_ROOT` 僅 alias）；任務必帶 `--caller-harness codex` |
| ZCode／Claude Code bare shell | 讀 `~/.zcode/cli/plugins/installed_plugins.json`（Claude Code 同名檔）取 `installPath` 拼 `bin/delegate-bridge` |
| Codex bare shell | **無 pin resolver**——禁猜 cache 路徑；走 plugin surface 或 repo checkout |
| Muse session | plugin-less caller kit（delegate-bridge repo `docs/muse-caller-kit.md`） |
| 任何 harness 的 repo checkout | dev binary `rust/target/release/delegate-bridge` |
| MCP face（plugin `.mcp.json`，ZCode/CC 安裝即註冊） | 九個 `bridge_*` tools 原生呼叫；`bridge_task` 恆 --background→bridge_wait（2.2.0+；codex 端不走此面——走 db-52 wiring） |

禁手拼版本化 cache 絕對路徑（`.../delegate/<version>/bin/...`）、禁造第二 pin——第二真相源必漂移；殘留靠 prune 清，stale 恆大聲失敗。

## MCP face 接線與 MCP tool dispatch（2.2.0+，DB-40 Stage 2／db-52＋db-53）

兩種合法接線，按 harness 分流：
- ZCode／Claude Code：plugin 樹自帶 `.mcp.json`（`delegate-bridge` → `${CLAUDE_PLUGIN_ROOT}/bin/<arch>/delegate-bridge mcp`）——安裝即註冊九個 `bridge_*` tools（plugin 安裝＝pin transition，免 rot）。已實證：CC canary server 連線＋9 tools；ZCode process 層 spawn（app 重啟即載入）。限制：command 綁 arch（aarch64 先行）；ZCode MCP 面變數展開 mirror-silent（hooks 面已實證注入）——fresh session tools/list probe 為驗收手段。
- codex：無 plugin MCP 聲明機制 → `scripts/codex-mcp-wiring.mjs` apply/verify/doctor/remove 將 stanza 接進 `~/.codex/config.toml`（surgical 手術保留他 section byte-for-byte＋時間戳備份＋原子寫入）。config.toml 易腐：codex 整檔重寫＋launcher 更新拆自訂段——每次 codex 更新後重跑 apply＋doctor。`--args` 後至 bare `--` 或 argv 結束屬 server args；吞到 wiring-flag token（--config/--command/--binary）＝exit 2 fail-loud。

MCP tool dispatch 紀律（與 CLI dispatch 同構、入口不同）：
- `bridge_task` 恆 `--background`：呼叫即得 receipt（jobId＋status）→ `bridge_wait` 回收 → `bridge_show`/`bridge_save_result` 收尾。
- codex-web known false-negative（upstream #674，DB-51）：terminal row 帶 `knownFalseNegative` extra（web transport＋disconnect 簽名）＝回應可能已完整渲染在 ChatGPT tab——**先查 tab／worktree 產物再論重派**（re-dispatch trap：ledger 記 failed、工作已完成）。muse/glm/native-codex 不受影響。

錨點：delegate-bridge `docs/ep.md`（MCP face 節頭 known false-negative 條款、`plugin MCP declaration (DB-53)` 節、`codex config.toml wiring tool (DB-40 Stage 2)` 節）；`plugins/delegate/.mcp.json`；`.agent-tmp/REPORT-DB47.md`（sandbox 盤點——MCP 消費端的 sandbox 情報）。

## codex web pool（webgpt）大內容

ChatGPT web edge 拒絕過大 turn body，計算含**整個 turn**（session 歷史計入；resume 中型舊 session 也會超標）；失敗**勿原樣重派**——carrier 會自動重試同一 payload，放大限流。精確觀測值與失敗態分流 → delegate-bridge repo `AGENTS.md`「Caller dispatch discipline」節。

派工前過**雙軸預算**（兩軸量的是相反兩端——材料端 vs 整包端，禁互抵、禁共用「上限／安全線」一詞；預算值行在 `rules/bridge-dispatch.md`）：

- **材料軸**（量待審材料）：待審材料內聯 prompt ≤8KB 實測安全——webgpt agent 讀不到 caller 本地檔，工單只帶 repo 檔案路徑＝未驗形態（agent 無從審起，09-16 實證）。超標 → chunk／改形態。
- **整包軸**（量 composer 整包＝工單＋repo AGENTS.md 鏈＋全域 `~/.codex/AGENTS.md` ~30K＋envelope buffer ~20K）：須 <100K chars——死亡線 ~100K–126K 實測收斂（as-of 2026-09，codex CLI 0.155.0-alpha.16），工單小 ≠ payload 小。超標 → fat-AGENTS 替代路由。

**fat-AGENTS 替代**：判準以估算式為準、不以 repo AGENTS.md 單一數字為準（教訓正在於工單小＋fat AGENTS 才爆）——repo AGENTS.md ≳50K 即進估算參考錨（dispatch 前 `wc -c AGENTS.md` 為低成本可選機械檢查；實例：62K AGENTS.md＋3KB 工單已死）。順序＝①降 payload（改 repo 檔案路徑交付〔材料軸未驗形態，採用前先驗 agent 可達〕／減 inline／用既有 artifact）→②native codex（credits 訂閱池——帳號路徑分界與額度現值依 model-routing）→③muse／glm（依 model-routing resolver）→④in-harness。

**觀察項**（單次實測值不升格永久規格）：
- CLI 注入量 drift：估算式的全域 instructions 與 envelope 兩項綁當前 CLI 版本，升級即過時——條文只認 as-of 標記，精確觀測值留 delegate-bridge AGENTS.md。
- envelope buffer 漂移：buffer 佔比隨版本增加，估算式逐項須定期對照。
- 回應段死亡（09-16 `displayed an error` 形態，分流表見 model-routing webgpt 節）×整包預算交互未對照實證——下次回應段死時記整包估算值回填死亡線 bracket。

## Dispatch⇄collection 配對（派工必配回收）——完整模式

delegated job 完成時**不會通知任何人**——`task --background` detach 是設計（setsid 背景工人生存過 app 重啟），代價＝完成無人觸發；root cause 是 caller 紀律缺口（派了沒安排回收），**waiter exit 就是通知**。單顆短工＝前景 `task` 丟 harness 背景 shell（shell exit＝完成通知；app 重啟即死，僅廉價輪可受）；N 顆平行／長工（muse 6–15+ min）／須活過重啟＝各 `--background`＋**派工同 step 自動 arm watcher**——開**一顆**背景 shell 跑 `uv run python scripts/bridge_waiter.py <jobId...> [--kind discussion|implementation|research] [--sink jobId:PATH] [--anchor jobId:TOKEN]`（watcher 內部包 fan-in `wait`：正常長跑期間零喚醒、exit 124 恆內部消化 re-arm 永不外洩；全 terminal 才叫醒並 stdout 尾行輸出 CollectionReceipt JSON——exit 0＝全 terminal completed 且 delivery 過（manual-anchor 視同過）、exit 1＝任一 terminal 非 completed，或 completed 但 sink 三步驗收不過（兩者皆出 receipt）、exit 2＝fail-loud（reconcile＝ledger 重生／重派跡象——**禁 retry 禁重派**；error、usage 透傳）、exit 3＝stalled-advisory 只喚醒不處置——偵測與處置分離，stop／重派決策恆歸主 session）。手動 fan-in `wait` 全部 id 降為 fallback：script 不可用時的替代（`wait` exit 124＝timeout 到仍在跑→**re-arm 非失敗**、禁重派——detached worker 仍在燒額度）與 app 重啟後手動恢復路徑——**重啟後對 running id 重新 arm watcher（同主路徑）；playbook＝script 不可用時的手動替代**（playbook 見下指針）；`--stuck-after` 起跳值按 family scale；`--sink`／`--anchor` 可重複（N 顆多 sink 常態）。push／daemon＝out-of-scope（forwarder 紀律）。

完整模式（場景表＋sh 範例＋family 起跳值＋重啟後恢復 playbook：先 `runs` 禁盲重派、`show <id> --json` 收完成、running 重掛 `wait <id> --stuck-after`——綠 runs 不證健康）→ delegate-bridge repo `plugins/delegate/skills/delegate-run-output/SKILL.md`「Dispatch ⇄ collection discipline」節。**terminal ≠ complete**：有 sink 登記者以 artifact 機驗（存在＋非空＋錨點）為完成，無登記者以 bounded receipt 非空為完成（0924 自 rules 收編；驗收程序見上段 sink 三步驗收）。

watcher 節（本 repo）：自動 arm 規約與場景分工見上「Dispatch⇄collection 配對——完整模式」段；watcher 狀態機 frozen spec T1-T9、exit 契約、動態 T 公式（T0=clamp(P50/3, 5m, 15m)、fresh progress T×1.5 cap 20m）單一源＝`scripts/bridge_waiter.py` module docstring（變更走卡 amendment）；bare shell 呼叫 watcher 須帶 `DELEGATE_BRIDGE_BIN=<bridge 絕對路徑>`（watcher 預設只查 PATH，找不到即 clean fail-loud exit 2 附修法——路徑由 installed_plugins.json registry pin 解析，見本檔上方 caller surface 對照表；0921 dogfood 實證）；雙軸 stalled 判準已對齊 bridge producer canonical（task.rs 單一實作「no ageable data is never reported」——0921 codex 腿 drift finding 修復）；**codex web 長生成期 heartbeat 滯後→worker 軸 5m floor 常態性誤報**（0921 高強度研究工單實證×3，job 本體活躍）——研究類派工帶 `--kind research` 抬 runtime floor 並容忍 advisory；watcher 增量定位＝124 透明 re-arm＋advisory wake＋CollectionReceipt 機驗（native wait 已原生支援 N-job batch fan-in 與雙軸 stuck 觀察——勿重複實作，長期 liveness 語義下沉回 producer）；0921 消費同步已落地：bridge ≥2.0.23 時 watcher arm 帶 `--wake-on-stuck --wake-axis runtime`，exit 3 wake JSON 轉譯為現行 stalled-advisory（自算雙軸輪詢退役；124 re-arm／terminal collect／exit 2 分流保留）——選 runtime 軸不選 worker，因 codex web 長生成期 heartbeat 滯後誤報×3（前述），選軸即把誤報消化在 producer；<2.0.23 維持自算雙軸（版本閘控雙模，MIN pin 不變 2.0.22——ZCode pin 翻轉後自動走 native）；CollectionReceipt 欄位集權威＝AIR-135.7 AC#2 bounded receipt（watcher 側投影定義在 bridge_waiter.py docstring，非新 schema；AIR-149 EP＝bridge／harness 兄弟契約同源文件；sink 三步驗收程序單一源＝delegate-run-output「Receipt acceptance」節，本檔引用不自創）；workflow 層配套（bounded slices／checkpoint 續寫）單一源＝AIR-135.7 契約。

## Canonical dispatch runbook（glm writer lane）

> glm writer（implementation）派發的全命令模板鏈——把 bridge-dispatch 紀律收斂成單一序列；條文語義單一源：always-on 核心在 rule 端，caller surface 對照表與 resume model-match 契約在本檔（0924 收編；步驟 1/5 引用）。

1. **registry pin 解析**：plugin surface 用 `${CLAUDE_PLUGIN_ROOT}/bin/delegate-bridge`；bare shell 讀 `~/.zcode/cli/plugins/installed_plugins.json` 取 `installPath` 拼 `bin/delegate-bridge`——禁手拼版本化 cache 路徑（第二 pin，見本檔上方 caller surface 對照表）
2. **provision 前置**：workspace 首次 glm 委派前 `delegate-bridge provision --family glm`（**唯一 sanctioned config write**；0924 自 rules 收編）；spawn verify-only（缺漏／drift＝fail-loud 附指引，不自動補）
3. **派發**：`delegate-bridge task --family glm --write-mode edit --yolo --wt --card <card-id> --background`——**`--wt` 是布林旗標、不帶值；`--card <card-id>` 帶值**；**禁 `--steps`**（glm carrier 不支援（validate_flags fail-loud）；此為 muse 旗標勿搬入 glm 配方）；prompt 大材料寫 repo 檔案只派路徑（長輸出任務形狀條，family 通用）
4. **watcher 配對（cwd＝job workspace）**：派工同 step arm `uv run python <ai-guide repo>/scripts/bridge_waiter.py <jobId>`——**waiter 的 cwd 必須＝job 的 workspace**：job ledger 是 per-workspace（`<ws>/.delegate-bridge/`），cwd 錯位＝查無 job（not-found 誤入 reconcile 分支）
5. **定向 resume（glm resume model-match 契約；0924 自 rules 收編，條文單一源＝本步驟）**：接續必帶**建立時** `--model <id>`（不帶＝落 manifest `defaultModel`；ledger row 有記；不符＝carrier `Select a model` fail-closed）；`--resume` 是布林、指定 session 走 `--session-id`。定義源＝delegate-bridge repo `AGENTS.md`「Build loop」glm provisioning 段＋`docs/ep.md` S1（僅指針）

## 下沉細節（自 rules 精煉遷入——on-demand 參考）

- provision 機制細節：user-invoked；stage per-model read-only configs＋sha256 manifest。glm 建立 job 的 model 記在 ledger row（resume 對帳用）；fail-closed 錯誤附 actionable hint。
- 第二 pin 形態例：stable symlink、「latest」 shim——殘留靠 prune 清。
- **Brief 動詞紀律（可寫 carrier；0924 自 rules 收編）**：brief 的動詞決定可寫 carrier 的行為——審查／調查／盤點類 brief 必帶顯式 `READ-ONLY / no writes / no git`（work-order 模板 review/advisory variant，§6 動＝零），實作類 brief 必帶 scope fence（格式＝work-order 模板範圍限定節）＋禁 commit（commit 恆為主 session gate）；**省略動詞約束＋brief 內出現 CHANGE/ADD/DELETE 條目＝實質實作授權**。各 carrier 寫檔能力表單一源＝delegate-bridge repo `AGENTS.md`，禁兩 repo 重刻。案例：muse 審查 job 收到全 CHANGE 條目的 spec brief、漏 read-only 指令→muse 讀完逕行實作 444 行（Writer/Reviewer 分離被打破）。
- Dispatch prompt 禁以 `/` 開頭——zcode 系 carrier 會當 slash command 拒執→exit 0 假完成（AIR-165 實證，DB-26 bridge 側修復中）。
