# Handoff：mosaic_alpha 承接——twin cleanup 腳本同步破口修復（F4；源：ai-rules AIR-70 遺留項）

## 任務一句話
把 ai-rules 側 `run-backlog-cleanup.sh` 的**兩段 loud-fail guard** 合併進 mosaic twin（`deploy/scripts/run-backlog-cleanup.sh`）——**合併非覆蓋**（mosaic 側有自己的 `BACKLOG_PRECHECK` override 與跨 repo 依賴註解要保留）。

## Baseline
- 本 repo：mosaic_alpha main WT，承接前 `git log --oneline -3`＋`git status --porcelain` 對時。
- 源錨：ai-rules `30d8c1c`（main）；09-10 掃描報告 finding F4（ai-analysis/reports/2026-09-10-repo-consistency-scan.md 群四，本機 ai-rules）。

## 背景（為什麼）
兩 repo 各一份每日 launchd 清板腳本（Done>30d 卡逐卡 precheck→task complete→commit），檔頭 twin 條款「同邏輯副本——修改須同步」是**人工契約**。ai-rules 側後來加固兩段保護未同步：mosaic 端環境壞（precheck 路徑斷/git 異常）時**不會失敗**——默默逐卡標「[不可清-跳過]」exit 0，正是 ai-rules 註解明言要避免的「靜默 no-op 與誤計 skip」；清板保護實際弱化且無人察觉（顧問評「接近高」邊界）。

## 已決策（勿重辯）
- **合併非覆蓋**——09-13 實 diff 證 drift 雙向：ai-rules 有 guard 沒有 override；mosaic 有 override（`PRECHECK="${BACKLOG_PRECHECK:-/Users/ctai/Github/ai-rules/skills/kanban-board/scripts/backlog_precheck.sh}"`）＋依賴揭露註解（「ai-rules 搬家則此腿斷」）。兩者都要在。
- 要合併的兩段（ai-rules 版逐字，位置＝precheck 變數定義之後、worktree 列舉之前；列舉檢查接在列舉行之後）：
  ```bash
  # 環境預檢：工具或 precheck 缺場 → loud 失敗（靜默 no-op 與誤計 skip 都比失敗更糟）
  for tool in git rg awk date; do command -v "$tool" >/dev/null 2>&1 || { echo "[FAIL] $tool 不在 PATH"; exit 1; }; done
  [ -f "$PRECHECK" ] || { echo "[FAIL] precheck 不存在：$PRECHECK"; exit 1; }
  ```
  ```bash
  [ "${#wts[@]}" -gt 0 ] || { echo "[FAIL] worktree 列舉為空（git 異常？）"; exit 1; }
  ```
  （註：mosaic 版列舉用 awk、ai-rules 用 sed——保留 mosaic 現形即可，只加空列舉檢查行。）
- 三個 WT checkout（offline_backtesting/trading_lab）**不用逐一修**——main 修好隨 trunk 收斂。

## 驗收（禁真跑清卡——會搬卡＋commit）
1. `bash -n deploy/scripts/run-backlog-cleanup.sh` 語法綠
2. **loud-fail 可觸發實證**（安全形態）：`PATH=/nonexistent bash deploy/scripts/run-backlog-cleanup.sh` → 預期 `[FAIL] git 不在 PATH` exit 1（環境壞時真的會叫，不是裝飾）
3. `BACKLOG_PRECHECK=/nonexistent bash deploy/scripts/run-backlog-cleanup.sh` → 預期 `[FAIL] precheck 不存在` exit 1（順帶驗 override 路徑仍通）
4. 正常環境**語法與列舉段**驗證：`bash -c 'source <(sed -n "1,/^while/p" deploy/scripts/run-backlog-cleanup.sh | head -n -1)'` 之類不觸發清卡迴圈的形態，或直接目視＋bash -n；**禁直接執行完整腳本**（無 dry-run flag）
5. mosaic 原 override 行＋依賴註解逐字保留（diff 對帳）

## 範圍外（勿順手）
- 結構升級（twin drift 機械檢查掛 ai-rules sync-sources/夜掃）＝ai-rules 側另卡——修完回報，ai-rules 側決定要不要做
- ai-rules 側腳本任何改動
- mosaic 其他 deploy/launchd 設定

## 建議執行 tier／workspace／卡歸屬
- tier：lite 可（合併規格已定死）；workspace：`~/Github/mosaic_alpha`（main WT，卡 branch 慣例依 mosaic 側）；卡歸屬：小 doc/script fix 依 mosaic 慣例（免卡或小卡自行判斷）

## 完成回報
修完跟 ai-rules 側說一聲（F4 閉合＋兩段 guard 實證輸出）——ai-rules 的 AIR-70 卡面已留「F4 跨 repo 另案」註記等銷帳。
