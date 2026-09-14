# AIR-79 live 腿 L1–L6 receipt（2026-09-14 08:01–08:15，mosaic 首站）

- 執行者：ZCode 排程 automation-6d26ab0e（user 09-13 指定 08:01，額度 00:00Z 重置後首時槽）
- 環境：muse 1.1.1；plugin muse-memory-governance 0.1.0（user-scope，source home＝本 repo `muse-plugins/memory-governance/`，install 09-12 未重裝——額度已恢復無需重裝步）；probe repo＝mosaic `.agent-tmp/mos98-live-probe/`（git init＋marker `{"protocol": 1}`＋**無 legacy hooks.json**＝plugin 單寫者隔離場）；diag plugin `mos98-stdin-diag`（臨時 user-scope，stdin dump 用，驗後已移除）
- 額度：bridge muse smoke `job-mu0hc84e-pjp06t` 完成（429 解除）；L1 一次 meta stream retry（attempt 2/10，瞬態）

## L1 live fire＋approval gating — ✅

- 隔離場 `muse exec --approval-mode never` 觸發 add_memory → `tool blocked by hook: 已代存 inbox: …/mos98-live-probe/.agents/memory-inbox/20260914-080605-96516-a5ea9745795f.json`（deny 訊息＝共享核心格式；probe repo 無 legacy → 唯一寫入者＝plugin）——**live（非 harness）session plugin hook fire 實證**
- receipt 逐字含真 stdin：`hook_event_name/tool_name/tool_input/tool_use_id/session_id/turn_id/cwd/transcript_path/model/permission_mode/model_provider`；permission_mode=`bypassPermissions`
- approval gating 雙向實證：diag 未 approve → dump 缺席（壓制）；approve → dump 在場（放行）
- probe inbox 計 23 筆 receipt（1 L1-pre＋1 L1-main＋20 L6 fixture＋1 L5c），probe repo 已清除

## L2 bridge headless — ✅

- `delegate-bridge task --family muse`（job-mu0hjg9u-kva66a，session 01a09d3e-ea81，workspace=mosaic root）委派 add_memory → deny＋receipt 落 mosaic `.agents/memory-inbox/20260914-080905-2190-*.json`（疊窗態＝legacy owner fire headless）
- diag（user-scope registry）於 bridge session 內 fire 13 條（stdin `cwd=/Users/ctai/Github/mosaic_alpha`）——**headless 讀 user-scope plugin registry＋hook fire 實證**（governance 本身於 mosaic 疊窗態 no-op，registry 讀取路徑由 diag 承載證明）

## L3 真 stdin 欄位（P-WS 凍結）— ✅ 素材齊

- **實測欄位集**（L1 receipt＋diag dump 多源一致）：`hook_event_name`、`tool_name`、`tool_input`、`tool_use_id`、`session_id`、`turn_id`、**`cwd`**、`transcript_path`(null)、`model`、`permission_mode`、`model_provider`
- **無 `workspace`／`host_workspace` 欄位**；`cwd`＝muse workspace root（muse stderr `workspace root: … (cwd default)` 互證）；sub-session（muse 內部 `submit_reminder_decision`）攜同值 cwd
- **凍結提案**：resolver jq 鏈以 `.cwd` 為權威首選（現行 `.workspace // .cwd // .host_workspace` 已可用——`.cwd` 居第二位但前兩者 live 恆缺席）；R4 硬化（stdin-derived repo 須 git root）與實測相容
- Proposed patch（交 ai-rules session 固化，未動源）：

```diff
-  REPO=$(printf '%s' "$IN" | jq -r '.workspace // .cwd // .host_workspace // empty' 2>/dev/null || true)
+  # P-WS frozen (live 2026-09-14): muse live stdin carries `cwd` (workspace
+  # root); no `workspace`/`host_workspace` field exists. Alternates kept as
+  # backward-compat fallbacks.
+  REPO=$(printf '%s' "$IN" | jq -r '.cwd // .workspace // .host_workspace // empty' 2>/dev/null || true)
```

## L4 untrusted workspace — ✅（形態與 O8 假說不同）

- probe repo＝未註冊 git root → muse 判 `workspace is untrusted`（Agent delegation suppress，O8 同款訊息），**但 approved plugin hook 照常 fire＋divert**
- 判讀：trust 邊界 suppress 的是 delegation，不是 hooks；EP ⑥「untrusted suppress 是合理安全邊界」的實際語義＝delegation 層。untrusted repo 帶 marker 仍受治理（防護面更大非更小）；malformed marker deny fail-closed 不變。是否需收緊（untrusted 連 hook 也不 fire）留 user 裁決

