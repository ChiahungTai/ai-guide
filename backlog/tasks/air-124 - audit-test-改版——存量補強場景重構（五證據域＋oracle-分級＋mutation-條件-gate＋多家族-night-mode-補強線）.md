---
id: AIR-124
title: audit-test 改版——存量補強場景重構（五證據域＋oracle 分級＋mutation 條件 gate＋多家族 night-mode 補強線）
status: To Do
assignee: []
created_date: '2026-09-17 14:02'
updated_date: '2026-09-17 14:03'
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

〔已決策勿重辯——場景與邊界（user 三次修正）：①audit-test＝存量補強場景（程式碼開發一段時間後發現測試弱→稽核＋補強），NOT TDD——建造管線（Test Construction Contract／RED 流程）屬 test-driven-development skill 領域，本卡剔除，僅留「出生證明查核」接口（存量測試標 provenance:unknown）②不改動開發期鏈（implement/post-build 的段級審查）——audit-test 仍是獨立稽核器＋新增補強生產線③單一 health score 廢除（100 個漂亮 CRUD 測試沖淡一條 cash invariant Critical——codex）〕

〔已決策勿重辯——稽核器重構：④八角度→五證據域（codex）：Semantic Integrity（反模式+mock+必要性合併；核心問題＝oracle 是否獨立/assert 對應 claim/impl 污染）／Traceability & Evidence Depth（覆蓋對稱+消費端+TC 對帳合併；mapping＝requirement/invariant→TC predicate→test→consumer path→evidence class）／Adversarial Strength（mutation+property+metamorphic+differential）／Test-System Integrity（新：flake/isolation/fixture provenance/seed determinism/stale golden）／Suite Operability（分層+runtime budget+first-pass/flaky/fail+slow-test 分佈）——muse 的 detector 細節保留進域內⑤新 detector：vacuous-green（條件式斷言——test_accounting.py:20-72 實證：if-in 包 assert 在計數下是健康測試）／oracle 分級 S（frozen spec/TC）>H（歷史真實數據）>I（impl 衍生）>N（無 oracle）——I/N 自動 Important⑥砍：角度 5 marker 分層（mosaic 已實證廢棄）、mock-count>assert-count heuristic（mock 錯誤 boundary 比 20 個 mock 危險）⑦修：角度 2 的 source↔test diff 對稱訊號與凍結 TC 制度矛盾（GREEN 期 source 演化 frozen test 不變＝理想態）→改查 behavior impact evidence⑧報告改 8 維 vector（semantic_integrity/traceability/critical_invariant_coverage/path_evidence/adversarial_strength/fixture_provenance/flake_isolation/suite_operability），gate＝Critical evidence 存在與否+P0 mandatory dimensions 缺場，分數類指標只作 trend telemetry〕

〔已決策勿重辯——mutation 三層（codex+muse 收斂）：⑨P0/silent-corruption critical path（會計/風控/單位/時區——AGENTS.md critical path 清單）變更弧＝scoped mutmut 必跑，gate 判「新增 non-equivalent survivor」非全 repo 分數閾值（mosaic 實證 8.2s/模組、87.4→97.1%）⑩普通弧免（防噪音稅）⑪週期輪抽存量照舊⑫kill rate 進 per-module trend line（drop 即紅）——mutation feedback 永不取得 oracle 修正權（封閉自洽迴圈防護）〕

〔已決策勿重辯——域特化：⑬mosaic determinism gate：backtest hash 斷言（同 config+seed→digest 全等——現全 repo 零 seed/hash 斷言，鐵律無人守）；invariant/PBT（會計守恆/風控上限/冪等）＋Hypothesis rule-based state machine（order/fill/cancel/replay 序列）＝mosaic 側卡（MOS 開在 mosaic backlog——本卡只出設計指針）⑭SC：pwspec 已達行為級契約水準（flash 查證 48 檔）——補強＝trace on-first-retry+retries:1（已落 uncommitted）+selector 漸進（getByRole/testid 優先新斷言）+vitest --coverage 一行+flake census⑮coverage 定位＝trend telemetry 非 gate（mosaic test-cov target 已落 uncommitted）〕

