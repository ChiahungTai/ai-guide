# 工單（advisory·read-only）：post-build 第二意見審查——illustrate 報告殼 template 弧

## 1. 紅線（首段，違反＝失敗）

- **read-only**：本工單為審查工單——禁任何寫入（檔案、git staging、config 皆禁）；只讀＋最終回覆承載報告
- 禁 `git add`／`git commit`／`git push`；git 僅允許唯讀查詢（`git status`／`git diff`）
- 禁把任何產物寫到 `/tmp` 或 repo 外；中間筆記不留檔
- 報告禁出現 email／人名 PII；宣稱附證據（file:line／命令輸出），失敗如實記錄

## 2. 目標（一句話）

對「illustrate 報告殼 template 化」變更弧（uncommitted）做獨立第二意見審查，產出 findings 清單供主 session judge 裁決。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）；審查對象＝uncommitted 變更中屬 §6 清單者
- 並行排除（非本弧、不審不改不納入結論）：`AGENTS.md`、`ai-analysis/_tasks/_archived/09-02-muse-plugin-cc/ep.md`、`backlog/tasks/air-17 …`；已 commit 的 73ed6c2（arch-thinking 載體中性弧）不屬審查範圍

## 4. 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/ep.md`——宣稱源（凍結決策、S1-S3、EP Review F1-F6）
2. `/Users/ctai/Github/ai-rules/skills/_common/illustrate-report-shell.html`——新 template 本體
3. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html`——本弧殼（首個消費者）
4. `git diff skills/_common/illustrate-html-mode.md skills/illustrate/SKILL.md skills/execution-plan/SKILL.md`——三處瘦身/同步 diff

## 5. 已決策（勿重辯）＋矛盾例外

- 本工單為獨立審查——無預設結論；以下僅為事實背景（非結論）：archify 在場（clone＋doctor 全綠）；本弧殼採基礎款＝成本分級選擇；殼內降級槽＝SM-4 刻意測試變體（有「示範」標示）
- **矛盾例外**：發現實際檔案與 EP 宣稱具體衝突→在報告舉證（file:line＋逐字引用），這正是你的職責

## 6. 範圍限定

- 審：上述 §4 四項＋`backlog/tasks/air-23 …` 卡（狀態宣稱 vs 實際）
- 不動：一切（read-only）

## 7. 工具接線

- 讀查：bash（`cat`／`rg`／`ls`／`git status`／`git diff`）＋read_file；字串搜尋一律 `rg`
- 本任務無需 code-reality；禁任何寫入面

## 8. 驗收（命令＋預期——逐條實跑供自己形成證據）

1. `git status --short` → 確認審查對象在場、並行排除項可識別
2. `rg -n "SLOT:" skills/_common/illustrate-report-shell.html` → slot 標記清單（你評估其自足性）
3. `rg -n "calc\(100vh|#0d1117|~200 行|1512|1728|264px|1480" skills/` → 你判讀命中是否全屬預期（template 值＋已知無關命中：memory-audit「200 行」×4＋generate_index.py×2＋consistency 行號假設例）
4. `rg -n "illustrate-report-shell" skills/` → 命中面（你判讀引用是否完整）
5. `rg -c "<section|sidebar-collapsed|frame-wrap" ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html` → 殼結構在場

## 9. 證據紀律＋PII 禁令

- 每條 finding 附 file:line 證據；審查軸無 finding 明寫 CLEAN
- 禁 PII；截斷標明；不掩蓋失敗

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. Findings 清單：`| ID | 嚴重度(🔴阻斷/🟡應修/🟢建議) | 檔案:行 | 問題 | 建議 |`——各審查軸（正確性／EP↔實作對照／引用 drift／文檔品質）逐軸給 CLEAN 或 findings
2. 逐軸評語一句
3. 你最有信心不足、建議主 session 聚焦複核之處

**Completion check**：回報前對 §8 逐條自評 pass/fail；任何未跑項如實標記。