## L5 re-approval 語義 — ✅ 全譜解碼（含卡片預言的 fail-open 窗口證實）

以 diag 自體實驗（不動 ai-rules 源）：

| 操作 | package sha | runtime status | settings trusted_definition_hash | live fire |
|---|---|---|---|---|
| update（內容不變，L5a） | 同前 | trusted_enabled | 不變 | —（對照組） |
| update（script 內容變，L5b） | 553d4d7f→698ff358 | **modified**（"definition hash changed and needs review"） | 舊值未動 | **停火**（L5c：dump 零新增） |
| re-approve（L5d） | — | **trusted_enabled** | 重釘新 hash 63462bcd | （語義已由 L1 雙向實證，未再燒額度） |

- **機制**：approve 綁 `definition_hash`（**含 script 內容**，非僅 manifest 形狀）；content update → hash 變 → runtime `status=modified` → hook inactive 直到 re-approve
- **fail-open 窗口證實**：update 後未 re-approve 的窗口內，governance hook 不在場 → live/headless add_memory **native 直寫 canonical**（headless 無任何提示）。卡片驗收⑤的擔憂成立——但其形態是「update 之後」而非「install 之後」
- **O7 修正**：`plugins list/inspect` 的 "hooks require review" warning 是 third-party 常駐雜訊（approve 後仍在），**非 approval 狀態訊號**；真訊號＝`muse plugins inspect <id> --json` 的 `runtime_capabilities[].status`（trusted_enabled／modified）＋settings.json `/runtime_capabilities/` hash 對比
- **治理含義**：governance 內容每次更新（ai-rules 推修復→`plugins update`）後必須立即 re-approve，否則全機器記憶閘靜默下線；health check 應 assert `status=trusted_enabled`

## L6 overhead — ✅ budget 內

| 軸 | early-exit（非 memory tool） | divert 全路徑 | budget |
|---|---|---|---|
| harness（`plugins hook test`，含 muse spawn；20 runs） | 62.6 ms/run | 153.5 ms/run | 100 / 250 ms |
| 純腳本（直接驅動 cached core；10 runs） | 32 ms | 35 ms | 同上 |

- 補充：plugin hooks 無 matcher → **每次 tool call 都 spawn**（diag dump 實證 muse 內部 `submit_reminder_decision` sub-call 也觸發）——N hooks × M calls/turn 的乘數在 runtime 軸存在，唯本 plugin 早退 32ms 攤薄可忽略

## Gate 判定建議（決策留 user）

| gate | 證據 | 建議 |
|---|---|---|
| ③ live activation（direct＋bridge headless） | L1＋L2 全綠 | **PASS** |
| ⑤ re-approval | L5 全譜：update→modified 停火（可 inspect 偵測）；re-approve 恢復 | **PASS 附運維條款**（update 後必 re-approve；health check 加 status assert） |
| ④ overhead | L6 兩軸 budget 內 | **PASS** |
| ② legacy 共存 no-op | offline（09-12）＋live（本日 mosaic 疊窗態 plugin no-op、legacy fire） | PASS |

## PENDING（待 user 裁決）

1. **S4 cutover**：四 gate 證據齊建議 GO——ai-rules 側正式 cutover 流程（重裝→approve→marker 落 ai-rules trunk→legacy 註冊退役）開弧執行
2. **mosaic legacy 退役**：前置＝marker 先 ff 各線 trunk（mos-98 已進 main；offline_backtesting/trading_lab 隨 rebase 取得）→ 才刪 `.muse/hooks.json`＋`hooks/muse_memory_inbox.sh`＋`hooks/setup-muse-hooks.sh`＋AGENTS.md 疊窗句；順序倒置＝三線裸露
3. **update-re-approve 運維條款**：governance 每次內容更新後 re-approve（建議寫入 ai-rules README＋health check assert `runtime_capabilities[].status == "trusted_enabled"`）
4. **L4 收緊與否**：untrusted workspace hook 照 fire（delegation 才 suppress）——現形態防護面更大；是否要求 untrusted 連 hook 都不 fire，留 user
5. **P-WS 凍結 patch**：上段 diff 交 ai-rules session 固化（本批次未動源）

## 清場紀錄

diag plugin 已移除（`plugins list` 僅餘 governance，enabled/active/valid）；mosaic inbox probe receipt 已刪（僅餘 consolidation done/processing/rejected 目錄）；probe repo＋diag dump＋fixtures 已清除。governance plugin 全程未動（install 09-12 原狀，approved，active）。本報告未 commit。
