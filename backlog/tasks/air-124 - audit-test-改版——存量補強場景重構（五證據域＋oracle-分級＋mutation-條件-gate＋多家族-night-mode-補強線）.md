---
id: AIR-124
title: audit-test 改版——存量補強場景重構（五證據域＋oracle 分級＋mutation 條件 gate＋多家族 night-mode 補強線）
status: To Do
assignee: []
created_date: '2026-09-17 14:02'
updated_date: '2026-09-17 14:12'
labels: []
dependencies: []
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
測試是 AI coding 最重要防線，但現行 audit-test 是開發期視角的八角度稽核器。本卡把它改版為存量補強場景：程式碼跑一段時間後回頭稽核測試強度並補強。經 bi 深度討論（muse＋codex 帶網搜）＋三輪 flash 查證（兩 repo 測試現況）＋user 三次定向修正（非 TDD／存量場景／多家族分配）後設計定案，等 bi 審卡後開工。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@3b9f1ec〕

〔已決策勿重辯——場景與邊界（user 三次修正）：①audit-test＝存量補強場景（程式碼開發一段時間後發現測試弱→稽核＋補強），NOT TDD——建造管線（Test Construction Contract／RED 流程）屬 test-driven-development skill 領域，本卡剔除；「出生證明接口」最小 schema＝三欄（標注鍵 provenance、值域 S/H/I/N/unknown、存放位＝測試檔 docstring 行或 fixture 檔頭），TDD skill 只加這一句②不改動開發期鏈③單一 health score 廢除〕

〔稽核器重構：④八角度→五證據域：Semantic Integrity（反模式+mock+必要性合併；**承接現行精華段**——PropertyMock type-level 危險性段原文保留＋新增 per-repo mock 豁免教義：被迫正確的環境 API mock 如 vi.mock('vscode')、NT test-kit providers，豁免清單 repo 自持）／Traceability & Evidence Depth（覆蓋對稱+消費端+TC 對帳合併；**角度 8 七項對帳表原文保留**——mock↔evidence class、oracle 圓形依賴、receipt/digest 為最高槓桿三行；有凍結 TC 時升本域第一 gate〔codex〕；**Registry Membership／Method Coverage 流程原文保留**）／Adversarial Strength／Test-System Integrity／Suite Operability⑤新 detector：vacuous-green＋oracle 分級 **S＝具獨立 authoritative oracle_source（規格/領域恆等式/歷史數據，禁待測實作）的 frozen spec/TC——frozen 本身不授予 S（codex 收緊）**；H＝歷史真實數據/真實 carrier 行為，anchor＝dataset/version/hash/record-id（text 類才用 file:line）；I＝impl 衍生；N＝無 oracle——I/N 自動 Important 且**禁 autonomous 補強授權**⑥砍：角度 5 marker 分層＋mock-count heuristic⑦角度 2 改查 behavior impact evidence⑧報告 8 維 vector，gate＝Critical evidence＋P0 mandatory dimensions 缺場〕

〔mutation 三層：⑨P0 critical path 變更弧 scoped mutmut 必跑，gate 判「新增且確認 non-equivalent survivor」⑩普通弧免⑪週期輪抽照舊⑫kill-rate **drop＝investigation signal 不阻擋**（trend telemetry 無 blocking authority——codex 語義漂移修正）；唯一 mutation hard gate＝⑨；mutation feedback 永不取得 oracle 修正權〕

〔域特化指針（圍欄：本卡 SKILL 只留問題陳述＋彼側卡連結，設計細節住彼側）：⑬mosaic determinism gate＋invariant/PBT＋domain-validity guardrail＝MOS 側卡⑭SC 薄改清單：**message protocol contract schema 化列首位（codex 首要投資——protocol contract >> E2E）**＋trace/retry（uncommitted 前提：開工前確認落定，commit hash 回填卡 notes，未落定 defer）＋selector 漸進＋vitest coverage＋flake census⑮coverage＝trend telemetry 非 gate（mosaic test-cov uncommitted 前提同⑭）〕

〔多家族 night-mode 補強線（user 設計要求——原話追認：半夜補強＋按家族數分配用法）：⑯分配軸＝獨立性需求×判斷密度×成本⑰五段管線：P1 掃描（flash——findings ledger 分段落盤）→P2 跨家族盲審（muse+codex bridge 並行，target manifest 見㉓）→delta 二分→P3 裁決（decision-qualified judge）→P4 補強生產→P5 機械驗收。**P4 契約（codex 修正——RED 字樣刪除）**：補強測試驗收＝canonical baseline GREEN＋targeted mutant/negative-control RED；S/H oracle 導出的測試使 baseline RED＝抓到 production defect→pending-decisions（夜間禁改 production code）；**P4 admission＝S/H oracle authority＋三證據鏈（spec/invariant oracle＋property/metamorphic/differential＋mutation challenge）合格才可自動進**——survivor 只能指出 probe 位置、不得決定 expected outcome（封閉迴圈防護——oracle 可不變而 test 被 survivor steering 的繞道封死）；P4 只寫 tests/fixtures，禁改 spec/oracle/production source⑱**家族適配＝per-stage availability（codex/muse 雙腿修正——非管線級 tri/bi/single 一個數字）**：P1/P2/P3/P4 各自 resolve AvailabilitySnapshot；GLM 撞 1308（家族級）→flash 掃描腿預設不存活（除非 flash 有獨立 fresh snapshot=available）；**P3 無 decision-qualified judge→夜間停在裁決隊列，禁進 P4**；降級記錄＝panel=single＋degradation receipt（explicit_same_family_degradation 是 independence 欄狀態非 panel token——codex 詞彙修正）⑲夜間可用性以 spine 事件＋三訊號判定，不預設任一家族充裕⑳落盤：.partial.md 分段＋durable sink＝**repo adapter**（mosaic inbox 慣例；無 inbox repo fallback＝daily-report 或 .agent-tmp＋晨間報告）21 autonomous 紅線：不 commit；夜間止於 P5 證據齊22 delta 歸類三選一（spec 歧義→修 spec／單邊漏→聯集／兩可→user 裁決）＋oracle stable anchor〕

