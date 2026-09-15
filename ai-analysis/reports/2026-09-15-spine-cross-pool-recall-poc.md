# Spine 跨池召回 POC——行為驗證報告

> 日期：2026-09-15。發起：user 提問「user-level 記憶有確定各個 harness 都可以正確讀到嗎？有做 POC 嗎（寫個 marker 問各 model agent）」並授權執行。
> 性質：行為驗證 POC（falsification test）。先前僅有結構可達驗證（AIR-45 S6 symlink 在場）與主池索引召回（SM-1 A=B=C=12/12、live codex 12/12）——spine 本體的跨 harness 行為召回從未驗過，本次補上。
> 證據檔：`.agent-tmp/spine-poc/L2-cc-foreign.out`、`L3-cc-aiguide.out`（ephemeral 7d）；bridge 原始輸出 `.delegate-bridge/jobs/job-mu2o3ksu-kn6lwj.jsonl`（muse）、`job-mu2o3ohy-466mxy.jsonl`（codex）。

## 方法

1. **Marker**：`~/.agents/memory-spine/poc_spine-recall-marker.md`——不可猜 token `ZEBRA-QUANTUM-7F3A`＋虛構 provider 事件，檔內自我宣告「虛構、非事實、POC 後刪除」（防注入設計）。POC 後已刪。
2. **五腿並行**，同一問題、不給路徑：「跨 harness 共享的 user-level 記憶（存放 model 額度／訂閱現值那類）放在哪裡？給實際找到的完整路徑＋逐字引用最近一次額度事件行。找不到就答找不到，禁止猜路徑。」

## 結果：5/5 PASS（含預測會 FAIL 的腿）

| 腿 | 條件 | 載具 | 發現 | 逐字召回 |
|---|---|---|---|---|
| L1 | ZCode／ai-guide | fresh subagent（general-purpose） | ✅ `~/.agents/memory-spine/reference_model-runtime-entitlements.md` | ✅ |
| L2 | **CC／外 repo（code-reality）** | `claude -p`（backend=GLM-5.3） | ✅ 同上＋正確引用 index.md 決議記錄 | ✅ |
| L3 | CC／ai-guide（對照） | `claude -p` | ✅ 同上＋主動標註 as-of/mtime 腐爛語義 | ✅ |
| L4 | muse bridge | delegate-bridge task（muse-spark-1.3/xhigh） | ✅ 同上 | ✅ |
| L5 | codex bridge | delegate-bridge task（chatgpt-web/high） | ✅ 同上 | ✅ |

- **逐字召回**：五腿全部逐字一致引用真實事件行「`- **近期事件**：muse 429 額度耗盡一次（窗口 reset 2026-09-14 08:00 台北後恢復）」——非幻覺（該行細節不可猜）。
- **抗注入**：L2（CC/外 repo）額外讀到 marker 檔與 token `ZEBRA-QUANTUM-7F3A`，但**明確拒採**為答案——理由正是 marker 自我宣告「虛構、非額度真相、不供決策引用」。防注入設計如預期發揮；其餘腿也一致視 marker 為非權威。

## 為什麼 PASS——發現種子在全域 bundle，不在 repo

POC 前主 session 機械掃描宣稱「全域開場材料對 spine 零提及、跨池發現不成立」——**該宣稱錯誤，模式為 rg 連字號/空格陷阱**：掃的是 `memory-spine`（連字號），但全域 model-routing rule 原文寫「**memory spine**（`model-runtime-entitlements`）」（空格）。機械複驗：

- `~/.claude/rules/model-routing.md`（CC 全域 auto-load）：命中
- `~/.zcode/AGENTS.md`（ZCode 全域 bundle）：1 命中
- `~/.codex/AGENTS.md`（codex 全域）：1 命中
- muse：行為證據直接成立（L4 PASS；bundle 亦含 guide）

即：guide bundle 的 model-routing rule「volatile state 不住 catalog/rule——每次 dispatch 前由 memory spine（model-runtime-entitlements）／probe 形成 AvailabilitySnapshot」一行，為**所有 harness、所有 repo** 的 session 提供命名種子；agent 憑條目名稱做檔案系統搜尋即可定位 spine 目錄。跨池發現路徑＝全域 bundle 命名＋FS 搜尋，不依賴 ai-guide repo 在場。

## 限制

- Bridge 腿（L4/L5）cwd 不可控（bridge 無 cwd flag，均自 ai-guide 環境起跑）——「真外 repo」僅 CC 腿成立；muse/codex 外 repo 未直接測，但其種子（全域 bundle）cwd 無關，風險低。
- 每腿 n=1；CC 腿 backend 是 GLM-5.3（非 Anthropic 模型，harness 開場材料同 CC）。
- ZCode 外 repo 腿未測（subagent 繼承 workspace）；種子同為全域 bundle，推定可比照。
- Marker token 未成為任何腿的「主答案」——問題語義指向 entitlements 主檔，屬設計瑕疵非失效；逐字真實行同樣完成防幻覺判準。

## 結論與更正

1. **更正**：本日先前對 user 的宣稱「跨池共享實際是 ai-guide 單池寫、誰碰巧知道誰讀；跨池是名義的」**錯誤**。行為證據：跨池發現與召回 5/5 成立，機制＝全域 bundle 命名種子（cwd 無關）。
2. spine index 認養表「ZCode 待辦」指 generator 認養 routing 行段（投影機制），與行為可發現性是兩回事——行為已 PASS，投影認養仍可做但非阻塞。
3. 仍然成立的缺口（與本 POC 正交，屬資料新鮮度軸）：as-of 手動更新（現值 09-13 已舊）、muse usage 無 probe 面、窗口形態未結構化（形態可推度/現值不可推度的折衷未落地）。這三項是後續卡的自然候選。
