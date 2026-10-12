# consume holder 恢復 runbook（AIR-320）

> **適用**：dutymail consume holder 卡死時的 operator 恢復——人類在場互動面。情境編號（S-a/S-b/S-c/S-d）承 AIR-318 裁定：真卡死集＝S-a（bind→save 窗口崩潰）／S-b（跨機 token）／S-c（holder 檔損壞）；S-d（外活 holder）＝busy 非卡死、恆不 force。
> **契約真相源**＝dutymail binary `--help`（安裝面 `~/.local/lib/delegate-bridge/runtime/current`，3.12.0；binary 更新後現場重驗）；全域旗標 `--store-root <PATH>` 可覆寫 store root（預設 exactly `$HOME/.dutymail/`——never cwd）。消費端本地狀態單一源＝`scripts/duty_receive.py`。
> **本文只用既有 face（status/release/takeover）**：CLI 無 `--force`、無 death-evidence 旗標——接管正當性是消費端規則（takeover help 條款：automatic only with authoritative old-owner death evidence, "a consumer-side rule — dutymail imposes no policy"）。typed contract：每命令恰一個 JSON；exit class 2 usage／3 admission／4 storage／5 fencing／6 wait-timeout。

## 1. 四情境允許／拒絕矩陣

| # | 情境 | 判定特徵 | 處置 | server 面 |
|---|---|---|---|---|
| M1 | 自家 token 在手 | 本 session holder 檔形正確、token 在場（§3 步 1） | **允許**——`holder release --address <ALIAS> --token <TOKEN>`（與既有 in-path 自癒同權威：server 對 role ladder 驗 token；outstanding prepared batches fenced〔consume role〕；mail/cursor/epoch retained。help 條款：Clean shutdown is release — not walking away） | release |
| M2 | token 不在手：S-a（bind→save 崩潰——server active、token 無處可尋）／S-b（跨機——token 在他機 XDG state） | `holder status` 報 binding active＋本機無可用 token | **有條件允許**——operator runbook（§3）＋AUTH（§4）；執行面＝`holder takeover --address <ALIAS> --expected-epoch <N>`。面缺席、evidence 不到 §2 授權線、fresh-counter-evidence 在場、CAS 競敗——任一即 **PENDING**（停、記錄、不上搶） | takeover |
| M3 | holder 檔損壞（S-c：壞 JSON／形漂移——每次消費被本地閘擋） | `_load_inbox_holder`／`load_state` S2Error 或壞 JSON 註記 | **允許（純本地）**——本地丟棄損壞檔＋audit 行；**零 server 面**。丟棄後 status 重觀察：`bound:false`→正常 rebind 自癒；`bound:true`→token 隨檔同失，落 M2 | 無 |
| M4 | 外活 holder（S-d：別 session 正值星） | binding active＋fresh-counter-evidence 在場（§2） | **恆拒**——busy 非卡死：不接管、不排程、不重試轟炸。正當路徑＝對方 release 後下一次顯式操作重試（pending 已保留；`_s2_bind_no_takeover` 機械閘本就擋） | 禁 |

## 2. 證據等級表

核心分軸：**evidence（它死了嗎）≠ authority（誰承擔誤判風險）**。

| 等級 | 內容 | 效力 |
|---|---|---|
| **A 權威死亡證據** | supervisor 報告 owner session／attempt 已終止；或可驗 owner PID＋process start identity／host／boot ID、且該 holder 可存活的所有 owner 執行實體均已退出；**且**身份能 join `address+epoch`（重讀 fresh status 仍同一 epoch） | 可作 M2 接管的判死前提；仍須 AUTH＋scope fence＋epoch CAS |
| **B 輔助** | heartbeat 停擺／state mtime 停止／過 24h 無新產物／`ps` 找不到某名稱／watcher 不喚醒 | 只提示、觸發查證；**單獨或相加都不構成 A**；process lineage 未知或 owner 在遠端時不可推死 |
| **C user 指認** | user 說「我關了那個 session」 | **authority 非 evidence**——給許可、不給證明；fresh-counter-evidence 在場恆拒（AUTH 不 override 物理）；不得由 unattended LLM 冒用 |

三個常見誤讀（皆非死亡證據）：

- 自家 token 在手＝custody 證明非死亡證據——M1 路徑根本不需要判死，server `release --token` 對 ladder 再驗即合法權威行使。
- `holder status` active＋epoch＝證**佔用存在**，不證死亡。
- legacy `_holder_death_evidence`（同 address+epoch 兄弟 state 全陳舊 ≥24h，duty_receive.py）＝B 級的自動化形——現況事實保留，不自動擴權為 M2 憑證。

## 3. operator runbook（逐步）

**前提：人類在場。** 夜間 autonomous 禁 M2 段（無 token 面＝跳過＋晨報；夜間無-token 自動 release 恆紅線）；M1 是既有自癒路徑、不需本 runbook。

**步 1 診斷（全唯讀、零寫入）**

