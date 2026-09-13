# AIR-85 EP——條件載入層 vertical slice（bundle-mode marker＋deploy 投影，instruction-writing pilot）

> **ep_type**: implementation
> 卡：AIR-85（To Do → 開工時 In Progress＋雙 ref）。baseline＝main @ f6150fd（AIR-86 已結案）。
> 材料源：reports/2026-09-13-scope-boundary-memory-rules-skills/report.md §3.4＋materials/codex-followup-out.txt §A（三軸分離設計全文）＋materials/leg5-probe-paths-verdict.md（paths: probe 實證）。

## UC 盤點

### Backlog 關聯
- AIR-85（本卡）；下游相依：AIR-87 skills 治理（desc 契約）、AIR-86 已結案（python-standards「AIR-85 前禁 pointer-only」銜接點解除等待）
- 自動建卡：無新 UC（deploy 能力擴展屬治理腳本，以卡＋rules/AGENTS.md 承載）

### SYSTEM-MAP 影響
- 無（無 SYSTEM-MAP.md）

### 掃描範圍
- scripts/deploy_agents.py（read_scope L168-188／discover_rules／bundler L321-338／slim_for_bundle L304-318）＋tests/test_deploy_agents.py（364 tests 基線）
- rules/instruction-writing.md（pilot 對象：已帶 paths: **/*.md＋配對 skill＋guide L5 bootstrap 句）

### 同主題 memory 條目（結案蒸餾範圍）
- reference_codex-cli-exec-facts／reference_muse-code-cli-facts（正交）；無條件載入主題既有條目——零衝突

---

## 段落 0：全域研究（已完成，材料引用）

1. CC `paths:`＝Read-trigger lazy inject（L4 probe 實證：load_reason=path_glob_match；對照組零事件；新建檔首 Write 前無 matching Read＝已知洞——python-standards blocker 依據）
2. deploy 現況只解析 `harness-scope:`；三 rule 已帶 paths:（instruction-writing/llm-output-convention/python-standards）——**`paths:` 單獨作非 CC 排除訊號＝retroactive semantic migration，禁止**（codex A1）
3. pointer 語義＝作者寫（source 同檔）＋deploy 只機械投影＋fail-closed（codex A2）；處理序固定 harness-scope → target eligibility → projection mode

## 段落 1：projection metadata parser＋schema validation（TDD）

**Context**：三軸分離的第三軸需要顯式 opt-in marker。codex 討論輪（09-13，materials/air85-ep-discussion）定名 **`bundle-projection: pointer`**——語義對應第三軸「portable bundle 如何投影」，非 rule 本身 mode。

**要點**：
- frontmatter 三鍵 schema（flat keys，machine-readable）：
  - `bundle-projection: pointer`（僅此一值；full body 為預設不標）
  - `pointer-target: instruction-writing`（限 skill-id slug，禁 `../` path interpretation）
  - `bootstrap-pointer: "<作者明寫 trigger 句>"`（逐字 materialize）
- **deploy 不解析 `paths:`**（契約一）：parser 只碰 `harness-scope` 與 projection 軸——`paths:` 是 CC runtime 軸，結構上隔離
- schema 四 invariant（解析期 fail-closed，段 1 落地非段 2）：`pointer` mode → target/pointer 必須齊；未知 mode value → fail；無 mode 但有 target/pointer 鍵 → fail；target 非 slug → fail
- 矛盾組合（`claude-specific`/`meta` 帶 projection）→ hard fail（契約：typo 不得變 deployment semantics）
- **新增 `read_rule_meta()`**，`read_scope()` 保留為 compatibility wrapper（不重寫既有 caller/tests API）

**驗證策略**：test_deploy_agents.py——三鍵解析、四 invariant、矛盾組合、既有 read_scope 測試回歸不變。

## 段落 2：投影機制＋全域 preflight（TDD）

**Context**：bundler 投影＋fail-closed 三驗。**契約二：projection validation 是全域 preflight**——現行 main() 是 per-target 獨立 build/deploy（某端失敗其他端照部署，partial deploy 是既有設計 deploy_agents.py:448-506）；pointer 三驗必須在**任何 target write 之前**全域跑完，不得在 per-target loop 中後段發現。

**要點**：
- `project_rule_for_bundle(path, meta) -> str` 純函數（full mode → 既有 `slim_for_bundle()`；pointer mode → **凍結模板的 provenance 註解** `<!-- pointer projection: on-demand body not shipped in this bundle; full text -> skill \`{target}\` (load the skill when triggered) -->`＋pointer 行 only——不殘留 frontmatter/body；註解屬確定性 provenance 模板非觸發語義，09-13 oracle 裁決後明定）；第二支（llm-output）起走同介面，零 special-case filename
- **deploy 冪等零寫入**（09-13 superpowers 借鑑補入）：identical bundle 重跑時跳過 stage/replace（內容比對後零寫入、mtime 不變）——oracle A12 契約
- preflight 三驗（real deploy 與 `--dry-run` **共用同一 preflight**，只差最後 write——否則 dry-run 綠真跑 fail 的假驗收）：
  1. target skill **source** 存在（repo `skills/<target>/SKILL.md`）
  2. pointer 行在場（bootstrap-pointer 非空）
  3. **runtime 可達**：`~/.agents/skills/<target>/SKILL.md`（non-CC 三家 canonical portable root——codex/muse 官方文檔實證＋ZCode 掃描規範）
- 任何一驗失敗＝deploy 整體 exit≠0，禁靜默
- **projection 先發生、再計 bundle bytes/size gate**（build_bundle 產投影後內容；ZCode/Codex 90KiB、Muse 36KiB 兩 gate 值不動）
- known limitation 記 interface debt：`check_broken_refs()`/`check_neutral_purity()` 掃 full source 非 projected representation——pointer body 不 ship 仍可能被擋（false-positive 面），vertical slice 不改，記 EP 尾

**驗證策略**：TDD——正常投影（header+pointer、無 body 無 frontmatter）；三驗各壞各 fail；全域 preflight 測試（壞 Muse 可達性時 ZCode/Codex 也未寫出）；dry-run 與真跑同 invalid marker 同 exit≠0；無 marker 檔案 byte-identical 回歸。

## 段落 3：pilot 標註＋全端驗證

**Context**：instruction-writing golden pilot。**契約三：AC#2 驗 CC runtime semantics 不變，非 byte-identical**——pilot 必然新增三個 frontmatter keys，CC 端「原樣」定義＝既有 `paths:` 與 rule body 不動＋新增 metadata 不改 path-trigger 行為。

**要點**：
- rules/instruction-writing.md frontmatter 加三鍵；bootstrap-pointer 句（codex 潤稿版，user 確認）：
  > **新增或修改 AGENTS.md、CLAUDE.md、rules 或 SKILL.md 等 instruction 檔前，先載入 `instruction-writing` skill；frontmatter、載體選擇、引用、Signal/Noise 與自洽檢查以該 skill 為準。**
  （trigger＝「新增或修改 instruction 檔」非「看到 Markdown」——不過度觸發；不攜帶 CC 專屬 paths 細節）
- 真跑 deploy：三端 bundle diff 舉證＋bytes 前後量測入卡 notes（預估 −0.86KB）
- **CC 端兩層證據**：①靜態 diff 證 body/paths 不動；②**L4 runtime probe**（升級為 pilot gate 非 unverified 放行）——沿用 leg5-probe 模板：同 path-scoped rule 加 projection unknown keys 後，matching Read 仍 `path_glob_match` 注入、對照組零注入。probe 不過 → fallback 設計（metadata 移出 CC 解析的 YAML 形態）回到討論

**驗證策略**：AC#1（三端 diff）＋AC#2（兩層證據）＋AC#4（deploy 全端綠＋量測）。

**測試設計細節（superpowers 研究借鑑，materials/superpowers-testing-research.md）**：
- S6 probe 雙場景對稱：(1) 含 projection keys 的 rule 在 CC 端 matching Read 仍注入（load_reason=path_glob_match）＋無 loader 錯誤；(2) 對照組正常——判準＝**行為非文本**（勿只驗 source 含 key）
- pointer 行為兩層：機制層（pytest：marker 字串＋投影內容＋三端可達＋**deploy 冪等零寫入**）；行為層（headless session 自然語言 prompt 斷言 skill 載入＋**premature-action check**〔Skill 呼叫前無實質 tool_use〕；多輪變體——extended conversation 後跳過是實測失敗模式；**ZCode headless runtime 可自動化**〔delegate-bridge GLM 同機制 isolated carrier home〕，CC 端 `claude -p` 模式）
- flaky 手段：統計重複（RUNS）非 retry、CLI exit 不參與判準、prose 寬容匹配、預算上限、四態分類（PASS/FAIL/UNEXPECTED/INCONCLUSIVE）、description-recall≠behavior 分開標

## 段落 4：文檔同步＋量測結算

**要點**：
- rules/AGENTS.md「部署紀律」補三軸語義一句（`bundle-projection` marker＋fail-closed＋全域 preflight）
- structure.md 9 對表 instruction-writing 列「AIR-85 projected ✓」；llm-output 列「second pilot ready（同介面 opt-in）」
- bundle bytes 記 AIR-85 卡 notes；interface debt 清單（purity/broken-ref 掃 full source）記卡 notes 或 AIR-87
- check_single_source＋/consistency 全綠；364+新測試基線

**驗收對照**＝卡 AC#1-4（AC#2 語義已按契約三重定義——卡面 wording 於開工 notes 補記）。

---

## Scenario Matrix（關鍵情境）

| # | 情境 | 期望 |
|---|---|---|
| S1 | IW 带 marker，deploy 正常 | 三端 bundle：header＋pointer 行、無 body 無 frontmatter 殘留 |
| S2 | marker 在、skills/instruction-writing 被刪 | 全域 preflight exit≠0（任何端都未寫出） |
| S3 | mode=pointer 但 bootstrap-pointer 空 | 解析期 fail（schema invariant） |
| S4 | claude-specific 或 meta 檔帶 bundle-projection | deploy exit≠0（矛盾組合 hard fail） |
| S5 | 無 marker 的 15 支 rule | bundle 輸出 byte-identical（回歸） |
| S6 | CC 端 ~/.claude/rules/ | body/paths 靜態不動＋L4 probe：unknown keys 注入行為不變 |
| S7 | `--dry-run` 與真跑、同一 invalid marker | 兩者同 exit≠0（共用 preflight） |
| S8 | `bundle-projection: poitner`（typo）或孤兒 target/pointer 鍵 | 解析期 fail（未知值/孤兒鍵 invariant） |
| S9 | size gate 計算時點 | projection 後內容才送 90KiB/36KiB gate |

## 已決策（codex 討論輪收斂，09-13）

1. **Q1 定名**：`bundle-projection: pointer`（語義＝portable bundle 投影軸；棄 bundle-mode——太寬易混 scope/load timing）
2. **Q2 schema**：三 flat frontmatter keys＋四 invariant（段 1 落地）；**deploy 不解析 `paths:`**（契約一）
3. **Q3 驗證**：source existence（repo skills/）與 runtime reachability（`~/.agents/skills/` non-CC canonical root）分開驗；CC unknown keys 相容性**升級為 L4 runtime probe pilot gate**（契約三配套）——不採「官方文檻沉默」當證據
4. **Q4 矛盾組合**：hard fail（claude-specific/meta＋projection、未知值、孤兒鍵全 fail）——typo 不得靜默變 deployment semantics
5. 三 contract 寫死：deploy 不碰 paths／projection validation＝全域 preflight（在任何 target write 前）／AC#2＝CC runtime semantics 不變（非 byte-identical）
6. 工程形態：`read_rule_meta()` 新增＋`read_scope()` wrapper 保留；`project_rule_for_bundle()` 純函數（後續 pilot 同介面）；preflight dry-run/真跑共用
7. bootstrap-pointer 句採 codex 潤稿版（trigger＝「新增或修改 instruction 檔」）
8. interface debt 記錄：check_broken_refs/check_neutral_purity 掃 full source 非 projected 面（false-positive 潛在；第二支 pilot 前處理）

## 第二支 pilot：llm-output-convention opt-in（09-13 同日插隊微弧）

- 標註三鍵（trigger 精確定位「撰寫 Python 輸出（print/Logger/logging 配置）」——非所有 Python 工作，防 codex A2 過度觸發）；**interface debt 試煉 PASS**（full body 過 purity/broken-ref 零誤報——codex 段 2 審的殘餘風險預測未發生）；deploy 三端 **28,487B byte-identical**（29,161→28,487，−674B）；投影區段正確、body 零殘留；404 tests
- bundle 累計（AIR-86+85 兩弧）：32,835→**28,487B（−4,349B）**
- **activation 行為 probe（positive/nonmatch 成對）PENDING**：provider 端故障（z.ai coding-plan「Model creation failed」——bridge 交叉測試同款失敗、90s 重試無效，非 scratch 問題；當日稍早同配置五輪 probe 全過）。carrier＋canary＋prompt 已 staged（.agent-tmp/air85/，config 需重 stage——配方見上方方法注記）；provider 恢復後補跑，若 trigger 語義需調校為後續 commit

## 段 3 驗收證據（09-13 實測，全 AC 到齊）

- **AC#1**：pilot 標註後真 deploy——三端 29,161B byte-identical（−788B）；投影區段＝凍結模板註解＋作者句逐字；IW body 零殘留；guide 引導句雙通道在場
- **AC#2**：CC 端雙層——靜態（~/.claude/rules/ body/paths 不動＋三新鍵並存）＋**L4 三臂 probe PASS**（treatment 含 3 unknown keys 與 control 注入行為逐項一致：`load_reason=path_glob_match`＋body marker 進 response；nonmatch 零注入）——隔離 config 用 settings.json symlink（GLM env 型 auth 隨檔走，無 secret 複製）
- **AC#3**：真環境 fail-closed 實測——mv skill 目錄 → deploy exit 1＋`[FAIL] 2 pointer preflight failure(s) (aborted before ANY target write)`；復原 exit 0
- **AC#4**：deploy 全端綠＋量測入卡 notes
- **pointer 行為測試（ZCode headless 直連，GLM-5.3 旗艦）**：scratch carrier（bundle＋canary skill 副本，**僅 `.agents/skills` 單根**——Q3 契約實證可達）5 runs：direct 意圖 PASS（第一步=載入 skill、理由引用 bundle 語義）、exec×2 PASS（canary 首行＋body 內容真實摘要）、pressure×3 PASS（**全數真載入**——鑑別 run 逐字引用 canary 段；canary 指令被優雅拒從＝正確注入防禦，非機制失敗）。方法注記：bridge 的 `DELEGATE_BRIDGE_ZCODE_HOME` 是 monitor 標記非 spawn 接口——直連 `HOME=<scratch> node zcode.cjs --mode plan --json --cwd <空workdir> --prompt`（provider 解析照 bridge glm.rs L341-380 複製、config 0600 不列印）
