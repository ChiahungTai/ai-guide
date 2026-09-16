# AIR-79 S2/S3 probe 證據（09-12）

## Offline 腿（09-12 完成——`muse plugins hook test` harness，無 model 呼叫）

**環境**：muse 1.1.1（R2514.1）；plugin 經 `install --scope user` 裝入 content-addressed cache 後以 harness 驅動。probe repo＝`.agent-tmp/air79-probe-repo/`（git init＋marker `{"protocol":1}`＋`.agents/memory/note.md`）。

| # | 觀察 | 證據 |
|---|---|---|
| O1 | install 驗證 manifest schema：`version`/`description` 必填、`timeout_ms` **不支援**（invalid-manifest-schema ×3） | EP 規格修正項——FINDINGS 事實 #6 的 optional 欄位宣稱僅部分成立；已修 manifest |
| O2 | hook 經 harness 在 **approve 前**即 fire（harness 是 dev tool，bypass approval——live approval 語義須 live 驗） | 首次 hook test pre-approve 即執行（deny_degraded 輸出在場） |
| O3 | **full divert 綠**：repo 解析（git rev-parse from $PWD）→marker valid→atomic 落地（0600）→deny 帶 inbox 絕對路徑→effects=`blocked`＋`permission_denied` | `.agent-tmp/air79-gov-hooktest.json`；inbox receipt 內容逐字完整 |
| O4 | **gate ② offline**：working legacy owner（executable＋realpath≠self）→no-op（`status=completed` 41ms）；malformed `hooks.json`→**不讓位**照 divert | 兩次對照 run |
| O5 | **harness fixture 陷阱**：fixture `stdin` 欄位以**原樣位元組**餵給 hook（含引號的 JSON string）——parser 對 string 輸入必炸；**object-form fixture**（stdin 為 JSON object）才是正確形 | diag plugin dump：string-form→`Cannot index string`；object-form→`tool_name` 解析成功（FINDINGS p2 未踩到——其 probe script 不 parse stdin） |
| O6 | hook 執行環境：**PATH 完整**（/usr/bin、/opt/homebrew/bin 皆在）、jq(/usr/bin/jq)/git/shasum/realpath 全可解析 | diag env dump |
| O7 | **P-UPGRADE 靜態半**：`approve` 是 per-capability（`plugin:<id>:hook:<cap>`）；**`plugins list` 不暴露 approval 欄位**（approve 前後欄位面相同——trust≠approve 且 list 不可見＝EP 審查 C2 挑戰坐實，欄位式 health check 死路）；content `update` 後「hooks require review」警告**復現** | list 對照；update 輸出 |
| O8 | untrusted workspace 觀察（間接）：/tmp 下 `muse exec`→`workspace is untrusted`（delegation 被 suppress）——muse trust 模型在場；plugin 在 untrusted workspace 是否 fire 仍屬 live 腿 | 429 probe 附帶輸出 |

**量測（S3 腿，20-run 迴圈）**：early-exit（非 memory tool）≈**7ms/run**；divert 全路徑 ≈**50ms/run**——budget（100/250ms）內，gate ④ script 軸綠。runtime 軸（muse spawn 開銷）harness 數據 7-101ms 供參，精確值屬 live 腿。

**machine 復原**：`plugins remove` ×2→`muse plugins list`＝`no plugins`；scratch 清除。

## Live 腿（**PARKED**——muse 訂閱額度 429，窗口 2026-09-14T00:00Z 重置）

| # | 待證 | gate |
|---|---|---|
| L1 | live（非 harness）session 中 plugin hook 真的 fire＋approval gating 語義 | ③ |
| L2 | bridge headless（`task --family muse`）讀 user-scope plugin registry 且 hook fire | ③（A2） |
| L3 | 真實 stdin 是否帶 host workspace 欄位（P-WS 凍結 resolver 常數） | —（S1 provisional seam 回寫） |
| L4 | untrusted workspace 下 plugin 是否 fire（suppress 形態） | ③ |
| L5 | content update 後**不重 approve** hook 是否仍 fire（re-approval 語義；O7 顯示警告復現——重置嫌疑高） | ⑤ |
| L6 | runtime 軸 overhead 精確量測 | ④ |

恢復程序（額度重置後）：重裝 plugin→approve→逐項跑 L1-L6（L3 用 diag 變體 dump 真 stdin）→凍結 P-WS 回寫 S1 常數→gate 判定→S4。
