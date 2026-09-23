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
| `/handoff` | **空間分工**：交另一個 session/provider | 主 session 在忙 / 跨家族第二意見（bridge 工單 `--family muse|codex`→findings 貼回→judge） / 跨 repo |
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

### Phase 1.5：交接資訊採「收取法形」書寫（AIR-168）

packet 內的交接資訊以**收取法形**書寫——每項交付寫「**產出路徑**＋**收法**（哪個命令／怎麼讀）＋**對帳注記**（若有已知矛盾，明寫）」。**狀態快照（「誰在跑／做到哪」類手抄敘述）禁入 handoff**——寫下即爛；狀態一律以 `uv run python scripts/inflight_snapshot.py` 機械生成現值替代，不手抄進 packet。依據：AIR-168 契約 §附帶——收取法形實證全數存活、快照形寫下即爛。

### Phase 2：按接手方調嵌入程度

依 skill「接手方三層」：同repo 引用路徑（對方讀得到 repo）/ 跨 repo 加跨 repo 背景 + 嵌源 repo 相關片段 / 跨 provider 嵌**最小必要**片段。

### Phase 3：跨 provider 機密檢查（僅跨 provider）

依 skill「跨 provider 機密檢查」，flag 敏感內容（帳號/金鑰/真實持倉/未公開策略/客戶資料）並提醒 redact（代稱/抽象化）。workspace／卡歸屬欄＝內部拓撲資訊——跨 provider 時判定抽象化／省略（repo／WT 路徑不直出）；「建議執行 tier」欄條件式自足、無模型名，逕用。

### Phase 4：產出 packet（completion 第 1 段：packet-produced）

產出 markdown code block（packet 本體；同時是 manual fallback 的攜帶載體，見 Phase 5）。

帶 `--save` → 交接內容寫入追蹤卡 `backlog task edit <id> --append-notes "<交接內容>"`（卡 notes 段〔Implementation Notes〕，隨卡歸檔，board 可見；不另寫檔案。⚠️ CLI 無 `--comment` flag——09-05 MOS session 實測回報修正，`--append-notes` 是唯一掛卡形態）。

> **有卡任務優先「卡即 handoff」**：卡 `desc`＋`notes`＋`references`＋`EP` 已 self-contained（見 [kanban-board](../kanban-board/SKILL.md)「卡即 handoff」），交接優先掛卡 notes（`--append-notes`）；原寫檔路徑已退場。**無追蹤卡**（跨 provider 一次性等）→ 不落檔，直接複製輸出貼給目標——`--save` 無標的可掛＝不適用（manual paste fallback；分流見 Phase 5）。

### Phase 5：Delivery——scbus 直送第一路＋manual paste fallback（AIR-156）

「prompt 產完」≠「對方收到」。packet 落卡只是 completion 四段的第一段，送達證明照本段追蹤：

| 段 | 判定證據 | 語義 |
|----|---------|------|
| 1 packet-produced | packet 掛卡 notes／落檔 | 起點，非完成 |
| 2 queued-visible | `scbus send` 的 transport receipt（`receipts/<command_id>.json`，stage=accepted＋visible） | 已達收件匣——**receipt＝queued-visible 非完成** |
| 3 consumed/accepted | 對方 recv 消費（pending→consumed）＋回 semantic ACK（`reply_type=accept`、`in_reply_to=<message_id>`） | 對方 session 承接 |
| 4 ownership-restored | 對方回 `reply_type=completed`＋`result_pointer`＋`evidence` | 交接閉環，可關 correlation |

- **審計錨條款**：receipt（command_id 鍵）＋ACK（correlation 鍵）兩錨同時對上才算完成證據，僅其一＝未閉環禁記完成（[conventions.md](../../governance/conventions.md) 節一對照表）。`declined`＝禁原樣重發；`needs-info`＝補件後同 correlation 重發。
- **ack protocol 本輪不擴**：receipt 語義上限＝queued-visible（bus 無 ack／user-read 第三態）；correlated upper-layer reply 已是語義面承接，amendment 須多弧實證。

**target 解析**（已知/未知分流——判定邏輯抽在 `scripts/handoff_delivery.py`，行為由單元測試鎖定）：

```bash
scbus list > .agent-tmp/scbus-rows.json     # registry rows
scbus whoami                                # 本側 session_id／workspace_root
uv run python scripts/handoff_delivery.py resolve-target \
  --target "<對方 session_id 或 claimed name>" \
  --rows-file .agent-tmp/scbus-rows.json \
  --own-session-id "<本側 sid>" --own-workspace-root "<本側 WT>"
```

- `disposition=known-direct` → 走直送第一路（先過下方 Consent gate）；`cross_ownership=true` 時 build-body 加 `--cross-ownership --consent-evidence "<AUTH 指針>"`
- `disposition=fallback-manual`（reason：`no-match`／`ambiguous`／`target-ended`／`self`）→ 降 manual paste fallback