1. `dutymail holder status --address <ALIAS>`——唯讀結構觀察（help 條款：never mutates state），回 `{bindingEpoch, bound}`；記 `N＝bindingEpoch`。role 預設 `consume`（顯式可加 `--role consume`）。
2. 本地狀態（ai-guide 消費端；路徑單一源 duty_receive.py）：per-session holder state（`${XDG_STATE_HOME:-~/.local/state}/ai-guide/duty-receive/<session>.json`）與 per-repo 短 holder（同目錄 `repos/<address>/inbox-holder.json`）可讀性與形。token 一律只印 fingerprint：`printf '%s' "$TOKEN" | shasum -a 256 | cut -c1-12`——token 全文禁落 log、報告、AUTH 引文。
3. in-flight batch：`dutymail receive status --address <ALIAS>`——唯讀投影；`liveBatch`（fromSeq/throughSeq/expiresAtUs）非 null＝有 prepared batch 在飛。
4. 證據收集對照 §2 表（A 條款逐項採集；B 只入查證記錄）。診斷缺席欄直接標 unknown，不猜測。

**步 2 對矩陣**——§1 判 M1／M2／M3／M4。

**步 3 AUTH（僅 M2）**——貼 §4 範本求授權：`<repo-address>` 門牌明名、`<N>` 填步 1 的 epoch。不含門牌的泛稱授權＝PENDING。

**步 4 執行面選擇**

- 執行前**重讀** `holder status`：epoch 已換代（≠N）即停——身分不符拒絕；禁地址通配、多址掃蕩、輪詢搶章。
- **M1**：`dutymail holder release --address <ALIAS> --token <TOKEN>`（role 預設 consume）。
- **M2**：`dutymail holder takeover --address <ALIAS> --expected-epoch <N>`——epoch CAS＋takeover intent stamp 入事件史（help 條款：same epoch-CAS skeleton as bind）。CAS 競敗（typed failure code `epoch-conflict`、exit class 5 fencing）＝停止回報，單次嘗試不重試轟炸。成功＝接管方取得新 binding（bind 同骨架、token 一次性發還）——解卡目的即刻以新 token `holder release` 回 holderless 常態，後續消費者走正常 rebind；不做 release＋bind 原子、不代值星。
- **M3**：丟棄損壞檔（§1 M3 行）＋audit；無 server 面。
- **M4**：不做。

**步 5 事後 audit**

- audit 行：時間／address／epoch／情境編號／evidence 等級與條件／AUTH 引文（含門牌與 epoch）／結果／新舊 token fingerprint。
- **禁 flush-ack**：prepared batch 在飛時不得清本地 evidence 讓未完成信消失——release/takeover 對 outstanding batch 是 fencing（help 條款），後續由消費規則重放（`receive prepare --invalidate` 顯式作廢後重 prepare，寧重不漏）。
- 晨報／夜間台帳記一行（若夜間發現）。

## 4. AUTH 範本（逐字）

> 我授權對 `<repo-address>` 的 consume holder（目前 epoch `<N>`）執行一次經核實的恢復；先檢查原 session 的死亡證據與 in-flight batch，只在 epoch 仍是 `<N>` 時以既有 token release 或 operator takeover 進行。若存活狀態未知、CAS 競敗或批次結果不明，停止並回報；我理解成功會使舊 token 失效。

使用約定：一次一授權（單址、單 epoch）；quote scope 門牌必指名；授權不跨情境、不跨址、不預授未來。

## 5. B2 條件卡觸發判準（bridge 側）

- **觸發＝僅**當任一真卡死情境（S-a／S-b／S-c）經 §3 runbook 實測、既有面（status/release/takeover）無法恢復——逐案例記錄缺口證據（指令全文、typed failure 輸出、exit class、預期與實際差、binary 版本）才開 bridge 側卡。**無實證不開。**
- muse 版 force-release CLI spec＝B2 的輸入（AIR-318 裁定 D3 降級），非觸發理由。
- 非缺口（不開卡）：M4 外活 holder（busy 非卡死）；夜間無-token 自動 release（恆紅線）；`--force`／death-evidence 旗標缺席（takeover help 明文把接管政策留在消費端——設計如此，不是缺口）。
# Marshal 補實測（真 binary help——補 writer 無 shell 的缺口）

## holder 面在場性（三面皆在）
- `holder status`：唯讀觀察（never mutates state；reports bindingEpoch/bound）✓
- `holder release`：token 驗證釋放（outstanding prepared batches fenced；clean shutdown＝release）✓
- `holder takeover`：operator-invoked 顯式接管（epoch-CAS＋takeover intent stamp；`--address` exact＋`--expected-epoch` 必帶；automatic 僅限 authoritative old-owner death evidence——consumer-side rule）✓

結論：**既有面完整覆蓋恢復需求**——runbook 的 operator 路徑（AUTH＋evidence 分級＋takeover CAS）可直接落在既有 CLI 上；B2（bridge 側新 CLI）無需觸發。
