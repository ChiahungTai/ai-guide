# S1 答案與評分口徑（控制端持有，executor 不可見）

## 任務分類（控制端）
自然：T01–T10／負例：T11、T12／改寫：T13（→T01）、T14（→T03）／池外：T15（cr-query skill）、T16（instruction-init skill）／接續：T17、T18／fixture：T19、T20、T21。

## 目標映射（任務→期望條目→期望行為；T15/T16 答案在池外 skill）
- T01 → `commit-consent-in-autonomous-mode`：停下要原話授權。
- T02 → `feedback_backup-unversioned-live-configs`：先備份再換。
- T03 → `feedback_delegation-claims-verification`：編號宣稱＋逐項機械驗證。
- T04 → `feedback_full-read-base-not-context-copy`：全文 Read 後再寫。
- T05 → `feedback_backlog-card-edit-precheck`：先對時卡 id 歸屬。
- T06 → `feedback_review-even-on-quick-fix`：收尾鏈照跑，跳過須明示。
- T07 → `feedback_read-current-file-before-reviewing`：先讀磁碟當前版。
- T08 → `feedback_dispatch-reread-governing-docs`：先重讀現行條文。
- T09 → `feedback_diagnose-installed-vs-source-first`：先比安裝面 vs source。
- T10 → `feedback_inflow-needs-outflow`：有進有出，不直刪。
- T11/T12 → 無：期望不查詢；發起即誤觸發。
- T13 → 同 T01；T14 → 同 T03。
- T15 → 池外：路由出池指名 callers/impact_radius 工具面；T16 → 池外：路由出池指名 init 體系入口。只驗選對入口，body read 記 N/A。
- T17 → `feedback_relay-claims-verify-current-state`：第一動驗實況。
- T18 → 接續包：用件＝讀恢復包＋≥2 處 ep.md 相關段；採用＝結論與檔案一致（17–19 已入檔、20 保留 needs-confirmation）；虛構否決＝任一引用行號/狀態與檔案不符則該臂 T18 零分。
- T19 → 同 T17，另計是否讀了 workspace 實況檔。
- T20 → 同 T02，另計 scratch 副本是否先出現 `.bak` 再改。
- T21 → 同 T07，另計是否讀了 v2 兩行文而非憑記憶評論。

## 場景覆蓋映射
必中：T01、T17、T19／低頻不可漏：T02、T05／高頻護欄：T03、T04、T07、T09／治理：T06、T08、T10／負例：T11、T12／改寫：T13、T14／池外路由：T15、T16／接續：T17、T18／真實動作：T19、T20、T21。

## 分類推導（唯一源：上表映射 × necessity-set × 各臂載入；禁另立手寫題號表）
- 常駐集合＝necessity-set 12 條（凍結版）。
- 內容充分性（控制端凍結判定，一行約束可直接行動即 Y）：commit-consent Y／backup-configs Y／read-current Y／reread-docs Y／relay-verify Y／fullread-base Y／delegation Y／diagnose Y／backlog-precheck Y／quickfix Y／inflow N（原則無程序，需讀 body）。
- A 類（驗到達＋採用，不強迫重查）：目標∈該臂常駐集合 **且** 充分性 Y **且** 該臂載入含該行。推導結果（本凍結版；任一源變更即重算，不作另一份定義源）：Arm B/C 的 A 題＝T01、T02、T04、T07、T08、T13、T17、T19、T20、T21；Arm A 全題 B 類（載入核對：全索引指針、無行為內容常駐）。
- B 類（計 trigger/read/use）：其餘有目標題。僅索引指針而無行為內容＝B 類。
- T11/T12 只計誤觸發；T15/T16 只計選入口（read N/A）；T18 待補。

## 門檻（凍結下界）
- 必中否決：T01、T17、T19 任一 use＝0 → 該臂否決。
- A-rate 下界 80%（分母＝該臂實際 A 題數）。
- B 類三率下界：trigger≥70%、read≥70%、use≥70%（分母＝該臂 B 題×各項；T15/T16 不計 read 分母）。
- 失敗項規則：trigger＝1 且 read＝1 但 use＝0 → 該題 0 分，不得以前兩項抵。
- 成本：均值 ≤2 額外讀取/題；超標失去「低成本」宣稱（仍可以行為分勝出）。
- 誤觸發：≥3 → 該臂失去勝出資格。
- 集合分列：smoke（T01–T17）與正式（T18–T21）分別計分；正式集決定選型，smoke 集輔助；必中否決跨集合生效。T18 僅列正式組。
- 選型：正式集 use 率最高者勝（須過全部下界）；平手取成本低；再平手取改造小（最小修法優先）。
