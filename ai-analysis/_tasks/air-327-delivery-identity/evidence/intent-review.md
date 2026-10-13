All verification legs are complete. Composing the final review report.

---

# AIR-327 独立审查（意图 / 架构）— GLM-5.3, session-label `air327-glm-intent`

## 1. 已审查的差异标识与范围

- **WT/分支/基线**：`/Users/ctai/Github/ai-guide-air-327`，分支 `air-327`，HEAD `7dbfd020fec402ca3c0eabb2c55a5752ae6e2057` —— 等于 EP 声明的基线（通过 `git rev-parse` 验证）。
- **差异**：仅未暂存（staged差异为空），14 个文件 +517/−104：`scripts/arc_manifest.py`, `scripts/arc_handback_join.py`, `tests/test_arc_manifest.py`, `tests/test_arc_handback_join.py`, `tests/fixtures/air-234/{handback-missing,handback-pass}.json`, `tests/fixtures/air-234/manifests/impl-a.json`, `ai-analysis/blueprint/{index.html,projection-manifest.toml,structure.md}`, `governance/AGENTS.md`, `scripts/AGENTS.md`, `skills/_common/work-order.md`, `skills/agent-workflow/SKILL.md`。未追踪：`ai-analysis/_tasks/air-327-delivery-identity/{ep.md,index.html}`。
- **差异 sha256：降级** —— plan-mode 沙箱阻止了管道/python 哈希操作。标识改由基线 + 统计信息 + 每个文件的 blob 证据（例如 `structure.md` 的新 blob `283df77b`，来自 git 自身的 diff 索引行）来固定。未尝试绕过。
- **排除项（根据工单 §3）**：`.agent-tmp/`，EP/报告 shell 的创作（仅查阅 shell 头部：声明的 EP 路径 + 相同的基线 —— 一致；注意 EP 进度部分仍然显示“未開始實作”，已被 Marshal 的账本淘汰 —— 超出我的范围）。已关闭的 backlog 卡片视为历史记录，未进行回写编辑。

## 2. 镜头覆盖范围（工单 §2/§5 —— 所有分支均已行使，非空）

**意图 / EP 冻结契约（S1 预言机 1–11）** —— 每个预言机都定位在代码 + 测试中并进行了追踪阅读：
tamper-with-recomputed-digest → `join()` 根据*预期 (expected)* 验证重新计算的结果 (`scripts/arc_handback_join.py:77-104`)，测试 `test_changed_dispatch_rejects_old_handback` (recompute=True, tests/test_arc_handback_join.py:388-406)；仅预期的失配 → 预言机 11 测试 (:372-378) + `--expected-digest` 为必填项 (argparse, :216-220; 子进程缺失参数测试 :522-525)；相同契约不同分配 → 摘要涵盖 `unit_id`+`predicates`，`contract_hash` 不变，`test_reassign_ac_subset_changes_digest_only_not_contract_hash`；相同内容重试 → `_write_manifests` 跳过规范相等文件，字节保留 (`scripts/arc_manifest.py:335-354`)，测试 `test_same_content_retry_preserves_original_bytes`；no-clobber/迁移 → 整批预检查在任何写入之前引发异常 + `open("x")` 独占创建 (:337-354)，测试包括预检查、竞争（monkeypatched）、变更契约，加上 `/1` 模式被两个所有者明确拒绝（`join()` 模式门控独立于摘要有效性 —— 测试 :419-429 使用完全自洽的 `/1` 对证明了拒绝）；通过真实子进程的生产者→连接（预言机 6, :474-525）；两个工具中的非有限值 → `allow_nan=False` + 生产者 `main` 捕获 `UnicodeError` (`arc_manifest.py:384`)，连接有限门控 (:76-80)，两个所有者的测试。**架构**：摘要定义是生产者拥有的单一助手，由消费者导入（无规范化重复，`arc_handback_join.py:37-44`）；身份层位于现有结构检查之前，不替换它们（测试 `test_identity_does_not_replace_structure` 断言结构诊断在没有身份噪声的情况下仍会触发）；身份通过 ≠ 语义接受，在 `join`（FAIL/NOT-DONE → 0），work-order「結構通過≠完成」和 agent-workflow「exit 0 不等於完成」中保持 —— 卡片 AC#1/#2 意图满足。

