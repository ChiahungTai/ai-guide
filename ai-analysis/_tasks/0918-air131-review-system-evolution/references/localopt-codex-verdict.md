你的三子題確實可以統攝，但我會把命題稍微修正：

> **共同病因不是單純「feedback loop 太長」，而是「決策到獨立證據的距離太長」，再加上 local opt 特有的「目標函數本身從未重新開放」。**

所以只做更快的 feedback 仍不夠。需要 **雙迴路**：內圈快速證偽；外圈定期解凍既有決策。

* * *

## 1\. Local opt：問題不是錯，而是「每一步都對，整體卻越來越怪」

逐弧模式本質上是一個 constrained local search：

```
目前系統 Sₙ
  ↓
接受既有決策 D₁...Dₙ 為 constraint
  ↓
找這一弧最佳修改 Δₙ
  ↓
Sₙ₊₁
  ↓
新決策再次 freeze
```

最危險之處正是：**每個 Δ 都可能合理。**

它會產生幾種很典型的形態。

| Local-opt 形態 | 表面看起來 | 全局問題 |
| --- | --- | --- |
| 儀式棘輪 | 每次事故多一個 gate | gate 只加不減，正常路徑越來越長 |
| 邊界複利 | 保護既有 boundary 很穩健 | adapter / exception / projection 不斷疊 |
| 詞彙分叉 | 每處定義局部都合理 | 同一概念有近義但不完全相同的 authority |
| 決策資本化 | 「這題已裁決，不重辯」節省 context | 暫時決策逐漸變成不可質疑的結構 |
| YAGNI 存量化 | 當初每個機制都有 failure case | failure mode 已消失，機制卻永久存在 |
| 自洽陷阱 | parity / consistency 全綠 | 只證明目前規則互相一致，不證明規則集合值得存在 |

這很接近 **single-loop / double-loop learning** 的差異：

```
single-loop:
規則是對的嗎？ → 有沒有遵守？

double-loop:
我們為什麼要有這條規則？
當初的假設今天還成立嗎？
如果今天從零開始，還會這樣設計嗎？
```

你現在的日常 gate 大多很擅長 single-loop。大審的獨特價值，就是重新開 double-loop。

### 哪些可以連續感測

我不建議做一個「architecture health score 73.2」。那很快會 Goodhart。

比較適合的是幾個彼此異質的 alarm：

| Signal | 可操作量測 |
| --- | --- |
| **Correction recurrence** | 同一 concept / authority 在最近一段 arcs 被 corrective 修改 ≥2 次 |
| **Ritual load** | 正常任務 mandatory lookup/read/action hops 持續上升；或連續新增 mandatory gate 而沒有合併/刪除 |
| **Semantic divergence** | 同一概念出現多個 live authority、alias、exception wording |
| **Boundary interest** | 同一種修改反覆需要跨多個 control surfaces 才能完成，且原因是責任重疊 |
| **Consumer friction** | fresh agent 需要 workaround、走錯入口、錯 resume point、需要額外 human clue |

尤其我會重視 **derivative，而不是 absolute size**。

例如 20 個 skill 不一定有問題；但：

```
12 → 15 → 19 → 24
```

而每次新增都解釋成「避免上一個問題再次發生」，這就很像 ritual ratchet。

### 哪些東西連續 sensor 永遠看不出來

有些問題必須靠 discontinuous probe。

最有效的三種：

1. **Zero-based rewrite thought experiment**  
   不真的 rewrite。只問 fresh reviewer：「如果今天只有需求與 failure history，不給現有架構，你會怎麼設計？」
2. **Cross-family challenge**  
   不要求 reviewer 尊重所有歷史裁決；要求它把 frozen decisions 視為可質疑假設。
3. **Consumer inversion**  
   fresh agent 只拿真實 consumer task，不告訴它 ai-guide 的內部 topology，看它自然走到哪。

這三個共同點都是：

> 暫時拿掉歷史路徑依賴。

所以它們不是一般 lint 可以取代的。

* * *

## 2\. 我會用「升溫 state machine」，而不是固定 architecture score

可以先用一個很小的版本。

觀察 window 用最近 **8 個治理相關 arcs**。追五個 signal family：

