# 規劃交付驗證

## 文件與審查

- 完整 EP 已逐段檢查自洽、責任邊界、引用與情境對應；六項外部 findings 經 current sources 核對、修訂、原 reviewer followup，全部 resolved。
- 初審 `job-mu2dzpyw-geyy61`、followup `job-mu2e7wgx-ffgcbp` 均 completed／exit 0，原始輸出在同目錄 JSON。沒有仍待收回的工作。
- 靜態檢查實跑 `uv run python`：Markdown／HTML 本地連結存在、HTML id 唯一、導航 fragment 指向有效 section、無未替換 placeholders、兩份 review JSON 可解析且有 finalText，全部 PASS。
- EP projection SHA256：`f4a7c8f920cf6e72d20106de0f7456b0aed684f85b2c1a573a3d23d17df905a2`；HTML 兩個來源欄位同步。
- consistency 檢查對象為 ep.md（全文＋修訂），沒有用自查取代獨立審查。sources 的 path:line 為基線導航起點，實作前仍需重定位。

## 明確限制

- CUA 開啟本機 file URL 被 browser security policy 拒絕。依該政策沒有嘗試 localhost／其他瀏覽器繞道。互動導航、折疊、hash restore 與獨立視覺驗收 **未完成**。
- 純規劃產物；S1–S4 behavior 實驗、真實 pilot、各端部署驗收均尚未執行。未跑既有全套 pytest，未將 AIR-91 歷史測試自報為本輪實跑。
- 首輪 reviewer 未全文重讀背景七份報告；本輪由主 session 閱讀報告、Reviewer 核對 EP 與 current workflow sources，followup 僅驗六項修訂與直接矛盾。
- 曾成功讀取原 ZCode session 尾部，並核對 user 指定 commit；沒有假稱恢復整個歷史。

## 交付狀態

完整 EP 審查收斂，可以評估是否採用。HTML 是附帶閱讀版，渲染驗證受限；新流程未實作，沒有 commit／deploy，也未動 AIR-96 既有 dirty。

## Marshal 增補後的最終驗證

- 增補調查 `job-mu2fgaqy-d9l930`、followup `job-mu2fn09e-d6vjf8`、closure `job-mu2fstmq-gouh8l` 全部 completed/exit 0 並回收。closure 三個漏洞修訂全 resolved，無新增 Important；M1–M4 限計畫修訂 verified。
- 最終 EP SHA256：`4cd321a32d8bc4bb4d95951ea97e5f803f4f37f933fae5f12960f9e9c42a701e`，取代上方初版 projection hash；HTML 兩處已同步。
- 實跑 `uv run python` 靜態核對：所有規劃 Markdown 本地連結、SM-01–24 連續且唯一、UTF-8 無 replacement 字元、三份增補 review JSON completed 且有結果、HTML hash 同源，全部 PASS。
- user 明示 HTML 互動／視覺驗證先不用做；本輪只同步文字，不再列為規劃未完成。runtime/behavior/pilot/成本效果交實作 LLM 驗收，沒有報作本輪 PASS。
- 複核最後一輪只核 EP 文字閉合，沒有重讀 current source；source 核對來自前兩輪及主 session，實作前仍須按最新現況重定位。

## /consistency 修復後的 hash 更新

- 上方 `4cd321…` 是增補 closure 當下的驗證快照（已封存，不改寫；對應 `56397e5` 版 EP）。其後 /consistency 修復改動 ep.md（錨點訂正 6 處：:130→:141×2、:79→:76–80×3、:85→:56、:25→:28；簡體回正 6 處；無計畫語義變更），EP 現版 SHA256：`5b8f9300a5de3ce605a2fe60576e3c1f6fe235b10149b4d9f83b7a7ef8268001`。
- HTML 兩處 projection 欄已換為現版 hash；HTML 內文不含被改字串，無需重產文字。接手核對以現版 hash 為準。
