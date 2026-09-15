# muse-tool-governance

user-scope Muse plugin：`bash-write-guard` PreToolUse hook，攔截 bash 工具內「python heredoc + 寫檔 API」的繞道寫檔形態（政策源：ai-guide `rules/tool-discipline.md` 檔案修改禁令；判斷契約移植自 `hooks/block-python-file-write.py`，AIR-97）。

## 安裝（v1 手動分發；deploy_agents.py 無 plugin 部署概念——擴充另案）

```bash
muse plugins install --scope user /Users/ctai/Github/ai-guide/muse-plugins/tool-governance
muse plugins approve muse-tool-governance
muse plugins inspect muse-tool-governance --json   # 斷言：runtime_capabilities[].status == "trusted_enabled"
```

## 運維鐵律

- **更新生命週期（S1 實證）**：改源檔**不會**自動傳播——cache 照跑舊版且 status 仍 `trusted_enabled`（無警訊 drift 風險）；必須 `muse plugins update muse-tool-governance` 同步 cache，此時 hash 與 approved 版不符 → status 變 `modified`、hook **停火**（fail-open 窗口）→ **立即 `muse plugins approve muse-tool-governance`** 恢復。完整鏈：改源 → update → approve，三步不可缺。
- **逃生**：`muse plugins disable muse-tool-governance`（誤攔時一鍵關閉；deny reason 內附此句）。
- **rollback**：`muse plugins reject muse-tool-governance`（trust 撤銷）或 `muse plugins remove muse-tool-governance`（整組移除）。
- hook 本地測試：`muse plugins hook test muse-tool-governance:bash-write-guard --fixture <json> --json`（fixture 頂層 `event` 欄必須、`stdin` 須 JSON 物件）。

## fail-closed 語義（AIR-97 已決策③；S3 實證基礎）

muse 對 hook crash／非零退出＝**fail-open**（S3 hook test 實證）——因此本 hook 所有異常路徑（stdin 讀取失敗／jq 不可用／JSON 解析失敗／command 缺失）皆 in-script 顯式 deny。兩段式：① 非 `bash` 工具一律 allow（不可分類不擋，防 brick session）；② 判定 bash 後不可判讀→deny。漏攔成本＞誤攔（判例：memory-governance）。

## 已知事項

- **無 per-repo opt-out**：user-scope 粒度，所有 repo 所有 Muse session 生效（與政策全域性一致；memory-governance 的 marker 三態 opt-in 本 plugin 無對應）。
- **雙 hook 疊加**：與 memory-governance 並存時每個 tool call 兩次 hook spawn（各 32–62ms 量級）——S3 實證 muse 無 hook timeout 截斷，延遲成本真實存在；本 hook 非 bash 路徑在 jq 分類後即早退。
- 判斷契約已知限制（沿襲移植源）：`open()` 第一參數含巢狀括號（`open(Path(d).name,'w')`）不攔——寧漏抓不誤傷。
- 驗收證據：[EVIDENCE.md](EVIDENCE.md)（S3 契約矩陣＋S1 fixture／延遲實測）。
