---
id: AIR-79
title: >-
  muse memory 寫入閘道升級 user-scope plugin——一次安裝全 repo
  生效（muse-memory-governance，AIR-54 續弧）
status: Done
assignee: []
created_date: '2026-09-12 01:34'
updated_date: '2026-09-14 01:36'
labels:
  - memory-governance
  - muse-plugin
  - hooks
dependencies: []
references:
  - ai-analysis/_tasks/done/09-12-muse-memory-governance-plugin/ep.md
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕把每個 repo 各自設定的 muse memory inbox hook（擋 muse 直寫記憶池的閘門）升級成裝一次、所有 repo 生效的 muse plugin。設計已收斂（GLM 主 session 架構思考＋codex 對抗討論 09-12、user 拍板），本卡＝建 EP＋實作＋首批 cutover（ai-rules 自身）；現況：設計定案、建 EP 中。

〔baseline：ai-rules fb8760a；設計討論源＝delegate-bridge workspace session（codex advisory bridge job-mtxp38so-dfcac2）；probe scratch＝delegate-bridge .agent-tmp/muse-plugin-probe/（POC 性質，EP 吸收後不依賴該路徑；p2/ 為最小 plugin skeleton）〕

〔已決策勿重辯：①載體＝user-scope muse plugin（muse plugins install --scope user；muse 1.1.1 live 實證 plugin 是 first-class 路徑，無證據 muse 讀全域 hooks.json）②獨立 plugin muse-memory-governance、不搭 delegate plugin（bounded context；不委派也用 muse 的人不被迫裝 delegation；memory policy 不綁 delegate release cadence；delegate 雙 nested manifest 本就被 muse exactly-one 規則拒；一鍵＝bootstrap installer 同裝兩者但兩 identity）③source home＝ai-rules（tests＋memory-audit 消費端＋AIR-54 契約在此）④opt-in marker＝明確版本化 manifest（memory-governance.json＋protocol:1）三態語義——absent→allow 原生／valid+supported→divert／malformed or unsupported→deny＋報錯禁 fail-open；否決「.agents/memory/ presence 即 opt-in」（bootstrap trap：muse add_memory 自建目錄會偽造 marker——codex catch）⑤遷移零 dual-writer 疊窗——plugin 見 legacy .muse/hooks.json memory matcher 在場→自動 no-op（deny short-circuit 未證實，雙跑＝duplicate receipt／edit CAS conflict）；逐 repo cutover 後刪 shim⑥目標契約＝「每個 trusted muse session（含 bridge headless）」；untrusted workspace suppress 是合理安全邊界不繞（否則惡意 clone 放 marker＝user-level execution surface）⑦repo 解析不信 $PWD==workspace root 偶然不變量——stdin 有 host workspace 欄位優先，否則 upward git resolution⑧額外風險（codex）——inbox liveness watchdog／memory-inbox symlink escape／untrusted workspace 中 bare jq+git PATH trust／worktree marker 語義須 explicit 非 cwd-accidental⑨fallback（activation probe 失敗或 overhead 超標時）＝薄 per-repo registration＋單一共享 hook artifact（drift 從兩份完整邏輯縮成 N 份薄接線）⑩arc home＝ai-analysis/_tasks legacy 頂層（AIR-77 遷移時搬）；開工起手式照 AIR-54 慣例補 code-reality snapshot --label AIR-79（首動 ls .code-reality/snapshots/ 確認）〕

