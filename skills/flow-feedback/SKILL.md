---
name: flow-feedback

description: "session 摩擦收集器——不順的 session 後，user 植入摩擦 + AI map 到 skills/commands，產 type-1（時機）/type-2（設計）建議 + 具體例子，寫 ai-analysis/flow-feedback/。/flow-feedback [摩擦描述]"
when_to_use: "After a session that felt rough or inefficient. User seeds the friction (where it felt off, in their words); AI maps to the current ai-guide skills/commands inventory and proposes initial suggestions — type-1 (timing: should have used /X) and type-2 (design: /X has a flaw or a command is missing) — each with a concrete session example and counter-factual. Writes structured feedback for later /flow-review discussion. Low-stakes collector (A-axis); deep reflection happens in /flow-review with the human."
argument-hint: "摩擦描述（哪裡不順）；無參數則互動問"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Write"]
---

# /flow-feedback — session 摩擦收集器

> **核心理念**：**收集器，不是反思本身**。把「不順」的摩擦結構化捕捉，供 `/flow-review` 定期討論。深度反思在討論段（human-in-loop），本命令只負責**降低反思門檻 + 誠實捕捉摩擦**。

## 為何存在

ai-guide 是持續演化的系統，但「session 不順 → 該改哪個 command/skill」的 insight 容易流失。本命令把演化輸入**結構化、持久化**，不靠記憶。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

---

## 流程

### 1. user 植入摩擦
- 有參數 → 直接帶入；無參數 → 互動問「這次哪裡不順？」
- **保留 user 原話**（高 signal；AI 改寫會稀釋）
- **terse 種子（無法 map，如 ≤3 字）→ 不列多選項**：保留原話 + 標「種子過短待釐清」+ map 到**最可能的一個**（標低信心），一句確認即可。禁止用「5 選項 + N 問題」抬高反思門檻 —— 本命令是降低門檻的收集器，不是 inquisition。真的無法 map 就保留原話 + 標待釐清，不硬猜。

### 2. 建立 inventory
讀 [skills/CLAUDE.md](../CLAUDE.md) 工作流索引 + 掃 `skills/` 清單，知道現有 command/skill 全貌，才能 map 摩擦。

### 3. 產兩類建議（強制都產）

| 類型 | 是什麼 | AI 傾向 |
|------|--------|---------|
| **type-1 時機** | 該用 /X 沒用、或用錯時機 → 給「正確觸發點」 | 愛提（推銷既有 command） |
| **type-2 設計** | /X 設計有缺陷、或根本缺這個命令 → 改善方向 | **不愛提**（等於承認設計錯）但**價值最高** |

> **type-2 不可省略**。就算結論是「沒找到設計缺陷」也要寫——這本身是 signal（摩擦純屬時機問題）。

### 4. 每建議附證據（品質規則）
- **session 具體例子**：指向這次 session 哪段（行為、對話、tool call）
- **counter-factual**：「若當時 [用 /X / 改設計 Y]，就會 [避免摩擦 / 更順]」
- **抽象建議無效**：「改善溝通」「更注意」這類視為無效，必須具體

### 5. 寫檔
`ai-analysis/flow-feedback/{YYYY-MM-DD}-{topic-slug}.md`（git-tracked；透過 `/commit` 提交）。

---

## 產出格式（dated file）

```markdown
# Flow Feedback — {date} — {topic}

## 摩擦（user 原話）
> {user 的話，原樣保留}

## session 摘要
{這次 session 做了什麼、哪段不順}

## type-1 建議（時機）
- **{建議}** → {對應 command/skill}
  - 例子：{session 哪段}
  - counter-factual：{若當時…就會…}

## type-2 建議（設計）—— 強制
- **{建議，或「未找到」}** → {對應 command/skill 或「缺這個命令」}
  - 例子：{session 哪段}
  - counter-factual：{若設計改…就會…}

## tags
`{command/skill 名}` 供 /flow-review 聚合
```

---

## 品質自檢
- [ ] user 原話保留（未稀釋）
- [ ] type-2 有產出（非空白）
- [ ] 每建議有 session 例子 + counter-factual（無抽象建議）
- [ ] 誠實（不自我辯護「我做得不錯」）

---

## 邊界

- **不是反思**：深度設計缺陷的挖掘在 `/flow-review`（你 + LLM 討論）。本命令是素材收集。
- **A 軸天花板**：AI 自審有 bias，建議是「討論起點」不是「定論」。type-2 強制是為了逼 AI 至少嘗試，不是保證找到。

---

## 與其他命令

- → [`/flow-review`](../flow-review/SKILL.md)：定期讀這些 feedback + 跟你討論改善
- 討論定案 → `/execution-plan`（大改，必要時先 `/spec` 釐清需求）/ kanban card（小改）→ `/implement`