**第一路：scbus 直送**（已知 session；body 結構欄對齊 conventions v2；helper 的機械把關——≤8192 凍結面、consent gate——**只在兩段式下生效**：單行 `$( )` 內嵌會吃掉 helper exit 2，gate 攔下時 stdout 空 → `--body ""` 空 envelope 照送＝fail-silent，禁用單行形）：

```bash
# 段 1：先組 body——exit 非 0（consent gate／超 8192／缺欄）即停不送，顯式 || 閘勿依賴 set -e
uv run python scripts/handoff_delivery.py build-body \
  --summary "<packet 指針＋一句話>" --source "<repo-id/card-id>" \
  --correlation-id "<uuid>" --want "session 承接後回 accept" \
  --card-ref "<repo-id/card-id>" > .agent-tmp/handoff-body.json || return

# 段 2：段 1 成功才送
scbus send --to "<session_id>" --body "$(cat .agent-tmp/handoff-body.json)"
```

send stdout 的 `message_id`／`command_id` 即 queued-visible 證據，記進交接卡 notes；大材料落 repo 檔案或卡 notes、訊息只派路徑。

> **msg_type 註記**：conventions v2 的 msg_type 四值枚舉（cross-repo-bug／fix-ready／verify-pass／breaking-intent）不涵蓋 handoff 交接——delivery body 以消費端約定 `handoff_delivery` 標記（先例＝proto §5.9 控制信 body 約定），不冒用枚舉值；晉升共用 schema 須 conventions.md amendment，非本 skill 權限。

**fallback：manual paste**（直送 unavailable 時的降級路徑，非預設）：

- 觸發條件＝`fallback-manual`（對方 session 未誕生／跨 provider 無法進 registry／ambiguous／ended）——此時印 code block 由 user 手貼
- user 親手貼＝隱式授權載體但**無送達證明**：completion 停在第 1 段 packet-produced＋user 見證，禁記 queued-visible 以上任一段

> **同repo 預設路徑標記（tri 裁決 4，勿重辯）**：同repo 預設＝新 session 尚未存在於 registry → 天然落 manual paste fallback，現況路徑本輪不斷路；「同 repo 交接意圖遷 Marshal continuation」方向已定，等該路徑 dogfood 後再收斂，本節僅標記。

### Consent gate（直送的授權面——AIR-156）

user 親手貼原本是隱式授權載體；直送後 AI 可直達另一 session mailbox，授權面重新設計——**不為機械化拆安全閘**：

- **scbus 直送＝outward action**（另一 session 在 undo 前可觀察到）：AI 發起、**逐次授權**——每次 send 前須 user 明確授權並附 `AUTH: user said "<their exact words>"`。定義源＝[rules/outward-action-consent](../../rules/outward-action-consent.md)（本節是消費引指非第二定義源）；skill 條文、交接任務本身、對方在 registry 可見，都不構成授權
- **跨 ownership envelope**（target `workspace_root` ≠ 本側，即 resolve-target 的 `cross_ownership`）：delivery body 必帶 consent 欄——`"consent": {"granted_by": "user", "evidence": "<AUTH 指針>"}`（`build-body --cross-ownership` 無 `--consent-evidence` 即 fail loud）。欄位語義＝審計註記：**transport consent ≠ mutation authority**，送達≠取得對方寫入權，承接後 mutation 仍歸對方主權（[conventions.md](../../governance/conventions.md) 節一 evidence 條款）
- **同 ownership**：gate 不豁免——直送仍是 outward，逐次 AUTH 照走；僅 body 免 consent 欄

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
- 直送必過 consent gate：每次 `scbus send` 逐次 AUTH（Phase 5；跨 ownership 另帶 consent 欄）
- 直送後照 completion 四段記錄送達狀態（receipt／ACK 證據進交接卡 notes）

### 禁止

- ❌ 嵌整檔（只嵌回答問題必要的最小片段）
- ❌ 把用戶沒交代的決策硬擠進去
- ❌ 跨 provider 未跑機密檢查就產出
- ❌ 處理 usage resume（那是 `/at`）
- ❌ 無 user 逐次授權的 `scbus send`（outward action；skill 條文≠授權）
- ❌ 以 transport receipt 冒充「對方收到」——receipt＝queued-visible 非完成

## 流程位置

```
（主 session 在忙 / 跨家族第二意見 / 跨 repo）→ /handoff [接手方] → delivery：已知 session 走 scbus 直送（consent gate 後）／否則 manual paste fallback → completion 四段追蹤
```

第二意見走跨家族：`/handoff` 產 self-contained 工單 → bridge 派發（`task --family muse|codex`）→ 對方 findings 貼回原 session → `/judge-review` 評估採納（獨立性階梯見 [review-engine](../review-engine/SKILL.md) 執行預設點 7——跨家族是 systematic bias 的升級軸）。非第二意見的一般交接 → 接手方回覆 → 貼回原 session → `/judge-review` 評估採納。
