# AIR-76 S0 Kit：MVP seeded fault-injection 備料（v3.1 測試契約）

> 備料者：air-76 worker（2026-09-15）。**實驗執行歸 marshal 編排——本 kit 不跑任何 LLM 腿。**
> EP 依據：`ai-analysis/_tasks/2026-09/09-11-test-contract-v31/ep.md` S0 段（素材規格／四軸量測／預凍結過線）。
> 誠實邊界（EP 原文約束）：MVP 量的是**已知壞樣的 discriminating power**，禁外推為 production 有效性宣稱；個位數樣本只判靈敏度。
> 起手式修訂：EP 的「rg v3.1 rules/model-routing.md 止血確認」**作廢**——AIR-91 改寫 rule 後止血失去客體（詳 drift-audit.md S1 節）；S0 開跑前置改為「S1 機械驗證全綠」＋本 kit 在場。

---

## 0. 預凍結過線標準（EP 定稿即凍結——跑之前不得改，防事後合理化）

| 軸 | 標準 | 量法 |
|---|---|---|
| Lane A challenge recall | oracle mutant 抓到 **≥ 3/4** | 逐份 verdict 對 answer key（§2 末） |
| Lane A clean 誤報 | **≤ 1** | clean 份被標缺陷數 |
| Lane B routing | 六類 mutant 至少 **5/6** 被預期路由的軸抓到 | 依 §3 expected-routing 表逐類判 |
| Lane B escalate | 混入的 oracle mutant（TC-A8 形態）被**標記轉介 challenge** 而非硬吞 | §4 步驟 ⑤ |
| attribution | 每 caught mutant 歸因正確 **≥ 5/6**（歸因錯＝有抓到但指錯機制） | 對 answer key 機制欄 |

任一軸不過線 → **S2-S7 全凍結（僅 S1 可跑——S1 已完成）**，blueprint 保持 ⚠️，fail-loud 回報 user（SM-11）；協議修正候選記入 mvp-report。

---

## 1. Lane A：8 份迷你 TC（盲 derive 標本）

題材：會計/單位邊界形態（張↔股換算／除權息調整／時區跨界）——自構迷你 TC，不跨 repo 寫入（mosaic mutmut spike 取形態不取素材）。

### 1a. 投餵面（A1 盲推 prompt 用——僅此四欄，oracle 欄禁入）

> 投餵順序洗牌固定如下（防「clean 連排」pattern 洩露；順序寫死保重現）：
> **A3 → A6 → A1 → A8 → A5 → A4 → A7 → A2**

- **TC-A1** claim：部位記錄以「張」輸入時，系統持股數＝張×1000。Given-When：輸入 3 張 → 呼叫部位換算。
- **TC-A2** claim：現金股利 D 的除息參考價＝前收盤價減 D。Given-When：前收盤 500.0、D＝12.0 → 計算除息參考價。
- **TC-A3** claim：成交紀錄按 Asia/Taipei 午夜切日歸屬交易日。Given-When：兩筆成交 2026-09-14T23:59＋2026-09-15T00:01（皆 Taipei）→ 歸日。
- **TC-A4** claim：除權息調整後，調整價序列在除權息日不產生人為跳空（前日值按係數同比例回調）。Given-When：參考價 95.0、前收盤 100.0（係數 0.95）、前日原始序列值 98.0 → 計算前日調整值。
- **TC-A5** claim：現金股利 D 的除息參考價＝前收盤價加 D。Given-When：前收盤 500.0、D＝12.0 → 計算除息參考價。
- **TC-A6** claim：部位記錄以「張」輸入時，系統持股數＝張×100。Given-When：輸入 3 張 → 呼叫部位換算。
- **TC-A7** claim：切日規則「timestamp ≤ 午夜整點屬當日」。Given-When：一筆 2026-09-15T00:00:00（Taipei）→ 歸日。
- **TC-A8** claim：調整價計算正確。Given-When：任意輸入 → 驗證輸出與實作 `adjusted_price()` 回傳值一致。

