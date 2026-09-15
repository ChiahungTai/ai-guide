# Controlled Compact Strategy UC

## 任務一句話

研究在長時間 AI coding session 中，以可控方式取代或補強 harness 自動 compact，保存推論狀態與工程決策品質，而不是只追求 token 壓縮。

---

# 背景

目前 ZCode / Muse 類 coding agent 可能在長 session 中遇到 context 壓力：

```
long reasoning session
        |
        v
automatic compact
        |
        v
continue
```

問題是一般 compact 的最佳化目標通常是降低 context size，而不是保存：

- 架構決策原因
- 已排除方案
- 目前 implementation state
- invariants / constraints
- 下一步工作狀態

對複雜工程任務而言，context 壓縮品質會直接影響後續推論品質。

---

# 核心原則

## Compact 不是 Memory

兩者目的不同：

```
Memory
=
long-lived knowledge

Compact artifact
=
short-lived reasoning state preservation
```

Memory 保存跨 session 知識。

Compact 保存同一 session 中斷後繼續推理所需狀態。

---

# 現況判斷

## 不依賴不存在的 compact hook

目前不假設 harness 提供：

```
before_compact event
        |
        v
custom summarizer
        |
        v
resume
```

因此不把方案綁死在特定 agent 實作。

若未來 harness 提供 compact lifecycle event，再將 manual flow 接成 hook。

---

# 建議流程

## Controlled Compact Protocol

```
context budget threshold

        |
        v
manual command trigger

        |
        v
extract reasoning checkpoint

        |
        v
compact

        |
        v
resume validation
```

---

# Compact 前狀態抽取

Compact 前應產生 checkpoint：

```yaml
objective:
  current task goal

decisions:
  important choices and rationale

constraints:
  architecture boundaries

current_state:
  modified files
  completed work
  pending work

open_questions:
  unresolved decisions

next_actions:
  immediate continuation steps
```

---

# Resume Validation

Compact 後不只恢復文字，而應驗證：

- 是否能描述目前目標
- 是否理解架構限制
- 是否知道已完成與未完成事項
- 是否能繼續下一個 action

---

# Skill 演進方向

未來可抽象成：

```
context-preservation skill

    |
    +-- compact preparation
    |
    +-- reasoning checkpoint
    |
    +-- resume validation
```

此 skill 與 memory-audit / review skill 職責分離。

---

# 與 Review System 關係

Review 解決：

```
AI confidently wrong
```

Compact 解決：

```
AI context degradation
```

兩者皆屬 AI workflow reliability layer，但不是同一 UC。

---

# 後續研究

1. ZCode / Muse 是否存在可用 compact event API
2. manual command 的最佳 interface
3. checkpoint 是否應結合 project memory
4. compact 後自動 resume quality evaluation
5. 不同 model context window 下 threshold 策略
