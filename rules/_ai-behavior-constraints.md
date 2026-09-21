---
harness-scope: neutral
---

# AI 行為約束

## single-source drift 防護（修改紀律）

改「定義源」（review-engine 共通邏輯 / 跨命令引用的 rule / 模式判定表——**含 code 定義源**）時，**強制 `rg "<單一關鍵詞>"` 掃所有引用該定義的命令/skill，逐檔同步**——否則「定義改了，引用沒跟」（drift regression）。細節見 instruction-writing skill「文檔自洽五維檢查」。