```
R = correction recurrence
G = ritual growth
V = vocabulary / authority divergence
B = boundary compounding
U = consumer friction
```

初版 trigger 我會這樣設：

| 狀態 | Trigger | 動作 |
| --- | --- | --- |
| **Cool** | 0–1 family active | 正常逐弧工作 |
| **Warm** | 同一 window ≥2 families；或同一 family 連續兩個 window 出現 | 對該 bounded area 做 reheat review |
| **Hot** | ≥3 families；或 tripwire | 進入 full-system / full-arc review |
| **Cooldown** | review 後連續一段 arcs 無 tripwire 且 <2 signals | 回 Cool |

Tripwire 不經過計分，直接 Hot。我會至少放三個：

```
1. 大審找到一個此前 daily machinery 沒抓到的 systemic Critical
2. authoritative semantics 實際出現互斥定義
3. ≥2 個獨立 consumer dry-run 因同一設計問題失敗
```

Warm 時不要立刻「再加一個 gate」。

Warm 的意思應該是：

> **這個區域現在禁止只用 additive repair 思考，必須同時產生 delete / merge / boundary rewrite 候選。**

這一點很重要，否則「偵測 complexity → 新增 complexity detector → 再新增 detector gate」，自己就變成 local opt。

可以把它想成 simulated annealing 的類比：

```
Cool:
    既有決策大致 frozen，快速 exploitation

Warm:
    部分歷史決策重新可議

Hot:
    允許跨 boundary、刪機制、重新分權、重建 vocabulary
```

這只是心智模型，不需要真的算 optimization energy。

* * *

## 3\. 大審 cadence：我會選 hybrid，而且「arc 數」比日曆更重要

純 calendar 不理想：

```
很忙的兩個月 → 可能累積 30 arcs
很閒的兩個月 → 只有 2 arcs
```

local opt 的累積量主要跟 **decision count / arc count** 有關。

但純 signal trigger 也不夠，因為 sensor 本身可能與系統共享 blind spot。

所以應該是：

```
event trigger
     +
arc-count ceiling
     +
calendar sanity check
```

例如可以把 **12 個治理 arcs** 當初始 full review ceiling，而不是說 12 一定正確。之後讓實際逃逸結果調 cadence。

### 「Critical escape」非常適合做 self-calibration，但不要當 KPI

我會明確定義：

> Escaped Critical = 在 full review 發現、在 review 開始前已存在，而且現行日常機制沒有把它升格為 Critical 的 systemic defect。

它和「review 找到 Critical」不完全相同。

例如 reviewer 新發明一個更嚴格標準，第一次套用發現問題，不宜直接算成過去 sensor 的 escape。

調節規則可以非常簡單：

```
初始 interval = 12 arcs

出現 systemic escaped Critical:
    next_interval = max(6, interval × 0.5)

連續兩次 full review：
    0 escaped Critical
    + review coverage 沒下降
    + heat 大致維持 Cool
→ next_interval = min(24, interval × 1.5)

其他情況:
    interval 不變
```

我刻意讓它 **慢慢降頻、快速升頻**。

因為 false-negative Critical 的成本遠高於多跑一次 review。

### 這個 feedback loop 最大的陷阱

「零 Critical」可能代表兩種完全相反的事：

```
A. 系統真的健康
B. review 變弱了
```

所以 zero-Critical streak 只有在 **review power 沒下降** 時才有資格拿來降頻。

至少要維持：

```
scope 可比
review taxonomy 可比
fresh-context independence 可比
異構 reviewer 覆蓋沒有縮水
```

如果從你這次的 6 異構腿縮成同一家一腿，下一輪零 Critical 不應該讓 cadence 降低。

因此我會把 Critical escape 當成 **thermostat sensor**，不是 performance metric。

不要設定「我們的目標是 Critical=0」。

否則下一步很容易發生：

```
Critical → Important
Important → Suggestion
```

數字很好看，系統沒變好。

* * *

## 4\. 「寫到一半才知道不可行」：把 feasibility 從 implementation 拉到 hypothesis 層

這類問題很適合加入一個非常小的 EP section：

