# AIR-48 P5②：writer 歸因可見性修法建議（SM-5 處方箋——設計產物，實作另裁）

> 範圍：EP P5②——只產建議交 user 裁，不實作任何一案。證據基礎＝p1-taxonomy §2（SM-5）＋§4（覆蓋率）。產出不 commit（隨 dogfood 批次）。

## 破口重述（為何要修）

- `originSessionId`（frontmatter，創建時寫死）≠ 窗內末位 writer：**ai-rules 71/128、mosaic 73/106**——常態非例外
- 拓撲加劇：CC 路徑真池目錄＋zcode 路徑 symlink＝同實體雙寫入路徑，frontmatter 單一視角必然漂移
- 第三通道（muse/codex CLI、bash 直寫）實證存在：21:00 後 mtime 變更無 db/CC 事件；specimen 創建 Write 未見於 db

**歸因服務的三個用途**：①稽核鑑識（drift 內容誰寫的）②收斂安全（層 3「刪除前 mtime 稽核」的活躍 writer 識別——目前只有 mtime 沒有身份）③誤置治理（M1/M3 taxonomy 的 session 歸因表）。

## 三案評估

| 維度 | (a) body 加 writer log 行 | (b) telemetry 擴欄 db 反查 | (c) generator 註記 |
|------|--------------------------|---------------------------|-------------------|
| 歸因覆蓋率 | 僅 LLM 自律通道（寫入者自己記）；bash 直寫必不記 | **ZCode db＋CC transcript 兩主通道**（subagent 含 parent 譜系）；第三通道盲 | 同 (b) 之資料源，但 regen cadence 粒度（兩次 regen 間寫入混批） |
| 條目尺寸成本 | **直接膨脹**——M3 爆寫波實證（18+22 波、極端 27 條目/2 秒）下日誌線性堆疊；對撞 12,000 chars 上限與 hook | 零（條目不動） | 零（條目不動）；sidecar/_audit-state 增長（可接受） |
| 寫入摩擦 | 每次寫入多一個義務動作＝最高摩擦；log 行自身也可能 stale-collision | **寫入零成本**；查詢時跑管線（既有 90 天窗基礎設施） | 寫入零成本；但每 regen 多一次 db 查詢 |
| 與既有紀律張力 | **正面衝突**「寫入當下即蒸後形」（六問 Q5）與「過程敘述不屬條目」（一句話測試）——writer log 本質是流水，恰是 M1 要改道的東西 | 無衝突——audit-side 機械證據模式的自然延伸（治理三分離：報告附證據） | **架構張力**：generator 單一輸入原則（frontmatter→投影）被迫加第二輸入源（db）；P3 剛定型的 R2/R3 fail-loud 語義再開刀 |

## 推薦：(b)

**telemetry 新增 per-entry last-writer 投影**（sidecar JSON，如 `_attribution.json`：entry stem → {last_write_ts, source, session, actor}），由既有 90 天窗管線產出；層 2/層 3 消費點＝「mtime 稽核」升級為「mtime × last-writer 交叉」——刪除/合併前不只看檔案多新，還看**最後寫入者是誰、哪條通道、是否活躍 session**。

理由：四維度中三維全勝或並列（覆蓋、尺寸、摩擦、張力），且完全複用既有資產（telemetry collector＋審計三分離模式），零新增寫入端義務。**耐久性弱點誠實標註**：歸因是查詢時重建非隨條目固化——db/transcript 清理後歸因蒸發（rollout 已實證會清）；對此的互補腿恰是 AIR-49① git 基線（波級內容史回答「哪波改的」，(b) 回答「哪個 session 寫的」——互補非替代）。

**殘餘盲區**（(b) 也解不了的）：bash 直寫與任何無事件通道——只能內容鑑識（P1 式事後分析）追。政策面已在收縮此面（codex/muse 定唯讀），殘餘量級待 dogfood 觀察後再議。

## user 裁決點

1. **是否採 (b)**：若你更看重「歸因隨條目耐久」可選 (a)——代價是尺寸紀律正面讓步（不建議；(a) 的耐久性部分可由 AIR-49① git 補）
2. **第三通道殘餘盲是否需要更重機制**（如 hook 層寫入攔截記錄）——建議等 dogfood 窗口內實例數據再議
3. **實作排序**：建議排 AIR-49 之後——避免 dogfood 觀測窗口內池工具鏈異動（AIR-48 整合策略同型考量）

## 裁決（user 09-09，定稿）

1. **採 (b)＋修正**：sidecar 語義改 `last_tracked_writer`＋三態（consistent／unattributed_external／ambiguous；consistent 禁叫 verified）；tie 加 ambiguous（寧可錯放不硬判）；actor＝kind＋root＋prompt＋leaf 雙欄（session_id 留 join key）；projection 只說看到誰、verifier 才說信多少。watermark／(e) 列觀察項（batch 語義下邊際價值待實例）。
2. **hook sensor 拆獨立小卡**：CC 側 PostToolUse(Edit|Write)＋FileChanged 先行；ZCode 側維持 (b)+hash（僅 PreToolUse／Stop，無 PostToolUse——分通道覆蓋邊界寫進實作卡）。
3. 排序約束已滿足（AIR-49 Done）；實作另開卡。外部第二意見（ChatGPT 跨 provider 諮詢：same-content／ABA 反例、watermark race、(e) journal、prompt_id）已吸收，handoff 在發起 session transcript。
