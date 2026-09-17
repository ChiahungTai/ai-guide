# .review/air-70.md — AIR-70 段二判準回填審查帳本

## Header identity
- branch: air-70
- reviewed revision: working tree（In Progress commit `0ad7c78` 之後的 uncommitted diff——AGENTS.md 4 行＋skills/memory-audit/SKILL.md 25 行）
- uncommitted identity: 修正迴圈後最終態（5 fixes 套用後；pytest 364 passed）
- 審查 profile: 7 軸（faithful/語義/inbound/drift/decision-replay/authority-hygiene/decoder-regression）——5.3 獨立審＋codex webgpt-high（--session-id 連續三輪：確認→審查→互改複驗）
- 去重判定: 本帳本為雙審查收斂後的**證據落帳**（findings 原走對話與 materials txt，依 post-build 證據身份比對規則補帳本；非重新審查）

## Findings 與裁決

| id | 發現者 | 內容 | 裁決 | 處置 |
|---|---|---|---|---|
| F1 | 5.3＋codex（獨立同抓） | 一行流 L162 漏改（派工清單漏 codex r2 diff C 段；自驗 pattern 配不到「每次都要＝rule」） | ✅採納 | 已修：一行流改「先套層級硬閘→…→rule 資格公式（含完整 disjunct）→最小 rule」 |
| F2 | codex（5.3 漏） | A row/Q2/Q6 把 residency 三測試寫成 qualification 替代品——TDD 反例：出現得早但無校準/裁定/bootstrap 不配 rule | ✅採納（全三處） | 已修：三處改「rule 資格公式＋residency 三測試」pointer 形；Q2 刪 shortcut |
| F3' | codex（5.3 漏） | L146「deployment contract…見 instruction-writing skill」＝broken present-tense pointer（該 skill 無此 contract——rg 三關鍵詞 0 hits 實證） | ✅採納＋修正案 | 已修：改「projection 機制尚未落地（落地弧＝AIR-85），落地前不得據此排除 non-CC bundle body」——codex 複驗採納（讀過 AIR-85 卡認證 future-work 準確） |
| 5.3-F3 | 5.3 | AGENTS.md:117 軸名枚舉「常駐-按需」vs 新表 residency | ⚠️ defer | 術語清理延後（codex 同意：軸名摘要＋同句有 SSOT pointer，非 correctness blocker；與 memory-audit L3 description 同類一體處理）——列入收尾報告待 user 確認 |

## 複驗證據（雙方收斂）
- 六 negative patterns（每次都要＝rule／每次都要的紀律／每次 session 都需要／首個有後果決策前必須在場→最小 rule／依 residency 三測試判定／deployment contract）active scope 全 0 hits
- codex 最終輪：7 軸全 PASS、decision replay 4/4（TDD→skill、port 慣例→project carrier、commit consent→rule、mermaid→skill）、decoder regression 9/9、0 新 finding
- 5.3 judge 三防線：findings 全機械複驗；sycophancy 雙向檢驗（5.3 否決一項＋codex 自我修正其 A row 草案）；無 inferred-only 採納

## Verdict
**收斂——可進 post-build docs 鏈。**（code 鏈 docs-mode 以本帳本＋materials txt 為證據閉環）