〔驗收：cutover gates 全過才切（handoff 定案）——①explicit versioned marker 落地②legacy 共存 no-op 實證③direct＋bridge headless 雙 live activation probe（untrusted suppress 與 bridge plugin-registry 讀取路徑目前 UNKNOWN）④每 tool-call spawn overhead 量測在 budget 內（event-only 無 matcher＝每次 tool call 都 spawn bash+jq）⑤upgrade re-approval probe（approve v1→reinstall v2 不重 approve→hook 是否仍 fire；若重置，headless＝靜默 fail-open 直寫 canonical，須做成 setup health check）。EP 需含四 live probe 段落（marker 檔名/位置與 protocol handshake 欄位／stdin host workspace 欄位／approve-vs-content-hash binding／overhead 量測設計）。首批 cutover 標的＝ai-rules（mosaic_alpha 側 S6 移植由 mosaic 承接）。EP 規劃 M＋C 雙審（codex 已有一輪 advisory 不豁免）。probe scratch 於 EP build+commit 時清除。〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-12 EP 雙審結算〕M 腿 muse-spark-1.3 額度 429（job-mtxq1dvu，窗口 09-14）→ user 指定 GLM-5.3-Flash registry code-reviewer 接腿；C 腿 codex chatgpt-web/high（job-mtxq1dxw-zxv0we）。兩腿 8🔴＋7🟡＋5ℹ️，judge 全數採納回寫 EP（legacy no-op 自我偵測迴圈＝兩腿獨立命中的關鍵根因；activation/in-hook 兩層 invariant；jq-free deny；可逆 handoff；fallback 現在凍結；控制面盤點修正 blueprint×3＋.gitignore）。EP 修訂版待 commit；實作未開工——等 user 觸發。

〔09-12 implement 進度〕S1 結算（03376b5：共享核心＋launcher＋manifest＋42 測試，331 全綠，impl-lite flash 執行＋主 session 獨立重跑驗收）；S2/S3 offline 腿結算（e9e69a7：harness 全流程綠、gate② offline 對照、overhead 7ms/50ms、P-UPGRADE 靜態半＝list 不暴露 approve；machine 復原 no plugins）。**live 腿 L1-L6 parked——muse 訂閱額度 429，2026-09-14T00:00Z 重置**（恢復程序＝poc/poc_activation.md 末段）。S4 cutover 需 gate③⑤ live 證據故暫停。review 腿已提前跑（S1 共享核心資安面先審）：flash code-reviewer＋codex bridge 平行中，judge＝GLM-5.3。manifest 經 install 實證修正（version/description 必填、timeout_ms 不支援）。

〔09-12 鏈結算〕user 指定鏈=implement(flash)→post-build→code-review(flash+codex)→judge(5.3) 已跑至可達上限：S1 結算（03376b5）→S2/S3 offline（e9e69a7）→code-review 雙腿（codex job-mtxsd4ap＋flash code-reviewer；2🔴+4🟡+4ℹ️ 全採納）→judge 裁決＋修正＋12 新測試（f78a763，343 passed；帳本 .review/air-79.md）。**parked at live gates**：S4 cutover 需 gate③⑤ live 證據（muse 額度 429→2026-09-14T00:00Z）；恢復程序=poc/poc_activation.md 末段（L1-L6→凍結 P-WS→gate 判定→S4→S5→post-build 收尾鏈）。branch air-79 四顆 commit 待最終 /commit 確認後收尾。

live 腿 09-14 由 mosaic 端完成（L1-L6 全綠）；收尾四件事由 follow-up 小卡承接（backlog 內 air-91 之後最新一張，title 含「AIR-79 live 腿收尾」）——receipt/patch/條款/同步，證據源＝poc/live_receipt_20260914.md

live 腿 L1-L6 全綠（2026-09-14 mosaic 端執行，receipt 落 poc/），四 gate 終局 PASS，收尾四件由 AIR-92 承接。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
muse memory 寫入閘升級 user-scope plugin（muse-memory-governance）——共享核心＋marker 三態＋origin-mode launcher＋343 測試；雙審（codex＋flash）2🔴4🟡全修；S4-lite cutover（install/approve/marker）＋S5 控制面同步；live 腿 L1-L6 user 豁免，legacy 註冊過渡保留（恢復程序 poc/poc_activation.md）
<!-- SECTION:FINAL_SUMMARY:END -->