**S2（无强制提交以证明活跃度）**：`skills/agent-workflow/SKILL.md:99` 重写 —— 仅内容层面证据，无新的写入/提交权限，建议保持沉默，终端/强死权威未变，旧工单明确修正条款存在。对 `skills/ agents/ rules/ scripts/ governance/ backlog/tasks` 进行 `rg "allow-empty|證活|空 commit"` 残留扫描：主动 surfaced 清洁；剩余匹配项为已关闭的卡片（air-293 历史记录）、不相关的 `--allow-empty-roots` 标志和 rebase-skill git 语义 —— 已正确保持不动。与同一文件中的 worktree 隔离 preflight（“需要 uncommitted → 先 commit”，:316）无矛盾 —— 该机制用于基线可见性，而非活跃度证明。

**S3（源码支撑的 blueprint 刷新）**：`index.html` 在同一变更集中针对每次 `structure.md` 更新进行了内容刷新（受众说明，L0-L2 行，跨仓库段落，部署边界项目，已知限制表 —— 均在 diff 中验证为镜像）。哈希：`projection_freshness.py` 语义 = git blob hash (:51-57)，具有节锚定哈希的 `AGENTS.md#命令的受眾視角` 条目。`structure.md` 条目 `283df77b…` **通过** git 的新 blob id **机械验证**。`AGENTS.md` 条目 `a17c87eb→e49c2c00`：root `AGENTS.md` 在此 diff 中未触及，因此旧值在 air-223 (`307e2e73`，清单的最后一次提交) 时就已过时；`AGENTS.md` 随后在 `d3455444/12307c25/02c4cc27` (air-229/bridge/air-290 受众部分编辑) 中发生了变更 —— 追上 (catch-up) 叙述与 git 时间线一致，且内容已刷新，因此不是哈希清洗。精确的 `e49c2c00` 值：仅执行验证 → 剩余。Blueprint/governance 导航声明与实际情况交叉检查：`governance/manifest.toml` 具有 `[surfaces.rules]` 及四个 `AGENTS.md` 目标，`[registrations.grok/zcode/codex]`，`~/.agents/skills` 母链，`~/.zcode/agents→agents/zcode`，`~/.grok/agents→agents/claude`；`registrations/` 目录列出所有五个模板，其中 cc.json 已休眠 —— 每个新的文档声明均匹配。

**消费者契约 / 指令一致性**：对跨主动 surfaced 的 `arc_handback_join|arc_manifest` 和 `arc-manifest/1|arc-handback/1` 进行 `rg` —— 仅主动指令消费者是 `work-order.md` 和 `agent-workflow`（均已更新为新的 CLI/模式）加上新的 `scripts/AGENTS.md` 集群要点；过时的签名仅存在于已关闭的 backlog 卡片 air-234/246（历史记录 —— 重写它们将伪造记录）。无缺少消费者更新（工单 §5 “缺少消费者更新至关重要” —— 未发现）。

**范围外（已遵守）**：无新的资格策略、监视者或 cron 引入任何 hunk；diff 仅包含列出的 14 个文件加上未追踪的 task-home shell。

## 3. 发现