### 1b. 答案面（僅進 A2 reveal 與 marshal 計分，禁進任何 spawn prompt）

| TC | verdict（answer key） | 缺陷機制 | 證據行 |
|----|----|----|----|
| A1 | clean | — | oracle_source＝台股交易單位慣例（1 張＝1000 股，領域恆等式） |
| A2 | clean | — | oracle_source＝交易所除息參考價公式（規格） |
| A3 | clean | — | oracle_source＝市場交易時段規格（日界＝台北午夜） |
| A4 | clean | — | oracle_source＝調整序列恆等式（98.0×0.95＝93.1） |
| A5 | **oracle mutant** | oracle 公式錯側（＋應為 −；正確參考價 488.0 非 512.0） | oracle_source 宣稱規格但與規格反向 |
| A6 | **oracle mutant** | 單位換算係數錯（100 應為 1000——他市場單位混入） | oracle_source 宣稱慣例但屬性錯置 |
| A7 | **oracle mutant** | 邊界 off-by-one（午夜整點應屬次日；「≤」造成錯側/雙重歸屬） | 無獨立源佐證錯側——self-serving 邊界 |
| A8 | **oracle mutant** | oracle_source 指向待測實作（**圓形依賴**——Critical 級） | oracle 即 impl，無獨立真相源 |

challenge 協定（EP S0-3）：跨家族 advisory、fresh context；**先自行推導各 TC 的正確 oracle（數值＋predicate）→ 收答案後才 reveal（1b 表）→ 逐份 verdict＋每個 mutant 產 falsifiable 探針**＋completeness 檢查（指出 8 份之外漏掉的場景）。

---

## 2. Lane B：六類 test 架構 mutant 標本（pytest 形態）

> 投餵面＝下方代碼塊＋一句「審查以下測試變更」；**mutant 標籤與 expected-routing 表禁入 prompt**。

- **M-1**（幽靈斷言升級形）：
  ```python
  def test_ex_div_reference_price():
      result = reference_price(prev_close=500.0, dividend=12.0)
      assert result is not None        # 斷言與 TC predicate（488.0）脫鉤
  ```
- **M-2**（同義反覆）：
  ```python
  def test_reference_price_matches():
      assert reference_price(500.0, 12.0) == reference_price(500.0, 12.0)   # oracle 即 impl
  ```
- **M-3**（evidence fidelity 缺陷）：
  ```python
  def test_adjusted_series_uses_factor(mocker):
      mocker.patch("pricing.factor_api", return_value=0.95)
      assert adjusted_series([98.0]) == [93.1]    # 期望值僅由 mock 值推導——驗的是 mock 透傳
  ```
- **M-4**（shared dependency 污染）：
  ```python
  _portfolio = {}
  def test_add_board_increases():
      _portfolio["tsmc"] = 3
      assert shares(_portfolio) == 3000
  def test_sell_all_clears():
      _portfolio.clear()                          # 依賴前測殘留與執行順序
      assert shares(_portfolio) == 0
  ```
- **M-5**（符號≠路徑）：
  ```python
  from pricing.internal import _convert           # 直接 import 私有符號
  def test_pipeline_output():
      assert _convert(3) == 3000                  # 未驅動 pipeline/CLI 消費路徑
  ```
- **M-6**（層級失衡）：
  ```python
  # 變更背景：PositionAggregator（跨 pricing＋ledger 兩模組的整合器）
  def test_aggregator_pure_math():
      assert PositionAggregator.sum_positions([]) == 0
  def test_aggregator_single():
      assert PositionAggregator.sum_positions([Position(qty=1)]) == 1   # 全 unit——整合面零覆蓋
  ```

### expected-routing 表（預凍結——EP S0-2 原文，跑前寫死）

