# AIR-89 EP——背景 agent liveness 兩項 skill 修正（handoff 承接）

> **ep_type**: implementation（小型：兩處 doc 定點修正，內容定版勿重辯）
> 卡：AIR-89。材料源＝backlog/drafts/handoff-agent-liveness-2026-09-13.md（codex 復議定版 job-mtzs63qz）＋delegate-bridge fdc8c47。
> baseline＝main @ 42c223c。

## UC 盤點
- Backlog：AIR-89（本卡）。無新 UC（既有 skill 事實修正＋doctrine 增補）
- 同主題 memory：`feedback_verify-both-sides-nonempty`（正交）；`reference_external-runtime-delegation-family`（bridge 面——:227 修正後其「heartbeat 需求」引用面需複核無殘留）

## 段落 0：標的現況（已核）

1. `skills/model-routing/SKILL.md:227` 行尾（liveness ticker bullet 內）現句：
   > bridge 端 heartbeat（jobs.json progress 時間戳／`wait --stuck-alert`）＝delegate-bridge roadmap 需求；fleet 架構位（execution identity 觀測 runtime 腿）＝AIR-71。
   ——兩處過期：heartbeat 實已交付（d1/2.0.3/39b6964）；flag 名錯（`--stuck-after` 非 `--stuck-alert`）
2. `skills/agent-workflow/SKILL.md`「Spawn 預設背景」節（L66-75）——L75 已有「主對話被中斷時 agent 會連帶 killed、產出遺失」但無死亡**盲區**防禦（通知 completion-gated/in-memory registry/閒置不能自醒三性質＋app 重啟全殺）。placement＝該節尾新增子塊

## 段落 1：model-routing :227 事實句替換（機械）

**old**（行尾句）：
```
bridge 端 heartbeat（jobs.json progress 時間戳／`wait --stuck-alert`）＝delegate-bridge roadmap 需求；fleet 架構位（execution identity 觀測 runtime 腿）＝AIR-71。
```
**new**（codex ep-review 修訂：去版本/commit provenance——出處留本 EP/card/git）：
```
bridge 端 heartbeat 已交付——背景 worker 每 ~2s 寫 `extra.heartbeatAt`＋`lastEventAt` 雙軸（前景不寫）；consumer＝`wait --stuck-after <ms>`（strict parser、stderr 軸別 alert＋dedup）＋`runs` 600s `running (stuck?)` 提示；AIR-71 fleet 架構位（execution identity 觀測 runtime 腿）不變。上方 ticker 建議保留——它看工作產物停滯，與 heartbeat 軸互補。
```
（交付 provenance＝delegate-bridge d1/2.0.3/commit 39b6964——僅記錄於此，不入長壽 instruction）

**驗證**：`rg -n "stuck-alert|roadmap 需求" skills/` → 0；新句含 `--stuck-after`＋「已交付」；**memory `reference_external-runtime-delegation-family` L43「roadmap」stale 句同步修（必修項，非條件式——codex 點④）**。

## 段落 2：agent-workflow 死亡盲區 doctrine 增補

**placement**：「Spawn 預設背景」節尾（L75 後）新子塊。**內容**（codex ep-review 修訂版：scope 限定 ZCode app-owned＋去日期/分鐘 provenance＋notification 收斂句——點①③）：

```markdown
- **背景 agent liveness（死亡盲區防禦——真實案例：ZCode app 更新重啟殺掉多個背景 agents、長時間無人知）**：通知是被動喚醒——可以等通知，但**一旦被喚醒（completion／user message／resume）、準備依賴舊 agents 結果前，先過 generation/reconciliation checkpoint**：確認承載 process generation 未變（ZCode app-owned Agent-tool 背景 agents：app 重啟＝舊代全死、零歧義；delegate-bridge external runtime 背景 worker 跨 session 存活，依其 jobs 狀態判定）。generation 命中後**先收 residue 再重派**（DB＋transcript＋worktree 殘留——完成未送達者盲重派＝duplicate side effects）；per-agent 判定禁「全凍結才報」聚合；**silence ≠ death；old-generation unresolved ≠ safe-to-retry**。驗屍法：db.sqlite `MAX(time_created)`（Python `sqlite3`＋`file:...?mode=ro`——CLI 有 silent-empty 坑）＋`ps`＋transcript mtime＋`git status` 殘留＋`TaskOutput` registry 查無。防禦階梯全案（WAL receipt／generation watermark reconciliation／exact-process hard-death dual-signal／stall advisory）＝probes 後另案建卡。
```

**矛盾核對清單**（codex ep-review 補遺後六項——AC#2 舉證）：
1. 同節 L75「agent 會連帶 killed、產出遺失」——新塊**延伸**非矛盾（kill 機制＋盲區防禦互補）
2. **同節 L70「通知會自動接手」＋L73「通知後無縫接手」（codex 點③）——新塊收斂語「可以等通知，但喚醒後先過 checkpoint」明確與之相容：接手＝被動喚醒成立，喚醒後的第一動作＝checkpoint 非直接依賴**
3. `model-routing` liveness ticker bullet（同 commit 改後）——ticker 看工作產物停滯 vs 新塊看 process generation：**互補軸**，新塊不重複 ticker 門檻
4. `model-routing`「兩端 SessionEnd 差異」bullet（CC 端 hook 殺 job 進程樹）——app 重啟場景同為 process 死亡族譜，語義相容；scope 限定語明確排除 external runtime 誤讀
5. `rules/tool-discipline.md`「背景執行」段（spawn 後回報即結束 turn 等通知）——同 2 的收斂語相容
6. liveness ticker 的「救援法＝muse-build-round-ops」引用——不受影響

## Scenario Matrix

| # | 情境 | 期望 |
|---|---|---|
| S1 | rg `stuck-alert\|roadmap 需求` skills/ | 0 hit |
| S2 | 新句要素 | `--stuck-after`＋「已交付」＋AIR-71 不變＋ticker 互補語在場 |
| S3 | drift 掃（五項核對清單） | 零矛盾；`--stuck-after` 全 repo 無第二處定義 |
| S4 | deploy＋tests | 三端 deploy 綠＋404 tests（skill 檔不進 bundle——deploy 應零變化或 [SKIP]） |
| S5 | **行為驗收**（codex 點⑤——instruction-testing 高風險 discipline）：fresh-context 壓力案例「收到 completion/user 訊息後、需依賴舊背景 agent 結果」——control（無 doctrine）vs treatment（帶 doctrine 段）各 5 reps（in-harness Agent tool spawn＝fresh context，不走故障中的 bridge headless 腿）；判分＝回應是否先提 generation/residue 檢查再重派/依賴（非背誦 doctrine） | treatment 多數先 checkpoint；control 多數裸依賴——RED→GREEN 形態成立 |

## 執行形態
- 兩處 Edit（主 session 直做——逐字規格、無語義判斷空間）＋驗證 gate 四項＋commit（帶事故脈絡）
- 改前載 instruction-writing skill（卡面驗收要求）；memory 池引用面複核照段落 1
