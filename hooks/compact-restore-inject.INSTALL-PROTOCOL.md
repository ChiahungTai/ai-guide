# AIR-155 segment 2：compact-restore-inject hook 註冊協議（安裝／卸載／驗證）

> 執行者＝主 session（worker 禁改 `~/.zcode/`）。hook 本體＝`hooks/compact-restore-inject.py`
> （ZCode UserPromptSubmit sync；消費 `scripts/compact_checkpoint.py` 同一驗證機制）。
> 註冊片段＝同目錄 [registration.json](registration.json)。

## 前置檢查（安裝前）

1. `hooks.enabled: true` 在 `~/.zcode/cli/config.json`（2026-09-22 唯讀確認已為 true）。
2. hook 與機制件同 repo 在場：`hooks/compact-restore-inject.py`＋`scripts/compact_checkpoint.py`
   （hook 以 `Path(__file__).parents[1]/scripts/` 相對定位載入機制件——兩者不可分離搬運）。
3. bare `python3 --version`＝3.9.x（CLT；hook 已按 3.9 相容實作）。

## 安裝（merge，非整檔覆蓋）

1. 讀 `~/.zcode/cli/config.json`，取 `hooks.events.UserPromptSubmit` 現值
   （現況＝1 個元素：scbus async 條目）。
2. 將 registration.json 的 `hooks.events.UserPromptSubmit` 陣列**第二個元素**（process 條目）
   append 進現值陣列尾端；其他鍵／其他事件條目一概不動。
3. 原子寫回（寫 `.tmp` → `os.replace`），寫前留備份（探針卸載先例：config 備份 124302）。
   手工 merge 時安全模型照 `governance/install.py --surface hooks` 同款（只動目標子樹）。
4. **per-session 快照**：註冊後須**新 session** 才生效（ZCode hooks 於 session 啟動時快照配置）。

## 卸載

1. 自 `hooks.events.UserPromptSubmit` 陣列移除指向 `compact-restore-inject.py` 的條目
   （保留 scbus 條目），原子寫回＋備份。
2. 卸載後新 session 生效；已存在的 checkpoint／proven 檔（`.agent-tmp/compact-checkpoints/`）
   不隨卸載清除——cleanup 須 restore-proven 或 user 明示（cleanup guard 語義）。

## 驗證（安裝後四步）

1. **config parse**：`python3 -c "import json;json.load(open('<config>'))"` exit 0，
   且 UserPromptSubmit 陣列含 2 條目（scbus＋process）。
2. **hook 四情境實跑**（bare python3，非 uv——模擬 hook 執行面；2026-09-22 已預驗全過，
   註冊後複驗同款）：

   ```bash
   # 2a 無 checkpoint → exit 0、stdout 空、stderr 空
   printf '%s' '{"hook_event_name":"UserPromptSubmit","session_id":"sess_x","cwd":"<repo>"}' \
     | python3 hooks/compact-restore-inject.py
   # 2b 有未消費 checkpoint（.agent-tmp/compact-checkpoints/sess_x/checkpoint.json 先備妥）
   #    → exit 0、stdout 為 hookSpecificOutput JSON（thin pointer：路徑＋sha256＋預覽）
   # 2c 已 proven（write_restore_proven 後）→ exit 0、stdout 空
   # 2d 損壞 checkpoint（寫入壞 JSON）→ exit 0、stdout 為損壞警示 JSON
   ```

3. **靜默確認（live）**：無 checkpoint 的 repo 開新 session 發 prompt——模型 context 無
   `<compact-restore-inject>` 標記；`~/.zcode/cli/log/zcode-<日期>.jsonl` 無該 hook 的
   `hook.run.failed`。
4. **restore 注入確認（live，dogfood 時）**：工作 session 依 compact-prep skill 義務一寫入
   checkpoint → compact（manual 或 auto）→ 同 session 首個 prompt 應見 thin pointer 注入
   （路徑＋sha256＋head/tail 預覽，非全文）；照恢復流程 proven 後，次一 prompt 起靜默。

## 生命週期註記

- **路徑漂移點**：registration.json 現指向卡 worktree `/Users/ctai/Github/ai-guide-air-155/`；
  卡 merge 收線後主 session 更新為 `/Users/ctai/Github/ai-guide/`。worktree 刪除前未更新
  ＝ hook 每 prompt fail-open（stderr 診斷、exit 0、零注入——不擋 prompt 但 restore 注入失效）。
- **長期收編**：UserPromptSubmit 條目併入 `governance/registrations/zcode.json`（`{{REPO}}`
  模板）走 `governance/install.py --surface hooks` 單一源——屬卡 merge 後段落，非本段範圍。
- **下游依賴**：hook 的注入決策消費 `scripts/compact_checkpoint.py` 的
  checkpoint_paths／validate_checkpoint／verify_restore_proven——機制件 API 變更時
  hook 與 skill fallback 同步（兩者共用同一驗證是 AC 的明文要求）。
