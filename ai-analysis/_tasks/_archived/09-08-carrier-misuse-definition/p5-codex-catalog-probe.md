# AIR-48 P5①：codex catalog 縮短真通道探針（SM-7 補實彈）

> 範圍：EP P5①——S6 v2 模擬（縮短至 37% 仍 12/12）留下的缺口＝「材料經檔案讀取非 catalog 載入」。本探針以真實 skills catalog 機制跑一次 retrieval，關閉該面。產出不 commit（隨 dogfood 批次）。

## 源碼查證（~/Github/codex clone；`codex-rs/ext/skills/src/render.rs`）

- **budget 三形態**（`skill_metadata_budget`）：`max_context_tokens` 有設＝min(設定值, 10,000) tokens；否則 context window ×2% tokens（min 1）；兩者皆缺＝8,000 chars fallback
- **分配三層階梯**（`allocate_skill_lines`）：①全額放入（總成本≤budget）→ ②**全員保留＋desc round-robin 水位配字**（每輪每 skill +1 char，無人獨佔；minimum 成本＝去 desc 行仍放得下時）→ ③按序貪婪放入「無 desc 行」（`- name: (file: path)`）、放不下者**整條省略**（warning：`Exceeded skills context budget...`）
- **排序鍵**（CoreCompatible `order_entries`）：scope rank **System(0)→Admin(1)→Repo(2)→User(3)→None(4)**，再 name、main_prompt——**USER scope 排最尾＝tier-3 溢出時最先被省略**
- 每條 desc 硬上限 1,024 chars（`MAX_CATALOG_SKILL_DESCRIPTION_CHARS`）；tier-2 縮短平均 >100 chars 才出警告
- prompt 觸發規則（catalog_prompt.rs）：「task clearly matches a skill's description shown above → must use that skill」——desc 是唯一隱式匹配面
- `short_description` 是 SKILL.md 選填第二欄位（ExtensionCompatible policy 優先採用；CoreCompatible 用 description）

## Live 探針

- **材料**：12 個 live 池條目（S1 PROBES 目標集——`ai-analysis/_tasks/09-08-context-lifecycle-unification/s1-probes/retrieval_probe.py`）desc 原文（38-97 chars，條件句領頭文法），以 USER scope 真實安裝形態裝入 `~/.agents/skills/<name>/SKILL.md`（name＝stem 底線轉連字；official skills.md 查證 USER 位置＝`~/.agents/skills`，非 `~/.codex/`——handoff 措辭校正）。安裝前快照＋碰撞檢查，82→94
- **形態**：`codex exec --model gpt-5.5 -c model_reasoning_effort=low`（旗標形態取自 reference_codex-config-zai-topology）；prompt 限 catalog-surface 匹配（禁讀檔/禁工具/禁展開 skill）——與 S1 live 探針（給檔讀）刻意對照
- **結果**：exit 0、tokens 51,218、session 01a08175-da94-7f33-905e-de365f0a8953

| # | 陳述 | codex 答 | 期望 | 判定 |
|---|------|---------|------|------|
| 1-9, 11, 12 | — | 全數＝期望 skill 名 | 同 | ✅ 11/12 exact |
| 10 | 記憶體快滿了想刪舊東西 | `memory-audit` | `feedback-inflow-needs-outflow` | ⚠️ 匹配歧義（見下） |

- **#10 歸因**：非不可達——codex 選了**真實部署的** memory-audit skill（desc 含稽核/清理語義，對「刪舊東西」同樣匹配）。兩候選並存時的擇優，屬 probe 材料與存量 skill 的語義重疊，非 catalog 機制缺陷
- **tier-2 實彈**：session 輸出含官方警告原文 `Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill, but some descriptions are shorter.`——94 skills 超預算、round-robin 縮短真實發生、**零省略**（tier-3 未觸發）、縮短後可達性維持
- 9×/session `missing-content-type` MCP 噪音如預期出現（z.ai trio 已知 quirk），未影響執行

## 清理驗證

12 個探針目錄移除；`ls` 計數 94→82；與安裝前快照 diff＝零差異（RESTORED-CLEAN）。`~/.agents/skills` 原狀恢復。

## 結論

1. **SM-7 真通道關閉**：S6 v2 模擬結論（desc 縮短後仍可達）在真 catalog budget 機制下再確認——11/12 exact＋1 匹配歧義，零 NONE 零遺漏
2. **池 desc 文法（條件句領頭）在 catalog 縮短環境存活**——desc 觸發面設計與 codex 隱式匹配規則相容
3. **對 AIR-49 的含義**：④codex 池路由走 project AGENTS.md（project_doc 鏈，獨立預算面）不受 skills budget 機制影響——設計選項 B 不因本探針改變；但若未來考慮以 skill 形態暴露池知識：**USER scope 在 tier-3 省略序最尾**（82-skill 部署面已在 tier-2 邊緣），REPO scope 優先
