# Codex AGENTS.md 與 context 用法研究

> 資料源（皆 repo 內，read-only）：①`ref-docs/harness/codex/` 官方文檔鏡像 ②`ai-analysis/reports/2026-09-08-codex-agents-md-usage-and-insights.md` ③`ai-analysis/reports/2026-09-08-codex-philosophy-instruction-layering.md`
> 引用皆逐字（verbatim）；行號以 2026-09-08 Read 實測為準。〔推論〕標記＝研究者自己的話。

---

## A. Codex 官方對 AGENTS.md 的定義（職責／載入機制／大小限制／分層）

### A1. 職責定義

`ref-docs/harness/codex/guides/agents-md.md:3`：

> Codex reads `AGENTS.md` files before doing any work. By layering global guidance with project-specific overrides, you can start each task with consistent expectations, no matter which repository you open.

`ref-docs/harness/codex/guides/agents-md.md:1`（標題即定義）：

> # Custom instructions with AGENTS.md

`ref-docs/harness/codex/concepts/customization.md:19`：

> `AGENTS.md` gives Codex durable project guidance that travels with your repository and applies before the agent starts work. Keep it small.

`ref-docs/harness/codex/concepts/customization.md:21-26`（該放什麼）：

> Use it for the rules you want Codex to follow every time in a repo, such as:
>
> - Build and test commands
> - Review expectations
> - repo-specific conventions
> - Directory-specific instructions

`ref-docs/harness/codex/learn/best-practices.md:49`：

> Think of `AGENTS.md` as an open-format README for agents. It loads into context automatically and is the best place to encode how you and your team want Codex to work in a repository.

`ref-docs/harness/codex/learn/best-practices.md:51-58`（good AGENTS.md 覆蓋面清單）：

> A good `AGENTS.md` covers:
>
> - repo layout and important directories
> - How to run the project
> - Build, test, and lint commands
> - Engineering conventions and PR expectations
> - Constraints and do-not rules
> - What done means and how to verify work

### A2. 載入機制（路徑、時機、merge 語義）

**時機**——`guides/agents-md.md:7`：

> Codex builds an instruction chain when it starts (once per run; in the TUI this usually means once per launched session). Discovery follows this precedence order:

`guides/agents-md.md:183`（無 cache）：

> If instructions look stale, restart Codex in the target directory. Codex rebuilds the instruction chain on every run (and at the start of each TUI session), so there is no cache to clear manually.

`config-advanced.md:693`（載入點在第一輪）：

> Codex reads `AGENTS.md` (and related files) and includes a limited amount of project guidance in the first turn of a session.

**三層 precedence**——`guides/agents-md.md:9-11`：

