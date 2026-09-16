---
name: codex-config-zai-topology
description: codex 四面：z.ai 認證拓撲/rescue 轉發 env 陷阱/sol high 審查能力剖面/AGENTS.md 上限 knob——跨家族第二意見定位
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_86e17312-7b74-4b25-a8dd-2b6ea28b2802
---

codex＝OAuth 本體＋z.ai 工具鏈＋rescue 轉發面；審查側是跨家族對抗性第二意見（盲點與 in-family 正交），dispatch 政策＝僅顯式指定。

> merged_from: reference_codex-companion-plugin-root-env, reference_codex-sol-high-review-capability, 2026-09-07 cluster-merge wave

## 認證與 z.ai 拓撲（original: reference，keeper 本體）

~/.codex 設定拓撲（2026-08-23 查證）：**本體不吃 z.ai**——`auth.json` `auth_mode=chatgpt`（Google OAuth），`OPENAI_API_KEY: null`；config.toml 無 model_providers/base_url。⇒ VSCode Copilot BYOK 想抄 codex 的 API＝無東西可抄。

**config.toml 的 z.ai 兩處（皆非 codex 自身 API）**：①四個 z.ai MCP servers（跨 harness 工具鏈標準佈建）；②`shell_environment_policy.set` 的 ANTHROPIC_* 六行——codex 生子進程注入，在其 shell 內跑 Claude 家族 CLI 導向 z.ai 相容端點（不打真 Anthropic 計費），codex 核心不讀。脫離代價＝失 web/zread＋nested claude 真計費，現狀合理。**計費規則（09-05 官方 doc）**：資源包/餘額場景必用 OpenAI 通用端點 `/api/paas/v4`；Anthropic 端點只消耗「從未買 Coding Plan 且加白」帳號餘額。

相關：[[vscode-byok-chatelanguagemodels]]、[[ccr-local-gateway]]

## AGENTS.md context 上限面（09-08）

