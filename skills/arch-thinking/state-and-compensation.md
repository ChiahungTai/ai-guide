# State、ownership 與補償關係

由 [arch-thinking](SKILL.md) 的觸發表載入。修復與刪除查補償；觸及 mutable state 或 ownership 時另查寫入路徑。兩者可共用證據，不能互相替代。

## 補償邏輯盤點

引用圖不保證找得到補償關係：B 可能讀 cache 或中間產物，依賴的是「A 的錯誤結果」，未必直接引用 A。修 A 卻保留 B 可能 double-count；刪 B 可能使 A 的缺陷復活；刪 A 可能讓 B over-correct。

1. 定位變更的量、轉換或狀態，以及產生→修正→消費的相關路徑。搜尋範圍從這些路徑開始，包含被刪除側，不全 repo 無差別掃。
2. 用補償訊號定位候選：`offset|compensate|workaround|FIXME|hack|手動補|抵銷`、同量的加減／重新計算、矛盾註解。關鍵字與註解矛盾只是線索；零命中不能證明沒有補償。
3. 對候選確認實際執行順序、量的定義、正負號與條件，證明是否抵消同一缺陷；必要時查外部框架的實際語義。兩處各算一次不必然錯，須核對契約與分支是否重疊。
4. 確認 A/B 是同一補償關係後，修 authority 與拆補丁作為同一修復範圍。實作驗收須執行完整組合路徑的整合測試或可重播驗證，覆蓋中間資料／cache 與消費端；只讀源碼或只測 A 不算修復驗收。驗證方式見 [validation-strategy](../validation-strategy/SKILL.md)。唯讀 review 記錄必要驗證與未跑限制，不自行越權實作。若跨部署／資料遷移不能原子完成，先定安全的順序與中間態，再執行；不能留下已知重複補償。

真實案例：修漏算 SHORT proceeds 的 compute 後，上游 sizing 仍手動 `+ proceeds`，使 baseline 虛高、風控失效。需驗 compute→中間產物→sizing 的組合，而非只測 compute。

## 變更路徑計數（mutation-path counting）

1. 枚舉相關 state 的 write sites，含欄位原地修改、alias、callback 與可見的持久化入口；逐項列出，不把同 owner 的多處寫入先合成一項。範圍或工具不完整時明列限制，不宣稱總數完整。
2. 區分 state 是跨層 domain invariant，還是 local／optimistic overlay；指出 authority、owner 與生命週期。
3. 分別判定 **ownership 粒度**與 **write-site 粒度**。單一 owning class 可有多個合法寫入位置，但不證明每條路徑或組合都保持 invariant。
4. 查每條路徑的前置條件、並行／重入、ordering、atomicity、失敗與重試；共同 owner 內的 await 或 callback 仍可能產生 lost update。
5. 結論分開寫「誰有權改」與「如何保證改對」，將仍需驗證的組合路徑交 [validation-strategy](../validation-strategy/SKILL.md)。

校準例：單一 class 管理 strategy-local overlay，多個方法更新本身不是違規；兩個方法跨 await 讀改寫同一值，仍需檢查競爭。跨 owner 寫入也不能只憑數量定罪，須核對明確協議與 invariant。