> **Load-bearing assumptions / kill criteria**

不用列十幾項，只寫真的會讓方案死亡的 1–3 個假設。

格式最好是機械可判：

| 欄 | 問題 |
| --- | --- |
| Assumption | 方案成立必須為真的事情是什麼？ |
| Probe | 最便宜的證偽方法是什麼？ |
| Kill observation | 看到哪個客觀結果就停止？ |
| Action | kill approach、pivot，還是拆 research arc？ |

例如差的 kill criterion：

> 如果實作太複雜就重新評估。

這不可否證。

好的形式：

> 若 target harness 無法在 real runtime 提供 required interception point，且唯一替代需要 second authoritative state，停止此 approach。

或者：

> 若 fresh-agent consumer test 在兩個 consumer repo 都需要 undocumented human hint 才找到 authority，這個 information architecture 不進 production。

關鍵是 **kill criterion 必須在投入大量 implementation 前寫**。

否則很容易變成事後合理化。

### Spike 不要用「做到有答案為止」

AI 對 wall-clock timebox 並不是很好的控制單位。

我反而會用 **evidence budget**：

```
一個 load-bearing assumption
→ 一個 disposable spike
→ 最多 2–3 個判別性 probes
→ 不做 production refactor
→ 不順便把東西做好
```

到 budget 邊界仍然不能證明 feasibility：

```
UNKNOWN
```

就是一個合法結果。

不要變成：

> 都研究這麼多了，不如直接實作看看。

那正是 sunk-cost transition。

### 止損弧要變成「成功終態」

這一點甚至比 kill criterion 本身重要。

現在很多開發流程潛意識只有：

```
implemented = success
abandoned = failure
```

這一定會鼓勵硬撐。

我會改成：

```
Arc terminal outcomes:

DELIVERED
INVALIDATED
SUPERSEDED
```

`INVALIDATED` 的成功條件是：

```
原假設
→ falsifying evidence
→ kill decision
→ 可重用 learning
→ 沒有留下半套 production mechanism
```

也就是：

> **被證偽的方案不是 failed arc，而是 uncertainty retired。**

甚至可以追一個很有價值的量：

```
cost-to-disproof
```

理想趨勢不是「永遠沒有 kill」。

反而是：

> 會死的方案死得越來越早。

* * *

## 5\. 「做完才知道難用」：fresh-agent consumer dry-run 應該正式成為 semantic UX test

你的兩個 repo 實驗已經示範了它真正測的是什麼：

不是 instruction 文法，也不是 consistency。

它測的是：

```
Given real consumer state + real task
Can a fresh agent discover the intended control surface
and reach the correct next action?
```

這是 instruction 系統真正的 UX。

我會把標準 dry-run 固定成四類 task：

| 類型 | 測什麼 |
| --- | --- |
| Cold navigation | 不給路徑提示，能不能找到正確入口 |
| Normal task | happy path 能不能正確執行 |
| Ambiguous/conflict task | 多個看似合理來源時選哪個 |
| Resume task | fresh session 能不能從 durable state 找到 resume point |

這裡最重要的控制變數是：

> prompt 只能描述 consumer goal，不可以順便提示 instruction topology。

否則會把 discoverability bug 藏掉。

* * *

## 6\. 「難用」對 AI consumer 可以操作化，不必停在感覺

我會拆成五個 observable dimensions：

| Dimension | 可觀察現象 |
| --- | --- |
| **Discoverability** | 是否第一次就找到正確 source / skill / command |
| **Navigation cost** | 到 first correct action 前讀多少來源、走多少 hops |
| **Ambiguity** | 是否同時存在兩個合理但不同的 action |
| **Prompt repair** | 是否需要 human 再補一句「去看 X」 |
| **Workaround** | 是否繞過設計好的入口才能完成 |

其中最值得收的是 **workaround event**。

因為 workaround 在成熟系統裡通常比 failure 更有情報量：

```
failure:
    agent 失敗

workaround:
    agent 成功了
    但系統 interface 不夠好，所以它自己補了一條路
```

這很容易被一般 success rate 隱藏。

### friction log 不需要做成另一套大平台

一筆 event 只需要：