chain＝global（`~/.codex/AGENTS.md`；`AGENTS.override.md` 優先獨佔）＋root→cwd 逐層各一檔串接，combined 達 `project_doc_max_bytes` 即停——**預設 32KiB（比 muse 64KiB 更緊）**。09-08 已調 `~/.codex/config.toml` `project_doc_max_bytes=102400` 且 **runtime 生效已驗證（雙探針，9fb9bc9）**：升級 `npm install -g @openai/codex@latest` 至 **0.153.4** 後（0.152.0 對 gpt-6-astra 一律 API 400「需新版 CLI」，請求未達模型不耗額度）——①覆述全域指引最後一行＝`<!-- bundle-end -->` ✅②引用 pipe-to-tail 禁令原句 ✅（tool-discipline 在 bundle 71.5KB 處、32KiB 預設下不可見——兩針都過=全綠）。**模型面**：`terra` 模型存在但「not supported when using Codex with a ChatGPT account」（ChatGPT 訂閱認證不給用，跨家族測試腿用預設 astra）。**model/effort 旗標（09-08 實測）**：config.toml:5-6 pin `model="gpt-5.5"`＋`model_reasoning_effort="low"`＝不帶旗標的落點（model-routing 舊記「本機已 pin sol」過時已修 0615d18——要 family 表值必須顯式帶旗標，禁信 config 預設）；raw `codex exec` 形態＝`--model <id>`＋`-c model_reasoning_effort=<v>`，**`--effort` 非 raw 旗標**（unexpected argument 實證；那是 plugin 轉發面詞彙）；額度牆訊息「try again at <local time>」直讀 reset 時點。**config 殘留清況（09-08 晚，兩條皆已刪、同備份 `config.toml.bak-crg-cleanup`）**：`[mcp_servers.code-review-graph]`@5555（舊 CRG、服務 08-30 已退場）＋`mcp_servers.nogic`（127.0.0.1:63283，全機零蹤跡孤兒——無 binary/服務/引用）。**9 條/session `missing-content-type` 刷屏真源＝z.ai MCP 三件**（web-reader/web-search-prime/zread）：對 `notifications/initialized` 回 **HTTP 200＋空 body＋無 content-type**（規範應回 202 Accepted）→ rmcp worker fatal；**3 server×3 retry＝每次 session 剛好 9 條**；context7 正確回 202。陷阱：initialize 步四件全正常（200+SSE 有 body）——**歸因必須兩步直探（initialize 與 notification 分別打、帶 config auth、key 不落輸出），單探 initialize 會漏**。**key 假設已排除（09-08 晚）**：user 假設「沒設 key」→ 指紋對帳推翻——codex trio `Authorization`（len 56 Bearer）與 ZCode config（`~/.zcode/cli/config.json` `mcp.servers.{web-reader,web-search-prime,zread}.headers.Authorization`）**兩端同一把**（sha 前 10 同值）；ZCode 側 live 呼叫綠（web_reader 取 example.com 成功）；帶 key initialize 200＝key 有效（缺/錯 key 是 401 非 200）。**差異在 client 嚴格度非授權**——同 server 同 key，ZCode MCP client 對 200+空 body 寬容零報錯、codex rmcp 嚴格 fatal。性質＝上游 z.ai 協議 quirk；**codex session 內三件工具實際可用性未驗**（rmcp worker fatal 可能代表工具斷線；驗法＝一次 codex run 呼叫 z.ai 工具，耗額度留 user 裁量）；**處置（09-08 晚 user 定）＝「先不管」——忍噪音現狊**；另兩選（codex 端停用 trio／等上游）留待真需要 z.ai 工具時再議。**旗標 end-to-end 驗證**（換帳號後）：`--model gpt-5.5 -c model_reasoning_effort=low` → exit 0＋header 正確顯示雙值。新 cr 接線走 **plugin 形態**（`[plugins."code-reality@code-reality-market"]`，stdio per-session——launchctl 無 8200 服務屬正常，plugin 不需常駐）。附帶：codex 對 skill descriptions 有獨立 context budget 並自動縮短（警告可見）。官方「太大」處方三選：調 knob／拆 nested 目錄／reference task-specific md（agent 循引用讀非機械展開）；另有 `AGENTS.override.md`（probe 借用）、`project_doc_fallback_filenames`、`CODEX_HOME` 分身。官方建議整理（keep-small／犯兩次才 codify／五層互補／skills progressive disclosure）：ai-analysis/reports/2026-09-08-codex-agents-md-usage-and-insights.md。

## rescue 轉發 env 陷阱（original: reference）

codex-rescue agent 以 `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task` 轉發——subagent shell 中該 env 偶發為空 → `MODULE_NOT_FOUND`，job 從未建立（此形態重派**不是雙跑**）。症狀：result 空或 `Cannot find module '/scripts/...'`。解法：①重派**新** agent（首派成功、resume 後失敗，09-03 實證）；②prompt 預寫 fallback：顯式設 `CLAUDE_PLUGIN_ROOT`（版號路徑先 ls 驗 scripts 在場）。失敗 log：`/Users/ctai/.zcode/cli/exec/sess_subagent_<agentId>/call_*.log`。與 [[muse-code-cli-facts]] 的 wrapper≠runtime 錯位區分：那個真的在跑，這個根本沒啟動。

## sol high 審查能力剖面（original: reference，09-06 單樣本勿外推 dense code）

**強項**：終版 11 findings 機械查證全成立零誤報、跨 worktree 錨點 100%；**自我否證是真行為**（3 false Critical 經 hash 對帳撤銷並提煉成最佳 finding）；讀架構 failure mode 非 lint；驗收規格可直轉 TDD。**弱點**：第一反射不問 authority（事後修正非事前意識）；嚴重度偏緊兩處；建議停概念層；雷達下限（格式漂移/gitignored 缺口漏抓）。**followup 加成**：驗修復 diff 抓回實作者自驗＋測試全漏的真 blocker（共享盲點跨家族兌現）；餵已修清單複審用 cell 級窮舉收斂。**定位**：輸出讓 judge-review 便宜（整場零反駁只校準）；「可信」來自查證習慣非戰績。dispatch 不變＝[[feedback_quota-failover-policy]]。關聯弧 [[project_codex-fullrepo-review-adjudication]]。
