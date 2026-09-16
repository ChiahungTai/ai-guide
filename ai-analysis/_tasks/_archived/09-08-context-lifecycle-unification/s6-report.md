# S6 報告：觸發面對齊與 spine

> parent: `s6-ep.md`。registry 投影生成機制未動；S1 單池結論不自動推廣為跨池結論。

## 1. 對齊清單（S1 定案可執行部分：情境句領頭，P5 三家族實證）

- 初掃（frontmatter 機械 audit，80 skills＋10 roles）：skills 68/80、roles 2/10 帶觸發語境。
- 誤報排除：英文 `Use when`／`when_to_use` 欄即語境化（與中文「當你」同效），重算後真缺口＝**4 skills＋8 roles**（中文體無情境句領頭）。
- 已對齊 12 檔（僅 description 首句，機制零碰）：
  - skills：code-review-and-quality、compact-prep、cross-verify、kanban-board
  - roles：archify-gen、cr-research、cross-verify-investigator、impl-lite、lite-verify、mem-distill、spec-miner、vision-review
- 複驗：skills 80/80、roles 10/10（audit 腳本見工作記錄 exec-163）。**口徑殘餘（post-build primed F3）**：100% 是「帶觸發語境」寬口徑（英文 `Use when`／`when_to_use` 欄計入）；**非條件句領頭的 desc 仍存在**（如 code-reviewer 雙檔「獨立程式碼審查者…」領頭）——剩餘清單歸後續收斂波次/S6 擴大，非文法全對齊宣稱。

## 2. spine 位置決議（二選一已定案）

- **選 `~/.agents/memory-spine/`**：兄弟目錄候選在 `~/Github/` 下無實體（實測不存在）；`~/.agents/` 已是跨池共享根（AGENTS.md／skills／commands 同住）。
- 實體：`~/.agents/memory-spine/index.md`（plain md＋同格式 frontmatter，含 routing 認養表）。
- ai-rules 側 routing 行：root `AGENTS.md`「Memory spine 路由」行（已加）。
- 生成掛點：條目由 ai-rules 側 session 寫入；各池 generator 認養 routing 行段（ZCode 待定；registry 機制不動）。

## 3. 跨 harness 投影確認

| 池 | 確認 |
|----|------|
| CC | symlink 原生可達（`~/.claude/skills`→本 repo `skills/`、`rules`、`agents`、`CLAUDE.md` 四條 symlink 實測在場）；不宣稱 bundle rank 投影 |
| muse | read-only 確認（禁 add/edit Memory；本 session 零寫入） |
| codex | auto-memory 不碰（本 session 零觸碰；CLI 0.153.4 在場，未跑 live exec——見 §4） |

## 4. SM-1 跨池版＋P6 desc 縮短情境

- 基線重跑：`retrieval_probe.py` 原面重跑與凍結 `.out` **IDENTICAL**（A=B=C=12/12，可重現）。
- P6 情境（codex skills-budget 自動縮短，S0 P6 實證）：兩檔縮短變體—
  - v1（散文行 50%，表格豁免）：面幾乎全表，僅 −57B，無鑑別力（方法失誤，已記錄）。
  - v2（無豁免，>40 字行全砍半）：armA 32,502B → 12,109B（37%），**仍 A=B=C=12/12**。
- 結論：P6 式縮短至 37% 下 SM-1 命中率無退化；機制＝寬判定下限（中文詞片段＋target-name fallback 存活），**非** codex 真實 budget 行為驗證。
- **live codex 探針已補（09-08 晚，unverified 解除）**：`codex exec --model gpt-5.5 -c model_reasoning_effort=low` 對 B 形態材料（armB-index＋_inventory）做 12 中性陳述指認——**12/12 全中**（68,745 tokens、exit 0；證據 `s1-probes/retrieval_probe_codex-live.out`）。跨家族執行者（S1 同家族天花板的對照腿）＋真 codex runtime 的 findability 雙缺口關閉；codex 內建 skills-budget 縮短通道仍由 v2 模擬承載（材料經檔案讀取非 catalog 載入）。
