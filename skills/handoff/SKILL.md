---
name: handoff

description: "產出 self-contained 交接 prompt：把當前工作（進度 + 決策脈絡 + 下一步）打包給另一個 session/repo/provider。與 /at（usage resume）分工 — handoff 交別人，/at 自己續"
when_to_use: "Hand off work to another Claude Code session, another repo's session, or a cross-provider web LLM (ChatGPT/Gemini). Package current progress + decision rationale + next step into a self-contained prompt. Not for usage-limit resume (use /at)."
argument-hint: "[接手方] [任務] [--save]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# /handoff — Self-Contained 交接 Prompt 產生器

把當前工作結晶成 self-contained prompt，交給另一個 session / repo / provider。解決「每次口語『給個 prompt』+ 手工湊 + 決策脈絡帶不過去」的反覆動作。

委託 Skills：
- [self-contained-prompt](../self-contained-prompt/SKILL.md) — 交接 prompt 設計原則（**接手方三層、標準 schema、drift 防護、跨 provider 機密**）；本 command 是薄 adapter，原則不在這重複
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

## 與 /at 的邊界（執行前確認）

| 命令 | 解什麼 | 觸發 |
|------|--------|------|
| `/at` | **時間接續**：usage 用盡，自己 resume | 5h usage limit |
| `/handoff` | **空間分工**：交另一個 session/provider | 主 session 在忙 / 要第二意見 / 跨 repo |
| 定向接續（`--session-id` resume/fork） | **context 接力**：對方 runtime 載入完整對話記憶續問 | 需對方記得整段對話（追問/糾偏/深挖）——成本警示：帶整包 context（codex resume 127K／fork 65K 實測） |

要「自己之後繼續」→ `/at`；要「別人現在接」→ `/handoff`；要「對方帶著完整對話記憶接」→ 定向接續（判準：任務可口述 → handoff doc；需對方記得整段對話才值得續卷成本）。通道現值：muse／codex 兩家族經 bridge（muse＝`task --session-id`，跨 workspace 加 `--allow-workspace-switch`；codex＝`task --family codex --session-id`，原卷不動查詢走 `codex exec fork` raw CLI）；glm／CC 驗證狀態隨 EP 推進變動（隨查 model-routing 專節）——語義矩陣與守衛處置見 [model-routing](../model-routing/SKILL.md)「session 定向接續」。

> **STATE.md 非交接選項**：STATE.md（Last session 觀察，每 session 覆寫）不是命令、非 `/at`/`/handoff` 替代。`/at` resume 時讀它補 observation（寫入步驟見 [state-md-write](../_common/state-md-write.md)）；交接決策仍是 `/at` vs `/handoff` 二選一。

---

## 執行流程

### Phase 0：判斷接手方 + 收集進度

**接手方**（決定 self-contained 程度，三層判定見 [self-contained-prompt](../self-contained-prompt/SKILL.md)「接手方三層」）：`同repo`（= 同 repo 的新 session，預設）/ `跨repo` / `跨provider`。arg 未指定 → 從對話偵測（「問 ChatGPT/Gemini」= 跨 provider、「給 `<other-repo>` 那邊」= 跨 repo、其餘預設同repo），不確定就問一句。

**收集進度**（機械）：

```bash
git log --oneline -5          # 近期 commit（baseline + 已完成）
git status --porcelain        # 未 commit 變更
git rev-parse HEAD            # baseline commit hash
```

+ 從當前對話摘「已交代的決策（為何選 X 不選 Y）+ 下一步 + 待決項」（用戶交代過的才帶，見 skill「決策脈絡原則」）。
+ 識別當前 EP（有 → 引用段落）。
+ EP 弧交接且 build 未完（repo 可跑 code_reality 時）：交接 prompt「下一步」含 `code-reality snapshot --repo <repo> --label <弧id>`（[implement](../implement/SKILL.md) 階段 1 對應物——接力 session 依 handoff 行動、不重讀 skill 階段，不寫就漏；實測 09-06 handoff 續跑弧 4/4 跳過 snapshot）＋**機械驗證行**（cr-audit R8）：「接力首動 `ls .code-reality/snapshots/` 確認 label 在場；缺 → 補跑，不以為已跑」。

