---
name: reference-zcode-cc-subagent-model-thinking
description: ZCode/CC subagent 對照遺產——08-29 registry split 後多半過時；仍活：別名實測、新chat判決、cwd 錨定
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_5615b021-a44d-4b22-bada-7bc2fa6bb88e
  modified: 2026-08-28T14:56:46.891Z
---

2026-08-28 對照快照——**08-29 registry split 後結構性過時**，現值單一源＝`agents/AGENTS.md`（registry 治理＋dispatch matrix）＋model-routing skill 解析表＋agent-workflow skill。以下只留仍活實證。（09-08 蒸餾；DROPPED：通用設計四層食譜〔registry split 設計檔承載〕、CC 官方方向參照〔08-28 時效〕、視覺兩路徑〔vision-review agent 承載〕）

**仍活實證**：
- **CC-on-GLM 別名**：Agent tool 填 `model:"haiku"` 實跑 glm-5.3-flash（transcript `"model"` 唯一值驗證）——sonnet/opus/haiku 在 GLM provider 是 tier 別名；驗證法 `rg -o '"model": ?"[^"]*"'`（禁全讀 JSONL）。**09-08 全映射實證**（定義源＝`~/.claude/settings.json` env，z.ai 相容端點 `ANTHROPIC_BASE_URL`、走 GLM 額度）：opus→glm-5.3[1m]、sonnet／haiku→glm-5.3-flash[1m]——查映射直接讀 env 檔即可，不必開 CC session 挖 transcript；CC 端 full-tier 投影已釘 `model: opus` 別名（AIR-44 CLAUDE_PINS——別名可攜，env 切 provider 免重釘）。
- **新 chat 判決慣例**：registry/快照類判決一律新 chat（restart+resume 有快照歧義；file symlink 可載入 09-06 實證）；user 開新 session 貼自足 prompt 寫 verdict 檔、主 session 讀檔收案。
- **subagent cwd＝session 工作目錄**（09-06 實測）：body 內相對路徑 cwd 錨定或絕對，`../roles/` 形必斷。
- **不對稱殘件**：`thoughtLevel` 綁具體模型（inherit 跟主；CC 可獨立降 thinking——搬不進 ZCode）；欄位名 `thoughtLevel`≠`reasoningEffort`（靜默忽略）；ZCode 快照制（改定義須新 session）；ZCode plugin agents 唯讀（拿不到 UI 調 model 槓桿——agents 不走 plugin 分發之因）；CC `--agents` JSON headless 可帶分層。
- **flash 載體判例（09-01）**：ZCode 無 spawn-time model 參數→flash 必須先有 pin 定義檔＋開新 session 才派得到；機械批量值得 pin（mem-distill 第四顆）；5 並發撞 1302 實證（不重派，主 session 補位）。

相關：[[agents-registry-split-design]]、[[reference-zcode-session-agent-communication]]