> 1. **Global scope:** In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`), Codex reads `AGENTS.override.md` if it exists. Otherwise, Codex reads `AGENTS.md`. Codex uses only the first non-empty file at this level.
> 2. **Project scope:** Starting at the project root (typically the Git root), Codex walks down to your current working directory. If Codex cannot find a project root, it only checks the current directory. In each directory along the path, it checks for `AGENTS.override.md`, then `AGENTS.md`, then any fallback names in `project_doc_fallback_filenames`. Codex includes at most one file per directory.
> 3. **Merge order:** Codex concatenates files from the root down, joining them with blank lines. Files closer to your current directory override earlier guidance because they appear later in the combined prompt.

**fallback 名單預設**——`config-sample.md:254-256`：

> # Ordered fallbacks when AGENTS.md is missing at a directory level. Default: []
>
> project_doc_fallback_filenames = []

`guides/agents-md.md:136`（fallback 生效後的目錄內檢查序）：

> Now Codex checks each directory in this order: `AGENTS.override.md`, `AGENTS.md`, `TEAM_GUIDE.md`, `.agents.md`. Filenames not on this list are ignored for instruction discovery. The larger byte limit allows more combined guidance before truncation.

**override 語義**——`guides/agents-md.md:45`：

> Use `~/.codex/AGENTS.override.md` when you need a temporary global override without deleting the base file. Remove the override to restore the shared guidance.

`guides/agents-md.md:103`（同目錄 override 排斥同層 AGENTS.md，檔案樹註解）：

> comment: "Ignored because an override exists",

`guides/agents-md.md:81`：

> Codex stops searching once it reaches your current directory, so place overrides as close to specialized work as possible.

### A3. 大小限制

`guides/agents-md.md:13`（核心條款——combined 上限＋預設值＋官方處方）：

> Codex skips empty files and stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default). For details on these knobs, see [Project instructions discovery](https://developers.openai.com/codex/config-advanced#project-instructions-discovery). Raise the limit or split instructions across nested directories when you hit the cap.

`config-reference.md:1013-1018`（knob 型別定義）：

> key: "project_doc_max_bytes",
> type: "number",
> description:
>   "Maximum bytes read from `AGENTS.md` when building project instructions.",

`config-advanced.md:695`（knob 描述）：

> - `project_doc_max_bytes`: how much to read from each `AGENTS.md` file

〔推論／觀察〕官方文檔間對同一 knob 有兩種措辭：guide（agents-md.md:13）說 "combined size"（全部鏈上檔案合計），config-advanced.md:695 說 "each"（每檔），config-reference.md:1017 說 "Maximum bytes read from `AGENTS.md`"（未指明 each/combined）。09-08 哲學報告採 combined 解讀並以機械驗證（見 B 節引述）。鏡像中無更權威的仲裁條款。

**截斷是官方承認的常見態**——`guides/agents-md.md:190`（troubleshoot 條目）：

> - **Instructions truncated:** Raise `project_doc_max_bytes` or split large files across nested directories to keep critical guidance intact.

### A4. 分層建議

`learn/best-practices.md:62`（三級分層＋proximity wins）：

> You can create `AGENTS.md` files at different levels: a global `AGENTS.md` for personal defaults that sits in `~/.codex`, a repo-level file for shared standards, and more specific files in subdirectories for local rules. If there’s a more specific file closer to your current directory, that guidance wins.

`concepts/customization.md:30`（更新紀律：最近目錄原則）：

> **Updating `AGENTS.md`:** Start with only the instructions that matter. Codify recurring review feedback, put guidance in the closest directory where it applies, and tell the agent to update `AGENTS.md` when you correct something so future sessions inherit the fix.

`concepts/customization.md:42-43`（global vs repo 分工）：

> Codex can load guidance from multiple locations: a global file in your Codex home directory (for you as a developer) and repo-specific files that teams can check in. Files closer to the working directory take precedence.
> Use the global file to shape how Codex communicates with you (for example, review style, verbosity, and defaults), and keep repo files focused on team and codebase rules.

〔推論〕官方分層建議＝「內容性質」對應「目錄位置」：溝通偏好住 global、團隊/codebase 規則住 repo、特殊規則住 nested——位置即 context 邊界。

### A5. 鏡像未載／未找到項

- Codex 官方文檔無 `@`-transclusion／機械展開機制的記載（已搜：`rg -i "transclu|@-?include|@path|@expand"` 於 `ref-docs/harness/codex/` → 0 hits）。best-practices.md:66 的 "reference task-specific markdown files" 指引用讓 agent 自己讀檔，非載入器展開（09-08 報告亦此判讀，見 B2）。
- `ref-docs/harness/codex/rules.md` 的 "rules" 是另一機制——sandbox 外指令控制的 `.rules` 檔（rules.md:3 "Use rules to control which commands Codex can run outside the sandbox."），與 AGENTS.md 指令鏈無關，勿混淆。
- 官方未記載 `project_doc_max_bytes` 的上限值（09-08 報告：「文件無上載明白款，type `number`」）。

---

## B. 兩份 09-08 報告的核心建議

### B1. `ai-analysis/reports/2026-09-08-codex-agents-md-usage-and-insights.md`

**自我定位**（報告 frontmatter，:3-5）：

> Part A＝文檔忠實整理（來源：`ref-docs/harness/codex/` 內 `guides/agents-md.md`、`concepts/customization.md`、`learn/best-practices.md`、`skills.md`、`memories.md`；句句有檔可查，不摻推論）。
> Part B＝arch-thinking 視角洞見（三主線：依賴規則／bounded context／use case 驅動；其中可機械驗證者已驗，推論標 `open`）。

**建議/洞見清單（逐條）**：

1. **五層互補**（:13 引官方 "These are complementary, not competing."；對照表 :15-21 將 AGENTS.md/memories/skills/MCP/subagents 映射到我方 rules/memory/skills/code-reality/Writer-Reviewer）。官方 build 順序（:23）：AGENTS.md（＋pre-commit hooks/linters 強制）→ plugin → skill → MCP → subagents。
2. **Keep it small＋feedback loop**（:27-30）：只放「每次在 repo 都要守」；「犯兩次才 codify：mistake repeated→加 rule；讀太多文件→加 routing guidance；同樣 PR feedback 出現兩次→寫死。不是預先寫全。」；放最近的目錄；配強制基礎設施（pre-commit hooks、linters、type checkers）。
3. **Global vs repo 分工＋層級倒置診斷**（:34-36）：global 是「你這個人」的預設；「我方現況對照：bundle 把「跨 harness 通用紀律」全塞進相當於 global 的位置（79KB），repo 層（ai-rules 12.5KB）在 muse 上 0 bytes——**層級倒置**：global 臃腫、repo 餓死。」
4. **太大時官方處方三選一**（:38-44）：① Raise the limit（`project_doc_max_bytes`）② Split across nested directories ③ Reference task-specific markdown files（"agent 循引用讀，非機械展開"）。另有管理機制：`AGENTS.override.md`、`project_doc_fallback_filenames`、`CODEX_HOME` 分身。
5. **Skills 是 authoring format，plugin 是發布單位**（:46-51）：progressive disclosure——「初始只進 metadata（全表 ≤2% context 或 8K chars……）；選中才讀全文；references/scripts 用時才動」；「"Clear skill descriptions improve triggering reliability."——description 是觸發器，寫爛等於沒有。」
6. **Memory 獨立 lane**（:53-55）：三家 memory 機制各異，「**三家 memory 都是獨立 lane，不進 rules_file 預算**——瘦 bundle 時 memory 規範的「寫入端」是第一個可疑對象」。
7. **官方驗收手段**（:57-62）：覆述探針 `codex --ask-for-approval never "Summarize the current instructions."`；TUI log/session jsonl 稽核；「Chain 每 run／每 TUI session 重建，**無 cache 可清**」。
8. **洞見 B1 分層塌縮**（:70）：「**我方 bundle 把 skills 層的 reference 內容 inline 回 AGENTS 層**——等於 adapter 住進 domain，依賴方向反了。截斷不是容量事故，是結構事故：分層塌縮後，單一 64KiB lane 被迫承載三層內容。處方不是「壓字數」，是「恢復分層」」。
9. **洞見 B2 邊界正交**（:74）：「Codex 用**目錄位置**做 context 邊界（global／repo／nested，deeper wins）；我方用 **`harness-scope` frontmatter** 做邊界……兩種邊界正交、可並存成矩陣」。
10. **洞見 B3 cut set 判準**（:78）：「判準：**一條 rule 是否跨工單**——跨工單的留 bundle……工單可自帶的走……**判準本身只有 5 行，可寫進部署紀律**，後續 rule 增刪不再憑感覺。」
11. **洞見 B4 共用層外溢否決**（:82）：「**改消費端各取所需（per-target variant），不改共用層**——A 案的架構級論證，與 token 數學無關，即使 B 案字數上可行仍否決。」
12. **洞見 B5 執行序**（:86）：「scope 切（現成）→ knob（現成，codex 已做）→ 下沉（先例）→ per-target slimming（新發明，不到萬不得已不做）。」
13. **方法論限制**（:88-93）：文檔以鏡像為準未對線上；「Codex 側**零實測**（knob 調整僅 TOML 解析通過，chain／cap 行為全引文檔）」。

### B2. `ai-analysis/reports/2026-09-08-codex-philosophy-instruction-layering.md`

**一句話結論**（:8）：

> Codex 官方哲學＝**小主檔＋引用＋skills＋memory＋MCP 五層互補**（`customization.md` 原話 "complementary, not competing"），配可調 knob。Muse 無文檔、無 knob，只能硬瘦；Codex 可調 knob，已於 09-08 調至 100KiB 根治。剩餘工作＝muse 變體（A 案先行）＋三條 rule 下沉＋per-target gate。

**問題起點與機械證據**（:4, :12-15）：

> 問題起點：muse user-rules 64KiB 靜默截斷（backlog draft-3 載體；lane 語義已於 09-08 以機械證據定案為串接）。

> muse session（ai-rules workspace）：`rendered_bytes=92,962`（user 79,315＋project 鏈 13,647）→ `text_bytes=65,535`，載入率 70.5%。切口：quality-constraints @63,956 只活 1,579B；tool-discipline @71,597 整檔陣亡；project AGENTS.md（12,550B）0 bytes。

**四家機制對照**（:19-25 表）——Codex 行（:23）：

> | Codex | 32KiB 預設 | 有記載（`project_doc_max_bytes`），combined，**可調** | 原 32K 切比 muse 更狠 ❌❌ | ✅ 調 knob（已調 102400，見下） |

**哲學映射（五層 → 我方現況 → 缺口）**（:32-38）逐條：

1. 「**小主檔（Keep it small）**：……我方 bundle 79KB 是其 2.5 倍（以 Codex 預設計）——超標確認。」（:34）
2. 「**引用（reference task-specific md）**：Codex best-practice 明示；muse 不支援 `@` 展開……結論：**下沉只能走 skills，不走引用**。」（:35）
3. skills：「三家機制皆支援……我方已有 8 組分層，路徑成熟。」（:36）
4. memory：「三家獨立 lane，不占 rules 預算」；muse 對 ai-rules 唯讀，「寫入端規範對 muse 是死重」。（:37）
5. MCP：「本議題無關……不占 instruction 預算」。（:38）

**處方（已執行＋待執行）**（:40-51）：

- 已執行（:44）：Codex knob `project_doc_max_bytes = 102400`；「79,315＋12,550＝91.9KB＜100K，Codex 側根治，bundle 不動。未驗證：CLI 版本是否認得該鍵」。
- A 案先行（:48）：muse 專用變體，排除 lsp-navigation＋model-routing＋instruction-writing＝11,536B → 變體約 67.8KB。
- 下沉 follow-up（:50）：「acceptance-evidence（57 行 7KB）、collaboration-constraints（81 行 6.8KB）、outward-action-consent（100 行 5.6KB）三條各下沉一半（rule 留核心＋pointer，深層進 SKILL.md）」。
- per-target gate（:51）：`BUNDLE_MAX_BYTES` 拆四檔（muse 64K 硬／codex 100K 軟／zcode 100K 硬／opencode 未驗先沿用 90K 並標 unverified）。

**驗收探針**（:53-58）：muse `rules_file text_bytes == 檔案大小`；codex 新 session 覆述 `<!-- bundle-end -->`；（選）concat 順序釘死；（選）`@` 展開探針。

**未驗證項**（:60-65）：OpenCode 上限；Codex CLI 版本是否接受 knob（「TOML 過≠runtime 認」）；muse 65,536 上限在 mosaic 級 project 鏈下行為；rendered/text 約 1KB 殘差。

---

## C. Codex 文檔/報告中的 context 管理 pattern

### C1. 目錄分層（位置即 context 邊界）

`guides/agents-md.md:3`（見 A1）＋ `guides/agents-md.md:9-11`（三層 precedence，見 A2）＋ `learn/best-practices.md:62`（三級檔案，見 A4）。

`concepts/customization.md:42`：

> Files closer to the working directory take precedence.

〔推論〕pattern：不做單檔，用「global → repo root → nested」鏈式串接，越近 working directory 越贏；內容按性質分流（溝通偏好/global、codebase 規則/repo、特殊規則/nested）。

### C2. 按需載入（skills progressive disclosure）

`ref-docs/harness/codex/skills.md:9`：

> Skills use **progressive disclosure** to manage context efficiently: Codex starts with each skill's name, description, and file path. Codex loads the full `SKILL.md` instructions only when it decides to use a skill.

`ref-docs/harness/codex/skills.md:11`（初始清單預算）：

> Codex includes an initial list of available skills in context so it can choose the right skill for a task. To avoid crowding out the rest of the prompt, this list uses at most 2% of the model’s context window, or 8,000 characters when the context window is unknown. If many skills are installed, Codex shortens skill descriptions first. For large skill sets, Codex may omit some skills from the initial list and show a warning.

`concepts/customization.md:126-130`：

> Codex uses progressive disclosure for skills:
>
> - It starts with metadata (`name`, `description`) for discovery
> - It loads `SKILL.md` only when a skill is chosen
> - It reads references or runs scripts only when needed

`concepts/customization.md:71`：

> Skills are loaded and visible to the agent (at least their metadata), so Codex can discover and choose them implicitly. This keeps rich workflows available without bloating context up front.

〔推論〕pattern：rich 內容常駐的只有 metadata（有硬預算：2% context 或 8K chars），全文靠「被選中」才載——即 ai-rules「rule 留 always-on 核心＋pointer，深層住 SKILL.md」分層的官方同構物（09-08 兩報告皆明示此對應）。

### C3. 引用外部 task-specific 檔（agent 循引用讀）

`learn/best-practices.md:66`：

> If `AGENTS.md` starts getting too large, keep the main file concise and reference task-specific markdown files for things like planning, code review, or architecture.

`learn/best-practices.md:118`（review 情境實例）：

> If you and your team have a `code_review.md` file and reference it from `AGENTS.md`, Codex can follow that guidance during review as well. This is a strong pattern for teams that want review behavior to stay consistent across repositories and contributors.

〔推論〕這是「主檔瘦＋衛星檔按需讀」的多檔策略；但載入是 agent 行為（讀引用檔），非載入器機械展開——與 Claude `@` transclusion 不同（鏡像無展開機制記載，見 A5）。

### C4. Size 控制 knob＋拆檔逃生艙

`guides/agents-md.md:13`（見 A3）：預設 32KiB combined、`project_doc_max_bytes` 可調、「Raise the limit or split instructions across nested directories when you hit the cap.」

`guides/agents-md.md:190`（見 A3）：troubleshoot 把截斷列為常見態，處方同上二選一。

〔推論〕官方 size 政策＝先拆檔/分層（結構手段），調上限是 knob 逃生艙而非鼓勵單檔變大。

### C5. Feedback loop 動態 codify（不預先寫全）

`concepts/customization.md:28`：

> When the agent makes incorrect assumptions about your codebase, correct them in `AGENTS.md` and ask the agent to update `AGENTS.md` so the fix persists. Treat it as a feedback loop.

`concepts/customization.md:34-36`（何時更新）：

> - **Repeated mistakes**: If the agent makes the same mistake repeatedly, add a rule.
> - **Too much reading**: If it finds the right files but reads too many documents, add routing guidance (which directories/files to prioritize).
> - **Recurring PR feedback**: If you leave the same feedback more than once, codify it.

`learn/best-practices.md:64`：

> Keep it practical. A short, accurate `AGENTS.md` is more useful than a long file full of vague rules. Start with the basics, then add new rules only after you notice repeated mistakes.

〔推論〕「routing guidance（該先讀哪些目錄/檔案）」本身就是 context 管理 pattern 的一種：把導航寫進 AGENTS.md，讓 agent 少讀文件。

### C6. Memory 獨立 lane（與 instruction 預算分離）

`ref-docs/harness/codex/memories.md:8-11`：

> Memories let Codex carry useful context from earlier threads into future work. After you enable memories, Codex can remember stable preferences, recurring workflows, tech stacks, project conventions, and known pitfalls so you don't need to repeat the same context in every thread.

`memories.md:13-15`（邊界條款；原句跨三行）:

> Keep required team guidance in `AGENTS.md` or checked-in documentation. Treat memories as a helpful local recall layer, not as the only source for rules that must always apply.

〔推論〕Codex 把「必守規則」（AGENTS.md，進 instruction 預算）與「回憶層」（memories，獨立機制）分開——09-08 兩報告據此把 memory 規範從 rules bundle 預算中排除。

### C7. Subagents 分流（雜訊任務出主 context）

`concepts/customization.md:165`：

> You can create different agents with different roles and prompt them to use tools differently. For example, one agent might run specific testing commands and configurations, while another has MCP servers that fetch production logs for debugging. Each subagent stays focused and uses the right tools for its job.

`concepts/customization.md:181`：

> 4. [Subagents](https://developers.openai.com/codex/subagents) when you're ready to delegate noisy or specialized tasks to subagents.

### C8. Thread/工作單元粒度

`learn/best-practices.md:223`：

> - Using one thread per project instead of one thread per task. This leads to bloated context and worse results over time

〔推論〕context 管理不只檔案層——官方連「一 thread 一 task」的工作單元粒度都列為 anti-pattern，對應我方「一 EP 一 session」。

### C9. 首輪即全量（chain 是一次性注入）

`config-advanced.md:693`（見 A2）："includes a limited amount of project guidance in the first turn of a session"。

〔推論〕與 skills 的按需載入相反：AGENTS.md chain 是 start 時一次性 concat 進第一輪 prompt——所以 chain 總量有硬上限、也是截斷風險所在。兩者構成 Codex context 模型的兩種載入語義：常駐指引（預算內一次性）vs 按需知識（metadata 點名、全文延遲）。

---

## D. 對照線索：反面模式 vs 分層/按需支持

### D1. 「單一巨型 AGENTS.md」的反面證據

| 證據 | 錨點 |
|---|---|
| "Keep it small."（AGENTS.md 職責段結語） | `concepts/customization.md:19` |
| "Keep it practical. A short, accurate `AGENTS.md` is more useful than a long file full of vague rules." | `learn/best-practices.md:64` |
| "If `AGENTS.md` starts getting too large, keep the main file concise and reference task-specific markdown files…" | `learn/best-practices.md:66` |
| "**Instructions truncated:** Raise `project_doc_max_bytes` or split large files across nested directories…"（截斷被官方列為常見故障態） | `guides/agents-md.md:190` |
| "Raise the limit or split instructions across nested directories when you hit the cap." | `guides/agents-md.md:13` |
| "Overloading the prompt with durable rules instead of moving them into `AGENTS.md` or a skill"（common mistakes 首條——注意：連「塞 prompt」都反對，durable rules 應進 AGENTS.md 或 skill，不是堆在 prompt） | `learn/best-practices.md:216` |
| "This keeps rich workflows available without bloating context up front."（skills 段，反「up front 全量」） | `concepts/customization.md:71` |

### D2. 支持分層/按需的正面證據

| 證據 | 錨點 |
|---|---|
| "By layering global guidance with project-specific overrides…"（開篇即分層框架） | `guides/agents-md.md:3` |
| 三層 precedence＋per-directory 一檔＋root-down concat | `guides/agents-md.md:9-11` |
| "put guidance in the closest directory where it applies"（就近原則） | `concepts/customization.md:30` |
| "…a global `AGENTS.md`…a repo-level file…and more specific files in subdirectories for local rules. If there's a more specific file closer to your current directory, that guidance wins." | `learn/best-practices.md:62` |
| "reference task-specific markdown files for things like planning, code review, or architecture"（多檔策略）＋`code_review.md` 實例 | `learn/best-practices.md:66`、`:118` |
| Skills progressive disclosure（metadata 常駐、全文按需、references 用時才讀；2%/8K chars 預算） | `skills.md:9,11`；`customization.md:126-130` |
| 五層互補框架（AGENTS/memories/skills/MCP/subagents 各司其職） | `concepts/customization.md:5-15` |
| Memory 與必守規則分流（"Keep required team guidance in `AGENTS.md`…"） | `memories.md:13-14` |
| "delegate noisy or specialized tasks to subagents"（雜訊出主 context） | `customization.md:181`；`:165` |

### D3. 報告面的對照判讀

- 巨型單檔反模式在我方 repo 的具象化：09-08 哲學報告 :34「我方 bundle 79KB 是其 2.5 倍（以 Codex 預設計）——超標確認。」；用法報告 :36「**層級倒置**：global 臃腫、repo 餓死。」
- 對截斷的定性（用法報告 :70）：「截斷不是容量事故，是結構事故……處方不是「壓字數」，是「恢復分層」」——〔推論〕與官方 D1 條目一致：官方處方（split/reference/skills）全是結構手段，調 knob 只是逃生艙。
- 官方哲學總結（哲學報告 :8）：「小主檔＋引用＋skills＋memory＋MCP 五層互補，配可調 knob」——五個成分裡四個是「不進主檔」的承載層。

### D4. 未找到項（誠實段）

- Codex 官方文檔未記載 `@`-transclusion／機械 include（已搜 `rg -i "transclu|@-?include|@path|@expand"` → 0 hits，`ref-docs/harness/codex/`）。
- 官方無「推薦行數/字數」數字型 size 建議（僅 32KiB 預設＋knob＋"keep it small" 質性原則）。
- 官方未記載 `project_doc_max_bytes` 上限；未記載 chain 內 per-file 與 combined 的權威仲裁（見 A3 措辭張力）。
- `rules.md` 的 rules 機制（sandbox 指令控制）與 AGENTS.md 無交集，鏡像中無「AGENTS.md 替代/補充 rules」條款。