〔已決策勿重辯——多家族 night-mode 補強線（user 設計要求——妥善利用 2-3 家族）：⑯分配軸＝獨立性需求×判斷密度×成本，非能力強弱⑰五段管線：P1 掃描（GLM flash in-harness——便宜高量，angles+oracle 分級草案，findings ledger 分段落盤）→P2 跨家族盲審（muse+codex bridge 並行——top-risk 模組各自獨立產弱點評估+補強建議，互相 blind 不看 P1）→delta 二分（交集＝高信心 findings；差集＝裁決隊列——derivation-delta 的 audit 版）→P3 裁決（GLM 5.3 judge——delta 歸類+survived mutant triage equivalent/real，判斷密集位不降級）→P4 補強生產（flash 或 muse implement——寫測試 RED→GREEN）→P5 機械驗收（mutation rerun kill delta+pytest+coverage trend——零 model）⑱家族數適配：三家在=tri 形態；兩家=bi（如 GLM 撞牆：muse+codex 盲審+flash 掃）；一家=single+explicit_same_family_degradation 顯性降級——複用 model-routing panel 詞彙非新發明⑲夜間經濟學：codex web pool 充裕/GLM 離峰 1x/muse request 計費——三家夜間剛好互補⑳落盤契約：findings ledger 用既有 .partial.md 分段；durable sink＝daily-report/pending-decisions inbox（mosaic 慣例）；晨間 readout＝交集 findings+裁決隊列+kill trend 三件21 autonomous 紅線：不 commit；P4 產物進 branch working tree；夜間止於 P5 證據齊，人類晨審後才 merge22 spec 理解分歧收割（user 追問）：blind-derive delta 歸類三選一（spec 歧義→修 spec／單邊漏→取聯集／兩可→user 裁決）＋oracle_source 釘行號〕

〔審查紀錄：設計鏈＝web 研究 4 搜（tautology trap/mutation guardrail/PBT oracle/spec-driven 共識）＋bi 深度討論（muse job-mu5kt9v4：test_accounting vacuous-green/PBT=0/hash 缺席/正負樣本；codex job-mu5kvs0u：五域重構/角度 2 矛盾/封閉迴圈/三證據鏈/健康度 vector）＋flash 三查（coverage 兩 repo 現況/SC pwspec 品質/mosaic UI 品質）＋user 定向修正×3——verdict 全文 .agent-tmp/dispatch-compiler-proposal/audit-test-*.md；本卡開卡後再經 muse+codex 審卡（user 指示）方為定稿〕

範圍——改：skills/audit-test/SKILL.md（主體改版：五域+新 detector+vector 報告+night-mode 節）；skills/test-driven-development/SKILL.md（僅加「出生證明」接口一句——非本卡主體）；rules/acceptance-evidence.md 或 quality-constraints（oracle 分級 S/H/I/N 正典一句——歸宿審卡定）。
明示不動：implement/post-build 開發期鏈；mosaic/SC repo 本體（⑬⑭⑮的落地各在彼側——本卡出指針）；model-routing panel 詞彙（複用不改）。
AC：①SKILL.md 五域結構+vacuous-green/oracle 分級/flake census detector 在場②health score 移除+8 維 vector 報告模板③mutation 三層條件 gate 條文+trend line④night-mode 節（五段管線+家族適配+落盤契約+autonomous 紅線）⑤angle 2 矛盾修正⑥TDD 介面剔除+出生證明接口⑦instruction-writing 審查閘（boundary 跨家族——即本卡審卡腿延伸）⑧對 mosaic/SC 的設計指針段落（invariant/PBT/hash gate/SC 薄改清單）。
<!-- SECTION:PLAN:END -->