**F1 — 重要 / 基于证据 / 缺陷 / unverified-by-graph（代码阅读 + 标准库语义；因沙箱无法执行）**
`scripts/arc_handback_join.py:77` — 恶意清单字符串可能导致未捕获的 `UnicodeEncodeError` → 回溯 + 退出 1，违反了记录的退出契约（退出 2 + stderr ERROR; docstring 第 24-26 行）。
- 机制：带有孤立代理转义符（例如 `"x":"\ud800"`）的清单 JSON 通过 `json.loads` 解析；`canonical_json` 的 `json.dumps(ensure_ascii=False)` 将代理输出到 str 而不报错；`assigned_manifest_digest` (`arc_manifest.py:85`) 中的 `.encode("utf-8")` 随后引发 `UnicodeEncodeError`，但这**不是** `ManifestError`，所以它逃出了 `join()` 的 `except ManifestError` (`arc_handback_join.py:79`) 并从 `main()` (:230, 在 try 外部调用) 中掉出。
- 同一变更集的不对称性：生产者 `main` **确实**为完全此类失败添加了 `UnicodeError` (`arc_manifest.py:384`)；消费者的重新计算路径遗漏了它。影响有限 —— 仍然是响亮且非零的，所以 DONE 保持阻塞（fail-closed 存活）；缺陷在于契约偏差 + 回溯而不是诊断，且仅可通过恶意输入达到（先崩溃；摘要不匹配行永远不会发出）。
- 复现（Flash/Marshal）：复制 `tests/fixtures/air-234/manifests/impl-a.json`，添加顶层 `"surrogate":"\ud800"`，运行 `uv run python scripts/arc_handback_join.py --manifest <copy> --handback tests/fixtures/air-234/handback-pass.json --expected-digest 961b585ef468a5a3861a04800d4a9ee7da1d63c6151d3cd3f8b7e3699d66b5f1` → 预期观察：回溯，退出 1；契约要求：退出 2 + `[arc-join] ERROR`。修复方向（Sol 所有权）：将 `UnicodeError` 加入到 `join()` 的身份 try 中（或在 `main` 中包装 `join` 调用）。
- 预存上下文（非新，不计入）：具有无效 UTF-8 字节的清单/回执文件在 `_load_json` 读取时已经以相同方式崩溃（`arc_handback_join.py:195`，此 diff 未触及）。

无其他发现：上述 S1/S2/S3 分支保持正常；在主动 surfaced 上未发现漂移、缺少消费者或不一致。

## 4. 实际运行的测试

**无** —— plan-mode 沙箱拒绝了 `uv run pytest`（拒绝记录在案；未尝试绕过）。独立验证改为通过完整阅读两个脚本、两个测试文件、`conftest`、fixtures，git blob-hash 证据以及 `rg` 消费者/残留扫描。变异预言机重跑（EP 验证要求）：不可执行；改为推理级别追踪 —— 删除预期比较会使 `test_expected_only_oracle11` 的 rc 2→0（断言失败）；删除重新计算会翻转 `recompute=True` 参数化；删除回执检查会翻转 `test_handback_digest_invalid`。负测试是突变敏感的，且预言机来源按测试注释被冻结为 "S — accepted AIR-327 EP S1 oracle1–11"。

## 5. CR 每分支回执

`route：live-cr:MCP` 尝试进行结构分支 —— `get_minimal_context` 正常（5679 节点/10113 边），但未通过 MCP 查询 surfaced 新鲜度特性，且该图必然构建在此未提交的 WT diff 之前；重建被禁止（父级为最终状态重建；从不同时进行）。**降级原因：WT-graph-stale + 无新鲜度特性可用。** 本报告中的所有消费者/结构声明均为文本回退（`rg` + 完整阅读 + `git` 证据），根据工单 §7 标记为 `unverified-by-graph`；未做出图支持的负面存在声明（零消费者/可删除）。

## 6. 其余未验证项（上级的收尾工作）

1. 测试套件通过：`uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py` —— 也传递地确认了 fixtures 存储的摘要 `961b585e…`（通过 `test_output_byte_equal_to_frozen_fixture` + 基于 `_run` 的测试强制执行）。
2. 投影新鲜度门控：`uv run python scripts/projection_freshness.py --manifest ai-analysis/blueprint/projection-manifest.toml` → 预期退出 0（确认 `e49c2c00` 节哈希以及已验证的条目）。
3. F1 运行时确认（上方复现）。
4. 差异 sha256（沙箱阻止哈希；标识由基线+统计+blob 固定）。

**结论（仅发现结果）**：一个重要发现（F1，连接退出契约 / 对抗性输入鲁棒性不对称）。每个 §5 冻结契约分支的意图和架构均保持；Writer 的 PASS 未用作证据；我未进行任何源码编辑，且此审查未发生 git 状态变更。处置权归 Marshal 所有。
