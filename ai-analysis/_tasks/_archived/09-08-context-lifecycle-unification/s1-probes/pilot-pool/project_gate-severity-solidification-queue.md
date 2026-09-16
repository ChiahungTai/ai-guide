---
name: gate-severity-solidification-queue
description: 治理收斂線終態——AIR 佇列收束、gate 90% 真線＋夜間 cron、bundle 減量三代（95.1%→82%）、治理 brainstorm 診斷、usage 盤點方法
metadata:
  node_type: memory
  type: project
  originSessionId: sess_07836405-5f73-4d17-9619-5456406f7cd3
  merged_from: [project_air-20-rules-bundle-diet, project_ai-rules-governance-brainstorm, project_stale-inventory-usage-audit]
---

治理收斂線：AIR 佇列收束＋gate 放寬＋bundle 減量三代＋治理 brainstorm 診斷＋usage 驅動盤點，全收案。AIR-13 委派面詳 [[agents-registry-split-design]]；memory 治理面詳 [[memory-cc-alignment-diagnosis-0905]]。

## ① gate severity（完結）

- bytes 降 INFO、硬 gate chars/lines、雙端 25,000 chars 事實（勘正詳 [[reference_memory-index-load-truncation]]）；**user 裁決放寬到 90% 真線**（GATE_CHARS 18,500→22,500），條件＝寫入原則配套＋**每日夜間收斂 cron 三軌**（23:40、僅 ai-rules 池：desc>100 輕掃＋波段收斂〔gate FAIL／`_regen-failed`／chars>21,000〕＋`_audit-state` 記帳）。分工：夜間＝流出腿、週日治理 cron＝健檢腿（lite audit）
- P1 desc 硬限 120→100 全同步——**常數變更必重驗 fixture 數學**（TRUNCATE_DESC 使索引行變短，gate 邊界錨要重算）；P2 夜間弧線軟預警腿（單檔 >8,000 chars 且近 7 天活躍＝僅報告不擋）
- 排程報告標頭歸因缺陷（二次肇案後修復）：標頭時間以 `date` 實際執行時間為準、禁自稱手動、禁沿用記憶/池條目時間戳——LLM 自寫的時間與觸發源皆不可信

## ② AIR 佇列治理教訓

- **開卡判準三條**：建卡＝scope 定＋跨 session＋可驗收；draft＝未承諾／觸發型；不進＝session 內消化（user「先都開卡」推翻暫案）；**archive 優於 delete**（退卡可復活，匹配退卡通語義）
- 依賴邊：**同檔兩線禁**（批次一→手術必須序列）；**受影響測試集機械列舉**（cr callers/impact_radius 或 rg tests/ -l，禁目錄直覺——8 個 baseline FAIL 漏網實證）
- **registry drift 首抓＝維護者自己**——動排程的 session 對 registry 有同步義務；排程職責真相只在 CronList prompt、無總覽文檔＝一晚三度失準的根因——**排程 authoritative inventory 是必要交付物**
- 審查可升級 dual-family：GLM fresh-eyes＋muse bridge review 背景並行→合併 findings→judge；AIR-17 驗證弧：排程隸屬 session 巢狀建檔被擋＝**乾淨 session 代建 one-shot 可行**（平台事實）；handoff 內嵌 state-sensitive gate 對 In Progress 卡固定 exit 1＝死鎖——**要改等價跨線檢查**
- mosaic 協作邊界：動 mosaic backlog/ 前先看 staged 集；非本 session 的 uncommitted 殘骸如實 disown 不代清；**ZCode-first（「現在我很少用 cc 了」）＝決策基準**

## ③ bundle 減量線（三代全收；原 air-20 檔，含更早 merged 的 truncation-rule-skill-split＋bundle-diet-wave2-ep）