〔㉓ night-mode 八契約（codex/muse 缺口全收——skill 條文必載）：(1) target manifest：P1 前凍結、兩 blind reviewer 同一份 targets，來源＝AGENTS critical/ripple＋dependency-graph hotspots（沿用角度 7 輪選），**禁 P1 findings 決定 P2 targets**（獨立性污染）(2) blind input contract：P2 工單明示禁讀清單（P1 .partial.md／daily report／另一 reviewer output）；如實標注＝procedural blindness 非 hard isolation（hard 隔離待實作期 sandbox 驗證）(3) delta identity：canonical key＝target/module＋behavior/predicate＋oracle anchor；交集定義＝support-count ≥2（寫死）(4) mutation baseline：pre-P4 survivor set＝獨立機械 pre-run 產（P1 不跑 mutation）；P5 同 scope/operator/config rerun 得可比 delta(5) P4 admission/exit＝⑰(6) stage-specific degradation＝⑱(7) durable sink resolver＝⑳(8) morning readout owner＝P5 completion aggregator 唯一生產者，從 immutable ledgers＋P3 決策記錄＋P5 receipts 組裝（禁 reviewer 自述摘要）〕

〔㉔ 三輸入模式處置：Daily Scan→night-mode 吸收（night-mode 即 Daily 的強化形態）；Diff/Commit Audit 保留接 pre-commit gate 與段落收斂。㉕ oracle 正典歸宿（審卡定案——codex 建議採納）：rules/acceptance-evidence.md 加一條正典（S/H/I/N＋frozen 不授予 S＋I/N 禁 autonomous 補強授權）＋細則下沉 skills/acceptance-evidence/SKILL.md；execution-plan/audit-test/fix-test 三處只引用不重寫〕

〔審查紀錄：設計鏈＝web 研究＋bi 設計討論（muse mu5kt9v4/codex mu5kvs0u）＋flash 三查＋user 三修；**審卡鏈（user 指示）＝muse mu5lp8ss（needs-fix：F1 ⑱矛盾/F2 P4-RED 矛盾/F3 出生證明 schema/F4 精華段歸宿/F5 輸入模式/F6 AC 缺口/F7 uncommitted 前提/F8 指針圍欄/F9 web pool 表述＋7 night-mode 缺口）＋codex mu5lrksz（needs-fix：P4 驗收重設計/authority gate 關閉繞道/三證據鏈 admission/per-stage availability/panel token 修正/drop≠紅/S 收緊/H anchor＋8 契約）——16 findings＋8 契約全數吸收進本版**；verdict 全文 .agent-tmp/dispatch-compiler-proposal/air124-*-verdict.md〕

範圍——改：skills/audit-test/SKILL.md（五域＋精華段歸宿＋vector＋night-mode 節含㉓八契約＋輸入模式處置）；skills/test-driven-development/SKILL.md（出生證明接口一句）；rules/acceptance-evidence.md（oracle 正典一條）＋skills/acceptance-evidence/SKILL.md（細則下沉）。
明示不動：implement/post-build 開發期鏈；mosaic/SC repo 本體；model-routing panel 詞彙（複用不改）。
AC：①五域結構＋精華段歸宿（角度 8 七項表/PropertyMock/Registry Membership 原文在場於對應域）＋vacuous-green＋oracle 分級 detector 在場②health score 移除＋vector 模板③mutation 條件 gate＋trend line＋**trend 不具 blocking authority 明文**④night-mode 節含㉓八契約（target manifest/blind contract/delta identity/mutation baseline/P4 admission/stop-before-P4/readout producer/sink resolver 全在場）⑤角度 2 修正⑥TDD 剔除＋出生證明三欄接口（僅一句）⑦**三證據鏈 admission＋mutation feedback 禁決定 oracle/expected value 明文**⑧砍除驗收（marker 分層/mock-count heuristic 条文不在即過）＋㉒歸類表＋oracle anchor 欄⑨mosaic/SC 指針段（圍欄：問題陳述＋連結）⑩instruction-writing 審查閘（boundary 跨家族——結案條件）。
<!-- SECTION:PLAN:END -->
