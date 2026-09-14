# sub+model 派工考古 × Marshal 框架交叉諮詢——圖解說明

> 本文是 [2026-09-14-sub-model-marshal-cross-consult.md](2026-09-14-sub-model-marshal-cross-consult.md) 的人類 viewport（mode D 圖解沉澱）。人判讀聚焦三問：**結構撐得起嗎**（對照節三必寫）、**在重造嗎**（單一源指針形態）、**方向對嗎**（待裁三項）。顧問材料非結論，Arbiter＝user。

## 1. 雙輪三家諮詢流程總覽

```mermaid
flowchart TD
    A["考古材料<br/>flash agent 報告 P1-P17<br/>＋Marshal 框架貼文"] --> B["Round 1<br/>三家同一工單<br/>全量材料＋Q1-Q4"]
    B --> M1["muse<br/>逐項錨點表"]
    B --> C1["codex<br/>17 項分類"]
    B --> G1["GLM-5.3<br/>頭部遭截斷"]
    M1 --> X["caller 交叉分析<br/>＋機械驗證 17a4fff<br/>修正工單兩條過時判定"]
    C1 --> X
    G1 --> X
    X --> D["Round 2<br/>摘要＋錨點工單<br/>（payload 教訓當場採納）"]
    D --> M2["muse<br/>糾錯 caller 兩處"]
    D --> C2["codex<br/>自列三項修正"]
    D --> G2["GLM<br/>補齊 D1-D4 判定"]
    M2 --> E["二次收斂<br/>分歧全數終結"]
    C2 --> E
    G2 --> E
    E --> F["報告<br/>ai-analysis/reports/"]
    F --> H{{"user 裁決<br/>待裁三項"}}
```

## 2. 17 模式覆蓋判定地圖

```mermaid
flowchart LR
    subgraph COV["已覆蓋 16 項"]
        direction TB
        subgraph EARLY["早期條文化 9 項"]
            A1["P1 旗艦裁決外派"]
            A2["P5 影像 flash"]
            A3["P6 背景跑"]
            A4["P7 調查 fan-out"]
            A5["P9 effort 對譯"]
            A6["P10 額度 failover"]
            A7["P12 codex 時機"]
            A8["P15 派發透明"]
            A9["P17 機械段派 lite"]
        end
        subgraph NEW["17a4fff 落地 7 項<br/>（09-14 15:46，標 air-91）"]
            B1["P2 fleet 預設 lite"]
            B2["P3 標準收斂鏈<br/>post-build SKILL"]
            B3["P4 顧問兩層語義"]
            B4["P8 主 session 不實作"]
            B5["P13 顧問共識授權<br/>deep-work SKILL"]
            B6["P14 arc 內改判"]
            B7["P16 對抗驗證 opt-in"]
        end
    end
    VAC["真空 1 項<br/>P11 Marshal 六角色框架<br/>rg 全庫零命中"]
    VAC ==> LAND["落地收斂載體<br/>agents/AGENTS.md 角色模型對照節"]
```

> 計數註：報告 TL;DR 沿 muse prose 記「15 已覆蓋」；按 muse 逐項表實為 **16 已覆蓋＋1 真空**（prose 係算術 slip，表為準）。P3／P13 由 caller＋GLM＋muse 三方獨立錨定，codex round-2 修正認可。

## 3. Marshal 六角色 → 現行載體（對照節提案核心）

```mermaid
flowchart LR
    subgraph ROLES["框架六角色（Role 定 What）"]
        direction TB
        R1["Marshal 控場<br/>state／phase／retry"]
        R2["Planner 規劃"]
        R3["Implementer 實作"]
        R4["Reviewer 意見權"]
        R5["Verifier 機械證據"]
        R6["Arbiter 裁決權"]
    end
    subgraph CUR["現行載體（對照節只寫映射，細節各歸其主）"]
        direction TB
        C1["主 session 編排<br/>＋CONFLICT 觸發句（真增量）"]
        C2["主 session EP 直做"]
        C3["impl-lite spawn＋主 session 編排"]
        C4["code-reviewer fresh／primed"]
        C5["lite-verify／cross-verify"]
        C6["judge 鏈位＝主 session full<br/>Arbiter 坐位＝待裁①"]
    end
    R1 --> C1
    R2 --> C2
    R3 --> C3
    R4 --> C4
    R5 --> C5
    R6 -.-> C6
```

**對照節「必寫」共識三條**（三家 round-2 收斂）：

| # | 必寫聲明 | 防什麼 |
|---|---|---|
| ① | 三層同名 disambiguation：功能角色 ≠ registry 載體（impl-lite）≠ 家族 profile（implement） | 第二個「旗艦雙義」 |
| ② | 主 session 兼任兩職：Marshal 職＋Policy 執行者（角色≠坐位） | 把 Marshal 等同主 session 的誤讀 |
| ③ | CONFLICT→Arbiter 觸發句（例外路徑非預設鏈）＋retry/escalation 歸屬 | 現行 contract 表無狀態機的真空白 |

## 4. 分歧終局與待裁事項

**Round-1 分歧 D1–D4 在 round-2 全數終結**：

| 分歧 | 終局 |
|---|---|
| D1 P4 顧問語義 | 已覆蓋（skill:155-159 兩層語義在場）；codex 立場係「標準之爭」非漏讀（muse 糾錯 caller 歸因）；profile/phase 細化＝未來增補候選 |
| D2/D3 P2/P8 | 已覆蓋；「再抽象一層」訴求＝對照節本身（命名不動條文） |
| D4 P16 預設化 | 三家皆反對——對抗驗證價值在稀缺性；維持 opt-in，對照節只陳述「例外路徑」 |

**待 user 裁決三項**（進 AIR-91 討論）：

```mermaid
flowchart TD
    P{"裁決① Arbiter 詞彙與坐位"}
    P --> PA["a. codex 案<br/>以 Judge 取代 Arbiter<br/>（六角色變五＋Judge）"]
    P --> PB["b. GLM 案<br/>Judge＝鏈上 findings 處置<br/>Arbiter＝共識破裂最終裁決＝user"]
    P --> PC["c. muse 案<br/>Arbiter＝主 session 直做<br/>（Decision 四態）"]
    Q{"裁決② verdict 三態 vs Decision 四態"}
    Q --> QA["muse：必寫對齊聲明<br/>（drift 點）"]
    Q --> QB["codex＋GLM：可省<br/>（不引入第二套 schema）<br/>2 比 1 傾向可省"]
    R{"裁決③ 行文取捨（低風險）"}
    R --> RA["retry/escalation：併句 vs 引註 a"]
    R --> RB["Verifier 界線：獨立句 vs 表列帶過"]
```

## 5. 流程自身實證教訓（回流素材）

| # | 教訓 | 證據 |
|---|---|---|
| 1 | 外部 runtime 輸出完整性無預檢 | GLM round-1 頭部截斷：stream／ledger／jsonl 三處一致缺失；muse 盲點預言被實況命中 |
| 2 | 多輪工單「摘要＋錨點」形態有效 | round-2 只帶摘要，三家全數完成表態（GLM 自證受益） |
| 3 | effort 軸不對稱→橫向比較歸因不可靠 | glm bridge 不收 `--effort`；「哪家更深」不可靠，本報告比較面同受此限 |
| 4 | transport 三態表缺 holder-session 死亡行 | muse 建議一行增補（零行為變化） |
| 5 | 三家交叉的價值 | caller 工單兩條過時判定被 GLM／muse 獨立糾錯——單一家族審查會漏的時序差，交叉即現形 |
