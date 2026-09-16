---
name: vscode-byok-chatlanguagemodels
description: VSCode BYOK 走 user-level chatLanguageModels.json＋customendpoint；ccr 3456 已落地（手寫 entry 教訓）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_816a3837-5b5b-449c-bded-42d3bca0ce91
---

VSCode BYOK（Copilot Chat bring-your-own-key，本機 1.134.0 原始碼+官方 docs 查證 2026-08-20）：

- **載體**：`~/Library/Application Support/Code/User/chatLanguageModels.json`（user-level，**所有專案/視窗共用同一份**；非 settings.json）。入口：Command Palette → `Chat: Manage Language Models` → Add Models。例外：VSCode Profile 有獨立 `profiles/*/chatLanguageModels.json`；untrusted workspace（Restricted Mode）model picker 只顯示 Auto
- **Custom Endpoint provider**（`"vendor": "customendpoint"`）支援 `apiType`: `chat-completions` / `responses` / `messages`（Anthropic 協議）；`messages` 型自動帶 `x-api-key` header；url 建議給完整路徑（否則 VSCode 自補 `/v1` + apiType path）。agents in chat 需 `toolCalling: true`
- **Key 存放**（workbench bundle 確認）：明文 key 寫進檔案會被 VSCode **自動遷移**到 secret storage（`chat.lm.secret.*` prefix）並把檔案值換成 `${input:...}` placeholder——明文不會留在檔案
- 相關 settings：`chat.agentHost.byokModels.enabled`（Agents 視窗用 BYOK model，實驗性、重啟 agent host 生效）；`chat.utilityModel`/`chat.utilitySmallModel`（無 GitHub 登入時 utility 任務需另設）
- **ccr 整合已落地（2026-08-23）**：群組名 `ccr`、模型 `Codex/gpt-5.6-terra` → `http://127.0.0.1:3456/v1/messages`（apiType `messages`）、key 已入 secret storage（檔案內 `${input:...}`）。前提：`Claude Code Router.app` 在跑＋Codex 帳號有量（08-23 實測 429 free plan、reset 約 2026-09-17；user upgrade 後免改設定自動通）
- **落地教訓（2026-08-23）：手寫 entry 不現、UI 精靈一次成**——手寫 flat entry（shape 經 copilot package.json schema＋官方 docs 驗證、log 出現 BYOK models available）但 picker/state cache 始終未顯示；改走 `Chat: Manage Language Models` → Add Models → Custom Endpoint 精靈立即成功。精靈寫出的形狀與手寫一致（`{name, vendor, apiKey, apiType, models[]}`），差異僅 key 走 secret storage 遷移流程；手寫為何不現未解（疑 picker cache/載入時序）——下次直接走精靈。另：`chat.agentHost.byokModels.enabled: true` 已加 user settings.json；user chat 面板常駐 agent-host-claude（glm via ANTHROPIC env，見 [[codex-config-zai-topology]]）是另一個 picker，BYOK 模型在 Copilot chat picker
- **codex 來源查證（2026-08-23）**：codex 本體走 ChatGPT OAuth——**無 API 可抄進 BYOK**；機器上可直抄的 LLM API 對 = `~/.codex/config.toml` `shell_environment_policy.set` 的 z.ai Anthropic 相容端點（`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`），model 名去 `[1m]` 後綴填基底名（glm-5.3 等）。z.ai 走 `Authorization: Bearer`（ANTHROPIC_AUTH_TOKEN 風格）——若 VSCode messages apiType 的 `x-api-key` 被 401，fallback ccr 3456 配方。詳 [[codex-config-zai-topology]]