| mutant 類 | 預期路由 | 備註 |
|---|---|---|
| M-1 幽靈斷言 | audit（機械對帳項 1 抓） | |
| M-2 同義反覆 | **audit 抓到後 escalate challenge**（oracle 類 specimen——圓形依賴面） | 機械層 audit 命中、判定屬 oracle 級 |
| M-3 evidence fidelity | review（軸B）＋audit（mock↔evidence class）**雙命中可接受** | |
| M-4 shared dependency | review（軸B shared dependency 項） | |
| M-5 符號≠路徑 | audit（對帳項 7→角度 4 引用） | |
| M-6 層級失衡 | review（軸B 層級平衡項） | |

---

## 3. 量測協定（腿、順序、隔離）

### 腿的建議（spawn tier 口徑＝EP F19 裁定：部署面真實配置，非主 session full 模擬）

| 腿 | 載體 | 考什麼 | call 數 |
|----|------|--------|---------|
| Lane A challenge | **bridge `task --family muse`**（跨家族 advisory·fresh context——EP 指名） | blind derive→reveal＋falsifiable 探針＋completeness | ~2 |
| Lane B audit 形態 | **in-harness registry spawn lite**（`glm-5.3-flash`；對應部署面機械驗證/consistency gate 的 lite 口徑——lite-verify preset 同級） | 機械對帳（攜帶 v3.1 角度 8 七項候選檢查項文本＋既有角度 1/4 引用語） | ~1 |
| Lane B review 形態 | **in-harness registry spawn code-reviewer preset**（`glm-5.3-flash`——部署面 review agent 層 lite 預設口徑） | 架構面（攜帶軸B 六項候選檢查項文本） | ~1 |

- 檢查項文本：直接取 EP S2/S4/S5 段的候選文本（「MVP 用的文本即落檔文本的候選」——EP 語義約束）；發現檢查項缺陷回饋 S2-S6 修正。
- **隔離**：audit 腿與 review 腿互不見對方輸出（防串供）；兩腿與 Lane A 亦隔離（各自 fresh context）。
- 實驗形態明示：in-harness lite 口徑量的是**部署面** discriminating power；muse 腿量的是 challenge 的跨家族形態——兩者能力檔不同，報告須分開陳述不得混算。

### 順序

1. 素材凍結：本 kit §1-§2（answer key／expected-routing 已寫死）
2. Lane A：盲推投餵（§1a 洗牌序）→ 收推導答案 → reveal＋逐份 verdict
3. Lane B：audit 腿＋review 腿（可平行，互不見）
4. escalate 驗證：取 **TC-A8 的 oracle 描述**混入 Lane B 餵 audit/review → 預期標記轉介 challenge 非硬吞
5. 四軸計分（對照本 kit 答案面）→ 過線判定
6. 產出：素材與 verdict 複製任務家 `ai-analysis/_tasks/2026-09/09-11-test-contract-v31/mvp/`；報告寫 `ai-analysis/_tasks/2026-09/09-11-test-contract-v31/mvp-report.md`（素材清單＋逐份 verdict＋四軸數字＋過線判定＋協議修正候選）

### 計分規則

- routing 判定依 expected-routing 表逐類：該類被預期軸抓到＝1（M-3 雙命中任一即計）；attribution＝caught 份的機制歸因與答案面「缺陷機制」欄一致（如 M-2 被抓但歸因「斷言太弱」＝歸因錯）；誤報＝clean 標本（Lane A 的 A1-A4）被標缺陷。
- **禁逐字洩漏**：spawn prompt 只帶（a）檢查項候選文本（b）標本本身。以下**皆禁入 prompt**：expected-routing 表、答案面、mutant 標籤、clean/mutant 分佔比、過線標準、對其他腿結論的引用。

---

## 4. 過線後與不過線後

- **過線**：回報 marshal 放行 S2-S7（凍結解除權在 marshal／user；本 worker 不自行解凍）。
- **不過線**：SM-11——S2-S7 全停、blueprint 保持 ⚠️、回報 user；修正候選（blind-derive 加錨定防護、檢查項加細、routing 表修）記 mvp-report，禁邊跑邊改協議（跑前凍結紀律）。