- **首波·截斷修復**：ZCode 單 instruction 檔 **100KiB 硬編碼**（`zcode.cjs`，無 config、官方文檔未載；重測法 `rg -b -o "100\*1024" zcode.cjs`）——141KB 時代尾部 rules 靜默失效。解法＝**rule/skill reference 分層**（rule 留 always-on 核心＋pointer、深層住 skills/）。**bytes 預算教訓：預算單位是 bytes（CJK 一字 3B）；撞 gate ≠ 成長禁令，是決策點**
- **二波·常態化**：三組 rule→skill 下沉；**`BUNDLE_WARN_RATIO=0.85` WARN 機制**＋per-rule 組成分析配方；**蒸餾產物必過 fresh-eyes agent diff 審查**（語義損失 blocker 級／引用同步殘留／量合理性四軸）
- **三代（AIR-20+22）**：S1 model-routing external-runtime 降級＋路由句去重＋progressive-validation 併入 quality-constraints＋四檔精簡；AIR-22＝modern-cli 陷阱目錄搬薄 skill＋memory 四問搬 memory-audit「寫入端紀律」段——**bundle 95.1%→82% 首次壓回 WARN 線下**。審查鏈教訓：rg `\|` literal-pipe 陷阱（命令寫進 markdown 表格即中招——改 `-e` 形態）；deploy broken-ref guard 不攔刪檔死鏈；**A2 裁決證據：always-on 不防踩（陷阱在 rule 照樣誤犯，防踩靠查詢習慣＋審查鏈）**
- **現值查法（不記現值——drift-prone）**：`uv run python scripts/deploy_agents.py --dry-run`；gate 常數單一源 `scripts/deploy_agents.py`。09-05 複核：夜間 relay 引 95.1% 過時值引發假紅燈——dry-run 實測減量態維持，零行動（[[feedback_relay-claims-verify-current-state]] 實例）

## ④ 治理 brainstorm 核心診斷（全弧完結；報告 ai-analysis/reports/2026-08-29-skill-agent-rules-improvement-brainstorm.md）

「**工具在場、紀律在檔、接線不在生產路徑上**」：①CR 滲透=0——三閘接線全屬 graceful-degrade sidecar，生產路徑從不被迫經過（→ 支持 in-path 必填方向）②治理自我例外（治理工具鏈 0 測試、孤兒 hook）③規則衰減實證（rg|head vs wc 差數量級、python heredoc 319 次、熱點重讀 x18）。對抗驗證鏈有效：flash lite-verify 覆核；**魔鬼代言人抓到致命錯——採信「CR 接線未做」未親驗，git show 直讀推翻——翻案宣稱須親驗才改寫**

- 落地骨架（全線完結）：deploy gate 程式化＋治理工具鏈測試化＋pre-commit；corrections-weekly skill＋mine_corrections.py（**SQL 不內嵌 cron prompt——不入版控會靜默 drift**；scan-project pattern＝機械面沉腳本）；T2-2 deep-thinking 設計翻案＝核心觀念進 `rules/design-thinking.md`（淨省優於單純下沉）；smell-detector 不入 post-build 鏈、改收尾報告 triage 欄
- **CR projected graph 接線**（四檔）：plan `[meta] project` 必須＝index 前綴，否則 minted symbol join 靜默失敗；主索引方向＝query-time lazy 自癒、不做 save-time watcher（incident 是偵測缺口非速度缺口）
- 方法論教訓：**Skill 呼叫遙測是採用的下界**（ad-hoc 口頭路徑繞過 skill——判讀「零採用」前先問有無繞道路徑）；side chat 決策凍結模式（relay 是唯一穩定回流路；決策翻案後已發 handoff 整份重製）；同義反覆測試真實形態＝共享 happy-path 典型數字、邊界值系統性缺席；**變更觸發掃描抓不到存量缺口**——週期任務需存量輪抽查面

## ⑤ usage 驅動過時盤點（方法可重跑）

- **四腿機械普查**：Skill 調用（part 表 `$.tool='Skill'`，**必先過濾 type 再取欄**——text 提及會假命中）＋Read 消費腿（兩 symlink face 都算——**reference 型 skill 零 Skill 調用≠休眠**）＋交叉引用腿（rg 排除自身）＋mtime/git 腿（**rules 是 always-on——零調用不是休眠證據**）
- 結果：84 skills 中 52 有消費證據、33 零使用但零孤兒；Tier A 8 檔零使用已裁決全刪（共同證據＝零 Skill＋零 Read＋xref≤2＋池零提及）；rules 19 條無死 rule
- 教訓：**機械盤點別派 agent**（5 顆 flash lite-verify 全滅——普查/清冊主 session 各一條 SQL/loop 跑完更快更省）；zsh 純量迴圈不分詞現行犯；sed 混 CJK mojibake 靜默壞整條 pipeline

關聯：[[agents-registry-split-design]]、[[memory-cc-alignment-diagnosis-0905]]、[[ai-analysis-restructure-design]]、[[cr-live-faces-roadmap]]、[[gate-commands-state-sensitive]]、[[at-skill-zcode-cron-gaps]]、[[reference_muse-code-cli-facts]]、[[reference_report-server-md-viewer-central-mount]]
