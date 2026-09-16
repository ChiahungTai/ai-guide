# S0 MVP seeded fault-injection 報告（AIR-76 / v3.1 測試契約）

> 執行：marshal 編排（2026-09-15 深夜～09-16 凌晨）；素材與協定＝[mvp/s0-kit.md](mvp/s0-kit.md)（跑前凍結）。
> 腿口徑：Lane A challenge＝bridge muse（muse-spark-1.3，effort high，fresh＋session 接續兩輪）；Lane B audit＝in-harness lite-verify（glm-5.3-flash）；Lane B review＝in-harness code-reviewer（glm-5.3-flash）——皆部署面真實配置（EP F19 口徑），三腿互不見對方輸出。

## 四軸計分（預凍結標準對照）

| 軸 | 門檻 | 實測 | 判定 |
|---|---|---|---|
| Lane A challenge recall | ≥3/4 | **4/4**（A5 符號反轉／A6 係數錯／A7 off-by-one／A8 循環依賴全數盲推抓到） | ✅ |
| Lane A clean 誤報 | ≤1 | **0**（A1–A4 全判 clean，推導值 488.0/3000/93.1/日界全正確） | ✅ |
| Lane B routing | ≥5/6 | **6/6**（見下表；M-3 由 audit 腿依「任一即計」計入——review 腿漏檢，勿以 6/6 解讀為六類皆雙腿命中） | ✅ |
| Lane B escalate（TC-A8 混入） | 轉介非硬吞 | audit＝Critical＋「escalate challenge 轉介」✅；review＝Item 4 Important 不吞 ✅ | ✅ |
| attribution | ≥5/6 | **7/7**（每個 caught 標本的機制歸因與答案面一致） | ✅ |

**過線判定：PASS——S2–S7 凍結解除。**

## Lane B routing 明細

| mutant | 預期軸 | 實際 | 計分 |
|---|---|---|---|
| M-1 幽靈斷言 | audit 項1 | audit 項1 finding（無 TC-ID＋斷言無語義） | ✅ |
| M-2 同義反覆 | audit 項3→escalate | audit 項3 Critical＋escalate 轉介 | ✅ |
| M-3 evidence fidelity | review 項4＋audit 項2（任一即計） | audit 項2「oracle 由 mock 值推導非獨立源」需查證（依其誠信約束交下游）；**review 判 clean＝漏** | ✅（依「任一即計」，附 review 漏檢註記） |
| M-4 shared dependency | review 項5 | review 項5 Important（order-dependent flake 機制）；audit 項6 亦抓到 | ✅ |
| M-5 符號≠路徑 | audit 項7→角度4 | audit 項7 轉介 angle 4 | ✅ |
| M-6 層級失衡 | review 項2 | review 項1＋項2（拓撲不對稱＋unit-only for integrator，附條件升級 🔴 判準） | ✅ |

## Lane A falsifiable 探針（reveal 後產出）

A5-SIGN（488.0 vs 512.0）／A6-UNIT（3000 vs 300 股）／A7-MIDNIGHT（半開區間歸屬＋23:59:59 對照）／A8-CIRCULAR（樁 impl 回錯值仍綠燈＝零檢測力實證）。全交 [laneA-muse-round2-reveal.json](mvp/laneA-muse-round2-reveal.json)。

## 誠實邊界與協議修正候選

1. **量的是已知壞樣 discriminating power**（裁決 §6 原文）——個位數樣本，不外推 production 有效性；不宣稱統計等價。
2. **review 腿 M-3 漏檢**：軸B「evidence fidelity」候選文本在 lite tier 對「mock 值參與期望值推導」形態未觸發（判 clean＋僅 🟢 inferred 提示 patch 綁定風險）。修正候選：S5 落檔時把項 4 文本加機械觸發問句「mock 回傳值是否參與期望值推導链」。
3. audit 腿 C4/C5（receipt／基線跑法）本輪無材料——七項的 receipt/digest/BEFORE_GREEN 半邊未經 MVP 驗證（S3/S4 落檔後首個真實弧補驗）。
4. Lane A completeness 品質高（除權合併公式／零股單位／UTC 轉換／因子連乘／退化輸入五項）——挑戰腿的 completeness 檢查有實效。
5. 計分解讀已跑前凍結：escalate 主要 credit 歸 audit（項 3 文本自帶轉介語彙）；review 以「不硬吞」為門檻——兩腿皆過。

## 素材清單

| 檔案 | 內容 |
|---|---|
| [s0-kit.md](mvp/s0-kit.md) | 跑前凍結的素材＋協定＋過線標準 |
| [laneA-muse-round1-blind.json](mvp/laneA-muse-round1-blind.json) | muse 盲推全文（job-mu2vonr8-gh52ev） |
| [laneA-muse-round2-reveal.json](mvp/laneA-muse-round2-reveal.json) | reveal 後 verdict＋探針（session 01a0a5de-b578-7c63-b3c0-9a48f6a12bd2 接續） |
| [laneB-audit-transcript.jsonl](mvp/laneB-audit-transcript.jsonl) | lite-verify 腿逐字 transcript |
| [laneB-review-transcript.jsonl](mvp/laneB-review-transcript.jsonl) | code-reviewer 腿逐字 transcript |
