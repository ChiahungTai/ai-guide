---
id: AIR-67
title: >-
  CR quick-wins——cr-research 角色定義修正＋symbol query 五步 ladder＋.code-reality.toml
  smoke（cr-audit R2+R4）
status: In Progress
assignee: []
created_date: '2026-09-09 21:43'
updated_date: '2026-09-14 05:22'
labels:
  - cr
  - governance
dependencies: []
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
cr-audit（reports/2026-09-09-cr-role-audit.md）即刻項半小時級。R2：agents/roles/cr-research.md:23 角色定義教錯 module-path query 形態（Class.method/bare name 才對）——修角色定義＋cr-query＋symbol-query-routing 三檔同步（定義源改動 rg 掃引用防 drift）＋五步 ladder 落地（①Class.method/bare→②去 prefix 重試→③LSP/rg 找 canonical→④CR 再查→⑤[WARN] degraded＋禁把 query miss 翻譯成 0 consumers）。R4：ai-rules 補 .code-reality.toml（module prefix/claims extraction）——必須 smoke 驗證（錯 profile 產生更危險自信假陰性）；解鎖 delta_tour EP 宣稱對照＋持久版 tour。驗收：rg 舊形態零殘留＋smoke 產出附卡＋三檔一致性。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔triage 併弧 09-10——升級為 CR 治理總弧（三段連續做）〕段二＝cr-audit R1+R3（negative-claim gate：R1 語義化 gate 牽 review-engine/execution-plan/judge 三檔——claim 四欄結構/negative verdict 永不可用 rg；R3 research.md evidence 載體——EP 同層 references/research.md 機械可驗收）；段三＝R6+R7（外部 runtime 注入：work-order.md:61 過時假議修正＋capability-aware 注入塊 MCP-first→CLI fallback→WARN degraded；fallback 可見化：spawn auth 失敗回報 CR 未遂＋重試一次禁靜默漂移）。提案全文：ai-analysis/reports/2026-09-09-cr-role-audit.md R 行表（:189-196）。

〔開工 2026-09-12〕R2 已由 5dc56cd 落地（cr-research 查詢形態修正＋miss ladder）；reviewer MCP-first 行已在 HEAD（code-reviewer.md:29／code-reviewer-primed.md:16）——原卡 R2 部分轉驗收。剩餘 scope 收斂為兩弧（codex 討論 job-mtxfv83d 定案）：弧A policy closure＝work-order §7「foreign runtime 無 LSP／MCP 面」過時斷言改 available-face 階梯（MCP→CLI→rg degraded [WARN]；禁從 role/template 宣告推定 runtime 有 MCP）＋R7 fallback 可見化（transient 才同 face 重試一次；capability 缺場記 reason 降階不盲重試；spawn auth 失敗屬 dispatch 層不混同）；弧B telemetry closure（施工序固定 collector→replay→trigger）＝cr_usage.py 演化三證據類（structured call evidence＝bridge jobs `item.completed`+`item.type=command_execution` 的 command 欄位〔正樣本 job-mtx2eakq 實證〕／output evidence＝`[SRC]`+「未 index 驗證」指紋、計數名 evidence-bearing outputs 非 CR calls／degraded marker 單獨計）→ 09-11 正樣本＋muse 基線 replay 驗收 → post-build 階段4 獨立條款「CR wiring telemetry checkpoint」（非 AIR-75 子條——政策傳播vs行為量測不同軸；checkpoint≠effectiveness proof）＋schedule-registry #3 描述同步（CR 腿事件觸發為主）。觸及檔：skills/_common/work-order.md、skills/post-build/SKILL.md、skills/corrections-weekly/{SKILL.md,scripts/cr_usage.py}、ai-analysis/schedule-registry.md。R4（ai-rules .code-reality.toml smoke）仍在卡內待做。

〔弧A/弧B 落地 2026-09-12〕弧A＝96ffff4（work-order §7 available-face 階梯＋fallback 可見化；drift 掃描殘留命中僅歷史報告/卡面引用）。弧B＝cr_usage.py 三源三證據類演化（bridge call 證據鎖 command 欄位 schema——正樣本 job-mtx2eakq 入帳、寫入面 0；replay 7d 窗：bridge 279 jobs＝call 3／evidence-bearing 107，db 面 callers 32 sessions，agent 產出 923 files＝evidence 63）＋post-build 階段 4 第 6 點 telemetry checkpoint 條款＋corrections-weekly :29 三源語義與 runtime hook 指針＋registry #3 描述同步。卡剩：R4、段二 R1+R3、弧A 行為面抽驗（下次 review dispatch 後抽 [SRC]／未 index 驗證／CR 呼叫）。

09-13 triage（lite-verify 機械核對）：

**handoff 記「stale 待 triage」不成立**——三弧全落地實證（R2+五步 ladder 5dc56cd／弧A policy closure 96ffff4——work-order:62 三階梯在場／弧B telemetry 882c9b5——cr_usage.py 三源＋post-build:78 checkpoint＋registry #3 全在場）；卡面 notes 與 repo 實況一致。

**剩餘三項**：R4 .code-reality.toml smoke（半小時級，標的不存在屬實）＋R1 剩餘（negative-claim 四欄——核心已被 review-engine:169 R8 吸收，剩結構同步 execution-plan/judge 兩檔）＋R3 references/research.md 載體設計（零命中未落）。弧A 行為面抽驗掛下次 review dispatch 事件。

**處置裁定（user 09-13 拍板）**：剩餘＝雜項尾巴，與 AIR-70 剩餘合併評估清掃 session 批次處理；不宣稱達成。

[09-14 R4 落地 ✅] .code-reality.toml 上線（五 module：scripts/hooks/skills(depth1=skill 名)/tests/deploy＋exclude 六目錄）。smoke 四項：①profile load 反向驗證——壞 profile（exclude 無 slash）被 [FAIL] 目錄粒度 assert 攔下、snapshot 不產出 ②module 歸類正確——26 檔歸 hooks/scripts/skills/tests 桶、變動模組 ai-analysis/ref-docs 正確落 exclude 桶 ③delta_tour claims 管道全鏈通——EP 宣稱抽取→對照→0 命中+多模組變更防呆降級 WARN 正確觸發（R4 擔心的假陰性被攔的實例）④module_edges 0＝真實拓撲（工具集合型 repo 模組間零靜態呼叫；graph rebuild 520 節點/896 邊）。附註：reconciler 等零靜態邊腳本不進 snapshot files（subprocess/動態載入非 profile 問題）。delta_tour 解鎖 ✓——後續弧 EP 宣稱對照可用。卡剩：R1 剩餘＋R3（09-13 裁定歸清掃批次）＋弧A 行為面抽驗（掛下次 review dispatch）
<!-- SECTION:NOTES:END -->
