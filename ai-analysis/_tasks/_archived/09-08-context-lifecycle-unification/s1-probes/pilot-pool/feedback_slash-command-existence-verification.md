---
name: feedback_slash-command-existence-verification
description: 驗證 skill/command 存在性時，先查 session 注入的 available skills 清單（權威來源），不要自己 rg/fd 搜 repo
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 976b997c-1bd7-4e85-90e2-93aefc0f4f4a
---

驗證「某個 skill 或 `/command` 是否存在」時，**第一動作是查 session 啟動時注入的 available skills 清單**（system reminder 裡的 "available skills" 列表）。不要直接 `rg`/`fd` 搜 repo——那是 fallback，且對兩類目標結構性失效。

**Why:**
1. **內建指令**（`/goal`、`/clear`、`/compact`）：不在任何 repo 裡，fd/rg 搜不到 → 誤判「不存在」。早期案例：`/code-review` 宣稱「`fd`+`rg` 零結果 → `/goal` 不存在，移除正確」，實際是內建指令，用戶當場反駁。
2. **Skills**（`/debrief` 等）：session 啟動時 ZCode/Claude 都會注入 available skills 清單。`fd "debrief" ~/.zcode/ --type f` 搜不到（因為 fd 搜 basename `SKILL.md` 不搜目錄名）。正確做法是查清單，不是自己搜——不信任系統提供的清單反而自己搜是失誤。

**How to apply:**
- **查 skill/command 存在性的優先序**：① session 的 available skills 清單（權威，2026-08-15 全面遷移後 skills/ 是單一載入點）→ ② 不確定時問用戶 → ③ rg/fd 搜 repo（最後手段）。歷史：commands 載入點（`~/.zcode/commands/`）已隨遷移退役，清單沒有 = 大概率不存在（內建指令除外，下條）
- **2026-08-15 案例**（歷史，發生於 commands 仍存在的時期）：宣稱「ZCode 無 /consistency skill」並繞道獨立 agent 替代——實際 `~/.zcode/commands` symlink 有 consistency.md，用戶當場糾正。錯因：把 Skill tool 清單當涵蓋 commands 的唯一權威。skills 與 commands 當時是兩個載入點。
- **清單是 per-session 啟動快照，不隨磁碟變動更新**：舊 session 殘留已刪 skill、可能缺新加 skill → 跨 session「X 消失」疑問必須開 fresh session 驗證。2026-08-16 implement 案：舊 session 觀察「implement 消失」（清單還含 85 時期已刪的 idea-refine 等），fresh session 實測磁碟 67 ↔ 清單 67 零差異、implement 雙根在場——快照假象，非實際丟失。
- **ZCode skill 調用形態**：靠 name 由 AI 經 Skill tool invoke，不是輸入框 `/name` slash 直達（官方文檔 pitfall 11）——輸入框打 `/implement` 找不到 ≠ skill 不存在。
- 內建指令（`/clear`、`/compact`、`/goal`、`/config`、`/help` 等）無法從 repo 搜尋驗證——它們是 harness 層級的。不要對內建指令下「不存在」的宣稱。
- 能從 repo 搜尋驗證的：自訂命令（`commands/` 下的 `.md`）、自訂 skills、agents。但即使這些，session 清單仍是更快的權威來源。
- 判別關鍵：命令前綴。`/claude:xxx`、`/<repo-dir>` 通常是 repo/plugin 命令；無前綴的短命令傾向內建。
- 不確定時：不要宣稱「不存在」，標注「未驗證」，或直接詢問用戶。
- **不要在 ai-rules/ai-development-guide.md 維護 skill 索引**——那是第二份清單（drift 來源）；harness 已在 session 注入清單。
