---
name: ccr-local-gateway
description: claude-code-router v3 gateway——3456 唯一客戶端入口（Anthropic 相容）、3457 core 內部端點勿直連、config 在 config.sqlite
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_816a3837-5b5b-449c-bded-42d3bca0ce91
---

用戶本機 claude-code-router v3（原始碼 `/Users/ctai/Github/claude-code-router`，monorepo + Electron app，gateway process 名 `Claude`）：

- `http://127.0.0.1:3456` — **唯一客戶端入口**，Anthropic 相容（`x-api-key` header + `local-gateway` sk- key）。2026-08-20 實測：`GET /v1/models` 回 7 模型、`POST /v1/messages`（`anthropic-version: 2023-06-01`）端到端通（ZCode/GLM-5.3 正常回覆）。chat 型模型：`ZCode/GLM-5.3`、`ZCode/GLM-5.2`、`ZCode/GLM-5-Turbo`、`Codex/gpt-5.6-terra`、`Grok/grok-4.6`（model id 含 `/`，照抄即可）；另 2 個 `Grok/grok-imagine-*` 是圖/視訊生成非 chat。`/health` 回 running
- `http://127.0.0.1:3457` — **core 內部端點，客戶端勿直連**：要 `x-ccr-core-auth` header（Bearer sk- key 打 `/v1/models` 回空 data）。端點名義上 OpenAI 相容（`/v1/chat/completions`、`/v1/responses` 等）但 auth 是內部的；接客戶端一律指 3456
- Config **v3 已從 `config.json` 遷 `~/.claude-code-router/config.sqlite`**：`api_keys` 表（欄位 `encrypted_key`＋`encryption` 常為 plain；`local-gateway` 的 `sk-...`＝gateway client key；`ccr-profile-*` profile keys 如 default-claude-code / zcode）、`app_config`、`runtime_state`。取 key：`SELECT encrypted_key FROM api_keys WHERE id='local-gateway';`
- ccr Agent Config profile 清單**無 VSCode**（有 zcode/opencode/kilo/kimi/grok/pi/workbuddy/codex/claude-code/claude-design）——VSCode 接 ccr 走 BYOK 直連 3456（配方見 [[vscode-byok-chatlanguagemodels]]）
- docs 在 repo `docs/src/content/docs/en/configuration/`（server.md / api-keys.md / agents/*.md 客戶端接法可參考）
- 查 sqlite 的 key 值時輸出 mask，不整段印
- **v3 provider 出站 auth（原始碼驗證 09-02）**：provider 定義在 config.sqlite `app_config`（key='default' JSON 的 `Providers[]`：api_base_url/api_key/type="anthropic_messages"/models；ZCode provider 範例＝api.z.ai/api/anthropic）。ingress strip 客戶端 auth（stripLocalGatewayAuthHeaders）後按 provider credential **重寫出站 auth**——客戶端送什麼 header 不影響出站。兩內建模式（packages/core/src/agents/local-providers/shared.ts）：`bearerAuthPlugin`＝Authorization Bearer＋removeHeaders x-api-key；`apiKeyAuthPlugin`＝x-api-key＋removeHeaders authorization；auth.headers 為任意 header map 可自訂。→ 接 Meta（api.meta.ai，官方僅認 Bearer）＝anthropic_messages type＋Bearer 模式即可（三路分析見 [[agents-registry-split-design]]）
