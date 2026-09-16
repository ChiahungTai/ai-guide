---
id: AIR-48
title: 載體濫用鑑識×統一定義表——對話紀錄實證 memory/bundle/skill 誤置（AIR-45 dogfood 證據腿）
status: Done
assignee: []
created_date: '2026-09-08 12:22'
updated_date: '2026-09-09 04:17'
labels:
  - memory
  - governance
  - context
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-08-carrier-misuse-definition/index.html
  - ai-analysis/_tasks/_archived/09-08-carrier-misuse-definition/ep.md
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔baseline：ai-rules d00bfe2〕〔已決策勿重辯：①北極星＝稀缺性分層（L2/HBM/DRAM/HDD 類比＋四判準——AIR-45 EP「User 核心定調」段）②任務狀態/暫存→scratch（.agent-tmp）/卡/EP，不進 memory（六問 Q1；user 09-08 再證 sessions「繼續濫用」——紀律灌輸已證弱，修法走預設路徑改道）③specimen 鑑識定案：sess_5220505c 對兩池條目≈30 Write 草稿式迭代（24+32 呼叫）；正確載體＝卡 notes/scratch＋結案一次性蒸餾④歸因破口：originSessionId 只記創建者（後續 writer 不可見）＋rollout session 結束即清（證據發現當下抽取）⑤分析腿派 flash agent；運作方式先定案（user 指示）⑥濫用面＝memory＋bundle(AGENTS.md)＋skills 三面⑦**AIR-45 殘餘移交**：B 上線切換＝本卡 Phase 3；catalog live 單探針補驗隨手做；mosaic 層級軸歸 mosaic 側 session（判準表在 s3-report）⑧階段序：P1 鑑識（證據是過去式，早跑）→P2 統一定義表 v1（三處判準合一：六問載體判定×writing 決策樹×收斂落點慣例）→**P3 B 上線切換＝定義表首次執法**（live MEMORY.md→12 常駐＋inventory＋工作節點；常駐集合依 P1 證據修正）→P4 dogfood 迴圈〕〔驗收：①近 3-7 天對話紀錄橫掃→誤置 taxonomy＋頻率＋session 歸因表 ②統一定義表 v1（載體職責×常駐-按需×寫入預設交叉表；每類誤置→處置設計，預設路徑改道優先）③**B 上線切換完成＋切換後 dogfood 首輪行為對照**（找得到/用得出）④後續 writer 歸因可見性修法建議 ⑤catalog live 探針補驗 ⑥產出＝任務家報告＋定義表；specimen 編入〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 誤置 taxonomy＋統一定義表初稿交付（specimen 編入）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【P1 完成 09-08 晚】taxonomy 交付（任務家 p1-taxonomy.md）＋主 session 三輪抽驗通過。數字校正：desc ③ 原載『≈30 Write』係 rollout 膨脹計數假象——db 真值 2ok+2err（specimen 定性不變更強：2h≥5 寫入≥4 身份）。SM-5 破口量化 71/128+73/106。bundle 面無確證 scope creep。hook 在已實裝面完全有效（MEMORY.md 直寫 0 次）——缺的是放置閘＋desc 內容閘。下一步 P2。

【P2 完成 09-08 晚】統一定義表 v1 交付：本體=memory-audit SKILL.md 新節「載體統一定義表」（九載體交叉表＋該寫哪一行流＋誤置→處置＋摩擦設計），審計副本=任務家 p2-definition-table.md（D1-D8＋Decoder test 9/9 反查通過）。指針鏈五處同步（instruction-writing/AGENTS.md/rules/context-management/memory-audit 內三處）＋memory 條目段名 drift 修正。驗證=rg 殘留零＋consistency 96/100。殼 hook 1 補建＋卡 ref 換殼 URL。摩擦設計定案：放置閘=提醒注入（語義留 LLM）、desc 內容閘三判準全過可硬擋、工具層不做——實作另裁。下一步 P3（B 切換，規格全在 EP P3 段含 R1-R5）。

【P3 完成 09-08 深夜】B 上線切換完成（user 確認凍結 12 條）：generate_index B 形態分流（清單檔 opt-in；唯一解析鍵=stem——6/128 條 fm name 分離實證；R2 fail-loud 三形態；R3 先 inventory 後常駐面；gate B=6,000/A=22,500）＋hook 擴 _inventory.md 手寫防護＋SKILL 三處同步。測試 14 條新增（lifecycle 65 綠/全套 222 綠）。live 切換：開場面 20,794→2,244 chars（-89%）；mosaic 三池 A 形態驗證不變；R4 實測常駐面 UNCHANGED＋inventory 信號口徑成立。回滾：池=先移 _resident-set.md 再 regen。下一步 P4 dogfood（3-5 session/48h 逐案四欄）。（註：backlog CLI spawn ENOENT 三連失敗——本段以檔案 Edit 直寫）

【P5 完成 09-08 深夜】①catalog 真通道探針：源碼查證（render.rs 三層階梯＋System→Admin→Repo→User 省略序、USER scope 最尾）＋live 探針 11/12 exact＋tier-2 縮短警告實彈（94 skills 真預算零省略下可達）——SM-7 關閉；清理 94→82 diff 零差異。②writer 歸因建議：三案四維矩陣推薦 (b) telemetry last-writer 投影，三 user 裁決點標出。P4 dogfood 窗口開放（case#1 三段已記，n=1/3-5，48h 至 09-10）——首輪結束回餵＋結案兩步。產出隨批 commit（p5-codex-catalog-probe.md／p5-writer-attribution-proposal.md／dogfood 記錄）。

【09-09 合併】user 裁定 AIR-48 剩餘（P4 dogfood 收尾——窗口至 09-10＋P5 三 user 裁決點＋統一定義表 wrapper 條目）併 AIR-50 整合弧執行——EP：ai-analysis/_tasks/_archived/09-09-skill-contract-fixes/ep.md（S9 段）；結案兩步隨該弧
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
P4 dogfood n=2收斂（case#2本弧＋ID核對事件；窗口至09-10晚無新case即定稿）＋M5 wrapper條目＋P5裁決點彙整（①採b②維持觀察待user裁決；③已滿足）
<!-- SECTION:FINAL_SUMMARY:END -->
