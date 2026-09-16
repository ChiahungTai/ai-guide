# AIR-100 開工交接包——guides-refactoring 弧調查產出 digest

> 讀者：air-100（memory 池治理整併弧）開工 session。目的：單一入口取得 guides-refactoring 前期調查的裁決輸入——不需回讀四份 `.agent-tmp` 原稿（暫存區，弧後會清）。
> 卡面關係：air-100 卡 notes 已指定開工必讀 `.agent-tmp/six-card-review/dossier.md`（另一份）；本包補上 guides-refactoring 弧這一份。**本包不改卡面、不自立新決策**——卡 Plan 的七條〔已決策勿重辯〕（air-100 卡 Implementation Plan 內 ①–⑦：auto-memory 機制定論／staging＋單向晉升方向／存量範圍含污染基線重審／清洗標的／AIR-90·83 整併／memory-audit:147 訂正／池鐵律）以指針引用，此處不重述。
> 持久源聲明：內容源快照住同目錄 `sources/`（`synthesis-topics-5-6.md`／`m-d-runtime-validation.md`／`codex-opinion-point-2.md`，2026-09-16 逐字快照）——`.agent-tmp/guides-refactoring/{synthesis,codex-opinion,m-a-output,m-d-output}.md` 清空後，快照即唯一源。

---

## 1. 調查結論精華（synthesis 議題 5＋議題 6）

> 逐字全文：`sources/synthesis-topics-5-6.md`。以下為決策相關精華，錨點保留。

**議題 5——hooks wiring 矩陣（memory-write governance）**：

- CC＋ZCode 兩家接線：PreToolUse `Edit|Write|NotebookEdit`→`hooks/block-memory-index-write.py`、PostToolUse→sensor、Stop→regen；CC 另有 FileChanged dirty-sensor＋SessionStart watch-seed（CC-only）。
- **Codex：memory-write governance 零 registration**（`~/.codex/config.toml` 全事件盤點無 `Edit|Write` matcher／memory script）——「主體對 codex 唯讀」僅紀律，非機械。
- ZCode SessionEnd 無事件鍵＝3.7.7+ 事件子集限制，非遺漏。
- muse plugin 僅註冊 PreToolUse（自濾＋inbox 導流＋終局 deny）；runtime approve 靜態不可證＝unknown——update 後未重 approve 即停火 fail-open 窗口。
- codex config stale `[hooks.state]` 殘留（指向已退役 `~/.codex/hooks.json`）**已於 2026-09-16 由 guides-refactoring EP S1.4 清理**（6 條 local 殘留刪除、market plugin 與 config.toml live 條目未動、啟動 smoke 過）——開工時勿重複處置。

**議題 6——「狀態後綴硬擋未實作」＋coverage matrix**（對應卡 P3 的現狀事實）：

- **air-90 後綴硬擋完全未落地**：決策文本在 air-90 卡 `:20`、承接本卡 P3，但 `hooks/block-memory-index-write.py` 全文無任何 stem-suffix 邏輯（2026-09-16 入册實測 273 行；`suffix` 命中僅 `.md` 副檔名判斷）；repo-wide 掃 `hooks/`、`muse-plugins/`、`scripts/`、`skills/memory-audit/` 零條 suffix-deny 實作。被擋的 writer 路徑＝無（零）；沒被擋＝全部。README「疑只護 muse inbox」猜測過於樂觀，以實測為準。
- writer×防線覆蓋現狀（M-D 三態標記＋unknown 認識態——**呈現選項，防線形態政策歸本卡裁決，本包不替拍板**；F-C 與 M-D 兩矩陣逐 row 相符，無矛盾，快照源＝`sources/`）：

