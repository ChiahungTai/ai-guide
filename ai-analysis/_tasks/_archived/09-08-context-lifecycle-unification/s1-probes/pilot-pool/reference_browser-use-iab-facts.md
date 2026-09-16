---
name: reference-browser-use-iab-facts
description: ZCode IAB（browser-use plugin）操作事實——fullPage
  截圖不生效（viewport-only）、tab 跨 turn 死亡／session 內重置 about:blank、shadow DOM 只能
  accessibility locator 穿透（page evaluate 看不見）、帶目標入鏡＝locator scrollIntoView＋截圖前驗
  rect（app 自帶搜尋常只過濾側欄、不動看板欄位）、fresh-load domSnapshot＝render 層 vs
  使用者分頁 stale 的責任分離探針
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_d1579c9b-c7ad-4ab0-9720-9afdabc0b951
---

ZCode 內建瀏覽器（browser-use plugin、IAB backend、nodeRepl `mcp__node_repl__js`）實測事實（09-06，board 視覺查驗弧）：

- **`tab.screenshot({fullPage:true})` 無效**：回傳 viewport-only（1280x720）非全頁——目標在摺疊線下就不入鏡（vision agent 會正確回報「無從核實」）。拍下方內容＝先把目標帶進 viewport（UI 過濾或 scrollIntoView）再截 viewport。
- **tab 生命週期不穩**：user turn 之間 tab 可能被回收（tabs.list 空）；也可能 tab 活著但 url 翻成 about:blank（頁面被重置）。每次 js call 先 `tabs.list()` 再綁 id；重任務 goto→定位→截圖塞同一 cell 減少掉窗。
- **shadow DOM 穿透**：Backlog.md web UI 卡片在 shadow DOM——page-context `evaluate(() => document.querySelectorAll("button"))` 找不到，但 `getByRole` locator 與 `domSnapshot()` 看得到（accessibility 層）。DOM 刺探走 locator（`waitFor`/`evaluate` on locator），勿用 page evaluate 全域掃；accessible name（如 `button "Open MOS-47: …"`）是算出來的，不是 aria-label 屬性。
- **找特定 UI 元素優先用 app 自帶搜尋/過濾**（user 提點「用搜尋啊」）——比捲動 hunting 可靠一次到位；Backlog.md board 搜尋框＝`textbox "Search (⌘K)..."`，過濾後單卡入鏡、跨來源卡可比對。注意搜尋可能只過濾側欄結果面板、不動主看板欄位（截圖前驗證過濾是否生效）。
- **render 層 vs 使用者分頁的責任分離＝fresh-load 探針**：新 tab goto→`domSnapshot()`→查 `Open <id>:` 按鈕存在性＋欄位 heading（如 `heading "To Do"`）下的順序走訪——fresh load 有＝render 正常，「看不到」收斂到使用者分頁 stale／view filter（refresh＋查 milestone 檢視/URL 位置/搜尋殘留）；09-06 62/64/65 案四層全綠、純分頁舊。
- **狀態類問題的決定性視圖＝點開卡看詳情面板**（user 提點「點進去就會看到右邊出現狀態」）；關閉控制名稱未知時先 snapshot 取真名——猜 `/Close|Esc|×/` 會 miss，fallback `locator("body").press("Escape")` 亦炸（「Active element is no longer the expected input target」）。
- **截圖存檔＋派 vision-review**：`fs.writeFileSync` 落 `.agent-tmp/` 再派 agent 讀檔——圖不進主 session context；視覺判讀走 vision tier（flash/lite 不做視覺）。見 [[reference-backlog-md-browser-id-mechanics]]（board 端）、[[feedback_subagent-background-spawn]]（背景 spawn）。