```
task
consumer/harness
symptom
intended path
actual workaround
extra hops
outcome
```

然後 weekly aggregation 看 pattern。

我會設一個很實用的規則：

> **同一 workaround 在兩個獨立 consumer contexts 再現，就從 anecdote 升格為 design smell。**

如果是在兩個不同 repo 或不同 harness 重現，證據更強。

### Navigation cost 不要硬訂全域 token threshold

不同 model、harness 的 token behavior 不同。

所以最好看：

```
same task corpus
same harness/model family
before vs after
```

例如：

```
median lookup hops: 3 → 7
read-set: 4 docs → 9 docs
prompt repair rate: 0/8 → 3/8
```

比「一定不能超過 5,000 tokens」有意義得多。

* * *

## 7\. 三個問題其實是同一張圖，但 local opt 多了一個特殊需求

可以這樣看：

```
                independent evidence
                         ▲
                         │
 feasibility             │        usability
 hypothesis ──→ spike ───┤   change ──→ consumer dry-run
                         │
                         │
                  implementation
                         │
                         ▼
                     many arcs
                         │
                         ▼
              reheat / full review
                         │
                         ▼
                 reopen assumptions
```

三種 failure 對應三種「距離」：

| 問題 | 被拖太遠的證據 |
| --- | --- |
| 中途不可行 | feasibility evidence |
| 做完難用 | consumer behavior evidence |
| local optimum | alternative-architecture evidence |

前兩個主要靠 **縮短 feedback** 可以改善。

Local opt 不完全一樣。

因為即使：

```
每個 feasibility test 都很快
每個 consumer test 都通過
每個 arc 都沒有 bug
```

系統仍然可以走進一個非常漂亮、非常自洽、非常難維護的 basin。

所以 local opt 還需要：

> **periodic de-freezing / exploration。**

這是不能被 inner-loop testing 消掉的。

* * *

# 我會留下的最小機制集

不建議再建一整套治理框架。你現有 parity、consistency、hooks、corrections weekly、cross-family review 都已經很多了。

真正值得增量加入的只有四件事：

1. **EP 加 1–3 個 load-bearing assumptions + kill criteria**  
   把不可行發現時間往前搬；spike 用 evidence budget。
2. **建立一小組 stable consumer dry-run corpus**  
   尤其 cold navigation、normal task、resume。高影響 instruction 改動拿 fresh agent 跑。
3. **把既有訊號聚合成 Heat state，不新增大型 telemetry**  
   corrections、workaround、authority drift、ritual growth、boundary compounding → Cool / Warm / Hot。
4. **保留 full review 外圈，cadence 自調但永不取消**  
   escaped Critical 快速升溫；連續 zero-Critical 且 review power 穩定才逐步降頻；永遠保留 arc ceiling。

最值得避免的是第五件：

> **不要替這四件事再造一條完整 lifecycle。**

否則你會用「防止治理 local opt」的方式，製造下一層治理 local opt。

* * *

# 可以記住的一句心智模型

我會選：

> **內圈快證偽，外圈定期解凍。**

展開就是：

```
Before build:
    能不能做？      → kill criteria / spike

Before close:
    實際好不好用？  → consumer dry-run / friction

Across arcs:
    我們是不是一路把錯的前提當對？ → heat / reheat / full review
```

或者更精確地說：

> **縮短「決策 → 獨立證據」的距離；但無論內圈多好，都定期把 frozen decisions 重新變成 hypotheses。**

我認為這比「所有問題都是 feedback loop 太長」更完整，因為它保留了你這次抓到的核心：**local opt 的真正逃脫機制不是更精密地沿原路走，而是偶爾允許自己重新選路。**

方法論上仍有幾個限制：Critical 數量很稀疏，不能當高精度統計量；reviewer、模型與 rubric 改變會污染歷史比較；dry-run corpus 久了也會被系統 overfit；任何固定 Heat threshold 都只是初始控制參數，不是真理。更根本地說，沒有 sensor 能證明你已達 global optimum。因此這套機制的目的不是「證明架構最佳」，而是讓 **不可行更早死亡、難用更早曝光、歷史決策永遠不會取得永久豁免權**。