### Phase 1：套標準 schema

依 [self-contained-prompt](../self-contained-prompt/SKILL.md)「標準 schema」十欄（任務一句話 / baseline commit / 來源 EP / 已完成清單 / 已決策 / 下一步 / 驗收 / 承接 commit 不重做／建議執行 tier／workspace／卡歸屬）。

其中「建議執行 tier」是 user 開新 session 的路由輸入（條件式，條款見 model-routing skill），「workspace／卡歸屬」為強制欄。

> 欄位盤點對齊 [task-recovery](../_common/task-recovery.md) checkpoint 欄位（目標／已決策理由／已驗未驗證據／open findings／背景 job 收法／授權範圍／下一步＋read-set）；接手端恢復順序亦以 task-recovery 為單一源。接手方自足 prompt 形態不變——三層嵌入照 skill。

有 EP → 引用段落 + 補這次對話剛定的決策；無 EP → 現擠 brief（完整 schema）。

### Phase 2：按接手方調嵌入程度

依 skill「接手方三層」：同repo 引用路徑（對方讀得到 repo）/ 跨 repo 加跨 repo 背景 + 嵌源 repo 相關片段 / 跨 provider 嵌**最小必要**片段。

### Phase 3：跨 provider 機密檢查（僅跨 provider）

依 skill「跨 provider 機密檢查」，flag 敏感內容（帳號/金鑰/真實持倉/未公開策略/客戶資料）並提醒 redact（代稱/抽象化）。workspace／卡歸屬欄＝內部拓撲資訊——跨 provider 時判定抽象化／省略（repo／WT 路徑不直出）；「建議執行 tier」欄條件式自足、無模型名，逕用。

### Phase 4：產出

預設印 markdown code block（複製貼到目標 session/provider）。

帶 `--save` → 交接內容寫入追蹤卡 `backlog task edit <id> --append-notes "<交接內容>"`（卡 notes 段〔Implementation Notes〕，隨卡歸檔，board 可見；不另寫檔案。⚠️ CLI 無 `--comment` flag——09-05 MOS session 實測回報修正，`--append-notes` 是唯一掛卡形態）。

> **有卡任務優先「卡即 handoff」**：卡 `desc`＋`notes`＋`references`＋`EP` 已 self-contained（見 [kanban-board](../kanban-board/SKILL.md)「卡即 handoff」），交接優先掛卡 notes（`--append-notes`）；原寫檔路徑已退場。**無追蹤卡**（跨 provider 一次性等）→ 不落檔，直接複製輸出貼給目標——`--save` 無標的可掛＝不適用。

---

## 參數

| 參數 | 說明 |
|------|------|
| 接手方（可選）| `同repo` / `跨repo` / `跨provider`；省略則偵測或問 |
| 任務描述（可選）| 交接的工作；省略則從當前對話推導 |
| `--save` | 有追蹤卡：交接內容掛卡 notes（`--append-notes`，隨卡歸檔，不寫檔）；無卡＝不適用（直接複製輸出） |

## 執行約束

### 強制

- 必須套 skill 標準 schema
- **已決策（為何選 X 不選 Y）必含**（決策脈絡是最常漏的）
- 嵌 code 必須讀回 commit 版本（drift 防護）
- 跨 provider 必須跑機密檢查

### 禁止

- ❌ 嵌整檔（只嵌回答問題必要的最小片段）
- ❌ 把用戶沒交代的決策硬擠進去
- ❌ 跨 provider 未跑機密檢查就產出
- ❌ 處理 usage resume（那是 `/at`）

## 流程位置

```
（主 session 在忙 / 要第二意見 / 跨 repo）→ /handoff [接手方] → 貼到目標 session/provider
```

接手方給建議 → 貼回原 session → `/judge-review` 評估採納。
