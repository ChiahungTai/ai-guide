# S5 報告：family 重構（minimal）

> parent: `s5-ep.md`（master AIR-45 blueprint）。決策 9（S2 入口最小）＋決策 10（writing 為 desc 文法定義源）落點：S5 走最小範圍，零 rule 改寫。

## 改了什麼（4 檔，共 +30/-3 行級）

| 檔 | 改動 | 行數 |
|----|------|------|
| `skills/instruction-writing/SKILL.md` | ＋`### Capabilities desc 文法與分類層級（AIR-45，本節為定義源）`：desc 正則 `^_cap_[a-z0-9_]+$`、L1/L2/L3 判準表、座標四列、寫入門檻（先有可執行入口才寫行）、觸發透明度（判準只讀 desc＋topics）；slim：映射表條 L126 末句壓為 cross-ref（與「既有映射表的 drift 查證」重複，實證冗餘） | 28,043B → 28,917B（＋874B；slim 有界：全文其餘無可證冗餘，不硬壓） |
| `skills/instruction-init/SKILL.md` | ＋Capabilities 初值（空表＋有入口才填行＋desc 文法引用）＋新層骨架四要素（定位＋種子＋Capabilities＋Boundaries；topics 未載入標 `待補` 禁捏造） | ＋4 行 |
| `skills/instruction-clean/SKILL.md` | NEVER 清單＋分類判準與座標行（壓掉即觸發鏈斷裂） | ＋1 行 |
| `skills/instruction-sync/SKILL.md` | 應該新增＋分類判準與座標行、S4 處置寫回澄清（禁只改散文不改判準行） | ＋1 行 |

## 未做（有意）

- writing 28KB 未大瘦身：全文已讀（1–384 行），除 L126 一句外無可證冗餘；方法論權威檔硬壓＝drift 風險＞token 收益。真實省 context 由 S2 pilot-merge＋rules slim markers 承擔（S3 已做）。
- 零 rule 改寫（決策 9）；`version/` 下四檔原樣快照已存（含 sha256，見 S5 工作記錄）。

## 驗證

- `uv run pytest tests/ -x -q`：207 passed（S5 編輯後）。
- audit：節名子串 4/4（rg）；三處引用寫法各異（init 帶（AIR-45）後綴、節標題另有「，本節為定義源」後綴）——同指一節，無歧義（F1p 回應）。
- F3 處置（s2 登記 rules-16-frontmatter）：S5/S6 已做 skills＋roles 文法對齊；rules/ rank＋觸發 desc 仍無消費者（bundle rank 排序待全量機制），再延期至後續弧（owner 待定），非蒸發。

## clean/sync 新入口走查（codex 終審 C3 補證據——S4 案例經改寫後入口重跑；**主 session 指令走查**）

### C2「rules slim 指針完整性」——處置＝保留（no-op）

- **被檢查的實際內容**（s4-report C2 定義）：5 檔 bundle skip markers 配對（acceptance-evidence 2 對／design-thinking 4 對／edit-discipline 3 對／llm-output-convention 2 對／must-execute 1 對——**12/12 全 PAIRED**，逐檔 rg 實測）＋collaboration-constraints YAGNI 1-line 指針的目標在場（acceptance-evidence skill YAGNI 判別材料 rg 命中）＋無懸空引用（freshness 三端 MATCH 隱含——marker 內容仍可完整重建）。
- **經新入口的處置**：clean NEVER 清單（SKILL.md:67）→ slim markers 與指針屬既有承載、完整性檢查通過 → 處置＝**保留、不壓縮**；sync「應該新增」段（SKILL.md:65）→ 無源變更 → **無寫回**。
- **no-op 對帳（固定 hash 錨，不綁 staging）**：C2 五檔走查後 shasum＝acceptance-evidence `5104c94a…`／design-thinking `8c56c2a3…`／edit-discipline `54397eb8…`／llm-output-convention `aec20166…`／must-execute `77803f1c…`——前兩檔與走查時記錄值**逐字一致**（走查前後未變）；走查為純文件操作、無寫入路徑。`git diff --name-only -- rules/` 僅 rules/AGENTS.md（C1 修正，非 C2 標的）。

### C5「Arm C 生成器」——證據不足不處置＝HOLD（no-op）

- **經新入口的處置**：S4 判準（證據不足 → HOLD，不裁淘汰/晉升）；clean NEVER 清單 → HOLD 態不觸發壓縮；sync → 無源變更無寫回（「禁只改散文不改判準行」反向同理）。
- **no-op 對帳（固定 hash 錨）**：C5 相關 freeze 三檔走查後 shasum＝freeze-answers `a2c98a0c…`／freeze-tasks `8408795b…`／freeze-manifest `9cc81b97…`。其未提交變更＝muse S1 **T18 重凍結**（早於走查、diff 性質抽查證實：T18 前置改「真實 session＋恢復包」）——非走查造成；走查零寫入。

**基線變動註記**：走查後 HEAD 新增 `cab99d7`（AIR-47 建卡 commit，僅含卡檔、與本批無關）並清空 staging——早前「與 staged blob 比對」的觀察已改綁上述固定 hash（codex 三輪 C3 指正）。引用命令應帶完整 repo-relative 路徑（`git diff --name-only -- ai-analysis/_tasks/09-08-context-lifecycle-unification/s1-probes/`），避免 repo root 相對路徑查錯。

**方法論標記**：主 session 指令走查（依改寫後 clean/sync 指令逐案執行並機械對帳）；非獨立 agent 盲測、非 L2 單元測試證據。S4 案例集與判準單一源（s4-report＋memory-audit 引擎段）未動。
