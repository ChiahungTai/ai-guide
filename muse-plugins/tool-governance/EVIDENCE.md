# EVIDENCE.md — AIR-97（MOS-105）Muse hook 契約探測與驗收證據

> 探測日 2026-09-15。方法：fixture plugin 宣告＋`muse plugins validate`／`hook test`／live stdin-dump probe plugin（`m105-probe`，已於探測後 remove）。
> 原始輸出存檔：本目錄 `evidence/`。

## S3 能力矩陣（EP 段落 3＋增補格）

| capability | verdict | 判定依據（命令＋原始輸出） |
|---|---|---|
| PostToolUse hook | **supported** | `muse plugins validate` fixture 宣告 → `valid:true`（evidence/validate-posttooluse.json） |
| Stop hook | **supported** | 同上（evidence/validate-stop.json） |
| matcher 欄位 | **rejected** | `unsupported-field` diagnostic："hook capability field \`matcher\` is a Claude/Codex hook field; TBH plugin hooks key on \`event\`"（evidence/validate-matcher.json） |
| updatedInput | **decision 管線接受**；live 改寫未驗 | `hook test` 回 `decision.updated_input={"command":"echo AIR97-UPD-WORKS"}`（探測鉤 marker 條件觸發；live 是否實際改寫工具輸入＝unknown，供 H5 未來決策） |
| **bash `tool_name` 值** | **`"bash"`（全小寫）** | live stdin-dump：`{"tool_name":"bash","tool_input":{"command":...,"description":...},"cwd":...,"model":"muse-spark-1.3",...}`（evidence/probe-live-stdin-bash.json） |
| stdin 欄位契約 | 頂層 `hook_event_name`／`tool_name`／`tool_input`／`tool_use_id`／`session_id`／`turn_id`／`cwd`／`model`／`permission_mode`；**無 `workspace`**（cwd＝workspace root，與 memory 條目蒸餾一致） | 同上 dump |
| exit-非零 hook 行為 | **fail-open（放行）** | `hook test` exit-1 鉤 → `should_block:false`、hook status `"failed"`——crash／非零退出不構成 deny，S1 deny 須 in-script 顯式輸出 |
| timeout 逾時行為 | **hook test 層無截斷**（sleep 3s 跑滿 `completed`，duration 3369ms） | EP SM-6 的 1000ms 是自律預算非 harness 強制；慢 hook＝真實延遲成本（疊加注意） |

## 附帶觀察

- probe 窗口期 live muse 工單在 exit-1＋sleep3 鉤在場下正常完成＝live fail-open 側證。
- 捕獲到 muse 內部工具呼叫（`submit_reminder_decision` 等）——非 shell 類，即 S1 allow 路徑實例；SHELL_TOOLS 枚舉以 `"bash"` 為現值，未知工具保守 allow（兩段式①）。
- probe plugin 已 remove（`muse plugins list` 僅剩 muse-memory-governance）。

## S1 bash-write-guard 驗收（2026-09-15）

| 項目 | 結果 |
|---|---|
| deny fixture（bash＋heredoc 寫檔） | `should_block:true`＋`permissionDecision:"deny"`，reason 具名修正指引＋逃生句 |
| allow 非 bash（`submit_reminder_decision`） | 靜默 exit 0，`duration_ms:13`（早退<100ms ✓） |
| allow 純讀 heredoc | 靜默 exit 0，36ms |
| deny bash 無 command | deny（fail-closed ②段），21ms |
| deny 全路徑延遲 | 首跑 465ms < 1000ms 預算 ✓ |
| install→approve→inspect | `trusted_enabled`（checkpoint 已向 user 出示） |
| 更新生命週期走查 | 改源→cache 照跑舊版（無警訊）；`update`→`modified` 停火；`approve`→恢復 `trusted_enabled`——README 鐵律據此修正為「改源→update→approve 三步」 |
| 判斷契約同源實證 | 測試過程中 ZCode 端移植源 hook（block-python-file-write.py）攔下測試指令本身——同契約跨 harness 活體對照 |