| writer | 現狀標記 | 備註（選項空間歸本卡） |
|--------|---------|----------------------|
| CC/ZCode 主 session Write/Edit | `prevented`（附條件：opt-in 限 generator 目錄、hook crash 非阻斷、stderr 送達未證） | 條件是否收緊＝本卡裁決 |
| CC/ZCode NotebookEdit | `unsupported`（matcher 含字面、script 無分支直落 exit 0——dead-matcher） | 補分支或移 matcher 字面＋coverage assertion＝codex 建議，歸本卡 |
| subagent tool write | `unsupported`（ZCode 2026-09-01 實證 16,154 chars 落地無攔） | 接受缺口／文件明載／升級 harness 機制——歸本卡 |
| muse tool write | `unknown`（接線齊、fire 未證；09-14 live receipt 已過期） | runtime 三斷言跑一次即轉確定態（見 §2 第 4 條） |
| muse teardown 直寫 | `detected`（僅 reconcile 事後偵測；PreToolUse 天然攔不到） | prevention 政策歸本卡 |
| Bash redirect／shell 直寫 | `detected`（僅 reconcile） | 同上 |
| codex 寫池 | `unsupported`（連偵測掛點都無） | 紀律 vs 補接線——歸本卡 |

## 2. M-D 九條 runtime validation 清單（開工第一動候選，未執行）

> 逐字全文：`sources/m-d-runtime-validation.md`。逐條攜帶如下（源＝M-D static 審查，全部未跑）。

1. **CC/ZCode 主 session Write 重放**：generator 池內新建條目故意 desc＞100 chars，預期 exit 2；同測 hash／日期／`sess_`／新建＞3K／膨脹＞12K 各一例＋收斂方向放行一例。用後即清測試檔。
2. **NotebookEdit 缺口確認**：同條件以 NotebookEdit 寫入，確認直通或 dead-matcher（需觀測區分）。
3. **Subagent 負對照**：受控 subagent 對池 scratch 檔 Write，查 hook log 無記錄且寫入落地。
4. **muse 閘現況三斷言**：`muse plugins inspect <id> --json` assert `trusted_enabled`；governed repo `add_memory` smoke 預期 deny＋inbox receipt；marker 改壞後預期 deny。任一不過即上表 row「muse tool write」由 unknown 轉 gap。
5. **Teardown 偵測鏈驗證**：先手放檔模擬直寫驗 reconcile exit 2；再跑真 muse session-end 重放驗觸發。
6. **後綴擋可驗性前置**：任何 writer 級驗證前，先以 rg 定位 suffix-RE＋單元測試存在性——目前錨不存在＝無驗證可跑（P3 落地後此條才有內容）。
7. **Codex 面**：查 codex session rollout 有無池路徑寫入實例；長期以 reconcile clean 趨勢＋telemetry 盲區聲明監控。
8. **Consolidation 轉寫路徑稽核**：抽查 inbox→pool 消費，確認轉寫確由 CC/ZCode 主 session tool 發起。
9. **Approve 漂移監控**：每次 `muse plugins update` 後重跑第 4 項。

## 3. Segment 0 順序（codex 意見第 2 點）

> 逐字全文：`sources/codex-opinion-point-2.md`。五步順序：

**cutover snapshot → 關閉／隔離新污染來源 → 補 forward guard → 再做存量處置 → 最後 reconcile acceptance。**

**「先堵後清」理由**：後綴擋不應等待池內存量（86 條或 cutover 時實際數量）處置完才做——方向相反；先讓池不再形成 moving target，再清 stock。suffix deny 只能擋一類 state pollution，staging/cutover 能先完成就先做更上游的 containment，再補 suffix invariant。實證：air-100 notes 基線 41→78 成長——「先清後堵」會把 inventory count 變成追逐中的數字。

配套約束（同出 codex 第 2 點）：runtime validation（§2 九條）屬 Segment 0——architecture freeze 前跑完；`muse approve` 三斷言、Write/Edit replay、NotebookEdit 實際路徑、reconcile chain 結果回來前，防線形態不應寫成「已決策」。

---

## 附：範圍邊界（防重辯）

- 本包只彙整調查產出；**air-100 卡 Plan 的已決策事項以卡面為準**（含〔已決策勿重辯〕①–⑦），本包無重述表、無新裁決。
- 防線形態（prevented/detected/unsupported 政策）在 §1 表以三態標記呈現**現狀**與選項空間，拍板權在 air-100。
- owner 對照：skills fleet 處置（domain skills 遷出、desc 瘦身、instruction-testing 去留）歸 AIR-113；後綴擋實作、NotebookEdit 處置、`~/.agents` 清理政策歸 AIR-100——guides-refactoring EP 範圍外對照表已載，此處僅提示不展開。
