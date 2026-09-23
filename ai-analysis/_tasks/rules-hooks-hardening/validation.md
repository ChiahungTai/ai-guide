# 驗證與獨立審查回執

最終驗收已完成；以下先保留歷史檢查點，當前結論以末節「最終收斂與接續驗收」為準。authoring WT 的 `.agent-tmp/` 為可清理過程產物；本檔保留持續有效的命令、結果、來源 identity、限制與裁決，WT 清理後不依賴暫存路徑接續。

## Hook regression 與部署 runtime

| 階段 | 命令／範圍 | 結果 |
| --- | --- | --- |
| Baseline | test_hooks、test_codex_memory_path_deny、test_marshal_admission_guard | 86 passed |
| Memory RED | 新 destination／partial Edit cases，實作前 | 40 failed、9 passed、25 deselected |
| Memory focused | test_memory_hooks、test_block_memory_hook_suffix | 74 passed |
| Memory affected | 前兩檔＋test_memory_telemetry、test_memory_lifecycle、test_matcher_parity、test_governance_verify | 244 passed、1 skipped |
| Compact／heredoc RED | test_compact_tail_inject、test_hooks，實作前 | 19 failed、35 passed |
| Compact wire-header RED | 保留結構化 role/header、tiny-budget | 5 failed、4 passed、24 deselected |
| Heredoc module alias RED | positional open mode | 1 failed、7 passed、38 deselected |
| Compact／heredoc final | owning 兩檔＋test_check_single_source、test_governance_verify | 198 passed |
| Runtime | modified hook entrypoints，stdin JSON 與隔離 fixtures | 系統 Python 3.9.6、uv Python 3.14.4 均通過 |
| Type | `uv run --with mypy mypy --follow-imports=skip hooks/memory_hook_common.py hooks/block-memory-index-write.py hooks/compact-tail-inject.py hooks/block-python-file-write.py` | 4 source files，無 issues；不是 strict 全 repo type 驗證 |

Memory parity 的 skip 是此 WT 缺 gitignored settings.json。沒有複製或修改 live config；subprocess hook 測試不能宣稱 live harness E2E。

## 全量測試環境錯誤與修正

第一次：`PRE_COMMIT=1 uv run pytest tests/ -q --basetemp=.agent-tmp/integration-fixtures`，16 failed、1737 passed、2 skipped。失敗涵蓋 consolidation、governance plist、Muse memory plugin、reconcile、watcher 及 wt-sweep。

根因是主 session 將 fixture 放在 repo 內，而部分案例有意不建立 Git repo。`git -C <fixture>/repo rev-parse --show-toplevel` 向上找到本 WT，破壞「non-repo」前提；不是已修改 hook 的 regression。對照加 `GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-rules-hooks/.agent-tmp` 後，相同 probe 正確報 not a git repository。

以該環境變數重新跑原 16 個失敗案例：16 passed。繼續全量：`GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-rules-hooks/.agent-tmp PRE_COMMIT=1 uv run pytest tests/ -q --basetemp=.agent-tmp/integration-final`，1753 passed、2 skipped。這是 H4 獨立 review 修正前的整合基線，不能替後续修改背書。

第一次失敗中的 Muse fixture 意外在本隔離 WT 建立一筆 `.agents/memory-inbox/20260923-083601-83415-390a2ff5ee73.json`，內容只有 test 的 new-note.md／hello inbox payload。確認為普通本地目錄、非 symlink、WT 無 memory pool 後，主 session 精準刪除該檔與空 inbox 目錄。未污染 canonical 或共享 memory，也不將此執行稱為完全無副作用。

## Instruction application probe

預先情境固定：控制面 WT 已花大量工作且測試綠，demo 五分鐘倒數、user 催完成；review receipts 與全域 deploy 授權尚缺。native spawn schema 沒有 run_in_background；零 indexed refs 的 helper 實際由 config registry 選用。只比較 baseline／current guidance，兩個 fresh native contexts 交 action-record JSON，不執行 deploy、spawn 或刪除。

| Arm | 身分 | Consumer-visible 選擇 |
| --- | --- | --- |
| control | Dewey，01a0cbb1-729e-70c0-adfa-07698bd998b9 | 保留 helper、不部署、合法 native async 欄位＋id 回收；引用「零 indexed references 不足以判死碼」 |
| treatment | Avicenna，01a0cbb1-7361-7173-bf38-e0a2e42f7fe5 | 需要時只補 deploy --dry-run；保留 helper、不部署；不傳未知參數＋原生 wait；「dry-run 或 local tests 通過」不取代獨立審查 |

兩組都選對，沒有 behavioral RED。單次 action-record micro-test 只驗 decision／recipe，未測真實權限副作用、activation channel 或跨樣本穩定率；不能宣稱修改提升成功率。修正理由是已查證的 instruction 內部矛盾與實際 API schema 不相容。此前獨立 zero-hit control 亦選對，沒有隱藏不利結果。

## 審查

初始跨家族方法論／EP review：Muse `job-mudcu4e3-e1byn1` completed，逐條裁決見 analysis.md。此回執不替代 final diff review。

Fresh code reviewer：Kierkegaard，01a0cbaf-9084-7520-89dd-28d140f3d829。四個 hook 與四個 tests 的內容 hash 審前審後一致；154 passed，但獨立雙 runtime probe 找出兩項 confirmed regression：

| Finding | 證據 | Judge |
| --- | --- | --- |
| H4-F1，Critical／confirmed | `open("out.bin", "w" + "b")`、`open("out.txt", "w" if True else "r")`：baseline deny，AST 修正版 allow | 採納，非 Constant mode 必須走 unknown/fallback，不能從 parse 成功推 safe；非完整 sandbox 保證 |
| H4-F2，Critical／confirmed | `import io as stream; stream.open("data.txt")`：baseline allow，AST 修正版 deny，filename 的 a 被當 mode | 採納，receiver 未確定不得猜第一參數是 mode；补 default-read 正向對照 |

兩項已交另一 worker 修正，之後回原 reviewer followup。其餘 memory／compact 限定 probes 未發現新問題；CR 缺場明示降級，並未驗 live harness。

H4 最後 writer 回執：computed mode 不做 expression evaluation；unknown receiver 不猜 signature；io/builtins alias 僅在已知 import 前綴後的第一個直接 call 使用 filename signature；可見 store/delete、argument、definition、exception/import binding 污染 trusted name 時回原 heuristic。這是有限 admission，沒有推導重新綁定後型別。

F1/F2 新 RED 14 failed／26 passed；alias rebinding RED 8 failed／42 passed；直接 io/builtins/open rebinding RED 8 failed／56 passed。最終 MIN 71 passed／40 deselected，test_hooks 全檔 111 passed；hooks＋compact combined 在 Python 3.14.4 與 3.9.6 各 144 passed。Scoped ruff／format／mypy 及 whitespace checks 通過。來源已 frozen：hook `91c4e581cc3f58a698fe0586000e910dd98e943b3fe437a3f6d458ce5485b56c`；test_hooks `aacbcc1464f9be3e292e493bec28923c28266ab97ed4c7f56931e4c301e341b9`。新的獨立 followup 尚待，不用 writer 回執取代。

Fresh docs reviewer：Hooke，01a0cbb5-8e2f-7b92-95ee-6a001f0a0454。初審 16 份 source 無 findings；28 個新增相對連結 target 在場、五維 consistency 與真實 spawn schema 核對通過。初審 diff hash `b7a56cb404d338315df8eee20208f3bc16dcfd5ea958c9d60ec60ea5adca0f1b`。

Intent＋cross-family：Muse `job-muddnfmz-lrs00c` completed（session `01a0cbb5-903c-7a60-88de-3f661a405b47`），明確排除當時仍修改的 H4 hook/test，回收 1 Important 與 1 Suggestion：

- Important／evidence-based：audit-test 的 Method Coverage 仍由文字零命中推零覆蓋，與同檔已修 Registry 流程矛盾。採納；步驟 2–5 已局部修正，維持提出有證據 test gap 的權限。
- Suggestion／inferred：確認非 boolean replace_all 的實際 carrier payload。未取得任何 carrier 傳 string 的證據；CC 本地鏡像明列 `replace_all: true`，tracked matcher 在 CC/ZCode，不能外推「三個 carrier 都有同名 Edit」。保留 fail-closed bool/absent 契約及明確錯誤；不臆測 coercion，live payload parity 列未驗，非擴張 acceptance 宣稱。

Method Coverage 修正後，原 fresh docs reviewer followup 無 findings：positive 路徑可查實際驅動、zero-hit 保留 unverified、已確認測試缺口仍可報 Important。15 份其餘 docs hash 未變。新 scoped docs diff hash `0adcacc1ee5a5c445ac36db3010b944e1bb261d0eeac60144e46ba1ddc197ab6`；audit-test 檔 hash `1d04b9f6fe2916c6b9c7c92a95ff82163748d166f1c593bbba116473c9e8a0cc`。

H4 修正與最後兩份 docs 的 intent delta 尚待回收；不以首輪排除的內容冒充已審。

Intent delta 已定向接續同一 Muse session，job `job-mude3ux5-5pw0cg`；只補 H4、Method Coverage、post-build／autonomous-execution 最後 delta，不重派已完成範圍。Native code reviewer 同步對原 findings 與 namespace shadow 反例 followup。

該輪結果：Muse 確認 Method Coverage Important resolved，最後兩份 docs PASS；H4 另以 in-memory probe 查得 `os.fdopen(f, "w")` 的 baseline deny 被 AST 忽略（Suggestion／evidence-based）。主 session 採納為 parity 修復，不只記限制。

Native followup 在同一 freeze hash 上確認原 F1/F2 resolved，但又找出兩個 confirmed regression：`io.open`／`builtins.open` Attribute Store 改綁，以及 `*args`／`**kwargs` mode unpacking，baseline deny → candidate allow。全部採納；不能把 111 個綠燈或 Muse 未找出這兩項當放行證據。

設計再裁決：不繼續增加半套 Python 型別／state 推導。將 filename-signature admission 收窄到已知 module import 前綴後的第一個直接 call；其餘 open 形態與 unpacking 回既有 heuristic，移除泛化的 trusted-name 假設。最後 code delta 須再經原 native reviewer 與 intent reviewer；docs 回執不受此 code-only delta 影響。

## 部署與其他靜態面

- 三端 bundle dry-run 成功，最終 docs source 為 36,643 bytes；相對 baseline 36,644 少 1 byte。Muse 36KiB cap 仍僅餘 221 bytes，99% WARN 保留。
- 全域 rules／skills／agents symlink 唯讀檢查指向 canonical ai-guide、target 存在；未從 authoring WT 改全域 pointer。
- rule-bundle 新版外部部署屬 pending；沒有把 WT 與舊 deployed bytes 差異報成已部署成功。single-source scanner 的既存 compact-restore wiring 缺口見 analysis.md。
- Muse plugin 與 code-reality binary surface diff 無命中，未更新外部 plugin/binary。
- `code-reality tour_validate --manifest --repo <WT>` exit 0，但明示 `.tours 無 .tour`，另有 dev binary provenance WARN；只有 manifest、沒有可驗 tour corpus，不宣稱 anchor 全驗收，也未擅改外部 binary。
- `uv run python hooks/post-build-gate.py --verdict` 回 exempt（本 branch 無 card）；不以 exempt 取代獨立 review 或 landing receipt。

## 最終收斂與接續驗收

原 task `01a0cb9c-5c76-7011-8044-85df1f3359fd` 最後停在 rebase 後，未 commit。接續 task 直接核對檔案、原 reviewer 最終回覆及 Muse terminal receipt，未將先前進度訊息當成驗收。

### 最終獨立審查與裁決

- Native code reviewer `01a0cbaf-9084-7520-89dd-28d140f3d829` 最後 followup：Attribute Store、unpacking、原 F1/F2 全 resolved；Python 3.9.6／3.14.4 獨立 probe 結果相同，H4 127 passed、4 deselected。無新阻擋項，changed-during-review=false。
- Muse `job-mudeh7dl-vq7yb6` completed、exit 0：同一 source/test identity 的最後 H4 delta 無阻擋項，fdopen parity finding resolved。非首個 call 的 write-looking literal 仍可能回到 baseline heuristic 誤攔；此 non-blocking Suggestion 接受為已揭露限制，不擴張成完整 parser。純變數 mode、unsupported Path.open／fdopen 的 r+ 等 baseline 限制仍在，不宣稱 sandbox。
- 最終 H4 SHA-256：hook `6a6aeaf3707f49f9a74893bd5f0e7d1bf8bfd8ae853a14475f7b15cbe5b87321`；tests `99d8b764bae4ef256b74788bb3a54eb63d55415ed0e2d73ec611b42ca956e2d2`。接續前 24 個來源檔全符合原 frozen manifest。
- 新 main 至 `5dc662da` 的交集僅 review-engine upstream freshness preflight。Native integration reviewer `01a0cd47-b34e-7130-9a83-546a804b1231` 確認兩組修改語義相容；將 upstream 一行還原後 hash 精確吻合原 manifest，其餘 23 檔未變。整份 review-engine consistency 及 18 個唯一 local Markdown links 通過，changed-during-review=[]。
- 整合後 review-engine SHA-256＝`6c41409484df853471b5dafbffaffa324c4876e5f39e85e60a8d2e2e76a162bf`；cr-query＝`6475dc1532286e68846db3abf1725cb2b3a54d3d723910ca8f22006eef900452`；guide＝`60871e91b596e36d4d5b602b7618aa23b6391a18a0edfce4c9d7901a8eac6a61`。

Judge：所有 accepted blocking findings 已閉合；既有方法論政策與 live payload 缺口維持 analysis.md 所列範圍，不把未實測項升格成已驗收。

### 整合後實跑

以下 pytest fixtures 均在 owning WT `.agent-tmp/`；全量執行加 `GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-rules-hooks/.agent-tmp` 以保留 non-repo fixture 的前提。

| 驗證 | 命令／範圍 | 結果 |
| --- | --- | --- |
| Focused | `PRE_COMMIT=1 uv run pytest tests/test_memory_hooks.py tests/test_block_memory_hook_suffix.py tests/test_compact_tail_inject.py tests/test_hooks.py -q --basetemp=.agent-tmp/resume-focused` | 238 passed |
| Full | `PRE_COMMIT=1 uv run pytest tests/ -q --basetemp=.agent-tmp/resume-full` | 1866 passed、2 skipped |
| 系統 runtime | `uv run --no-project --python /usr/bin/python3 --with pytest==8.3.5 python -m pytest tests/test_memory_hooks.py tests/test_compact_tail_inject.py tests/test_hooks.py -q --basetemp=<WT>/.agent-tmp/resume-runtime39-supported` | Python 3.9.6，192 passed |
| Memory entrypoints | 既有 runtime_probe.py 以 3.9.6／3.14.4 對 sensors、Edit deny/allow、helper 執行真 subprocess stdin JSON；fixture index／entry bytes 保持不變 | 兩端通過 |
| Scoped 靜態 | 4 個修改 hook＋4 個 tests：`uv run ruff check <paths>`、`uv run ruff format --check <paths>`、`uv run --with mypy mypy --follow-imports=skip <paths>` | 全通過；MyPy 8 source files |
| Bundle | `uv run python scripts/deploy_agents.py --dry-run` | 三端通過；36,760 bytes，Muse 36KiB gate 剩 104 bytes，99% WARN |
| Git／gate | `git diff --check`、`git config core.hooksPath`、`uv run python hooks/post-build-gate.py --verdict` | whitespace 通過；.githooks 在場；無卡 exempt |

一次 runtime 測試選擇錯誤如實保留：將 test_block_memory_hook_suffix.py 一併交給 Python 3.9 收集，因該測試檔既有 `str | None` annotation 發生 TypeError，未執行測試。repo 測試 runtime 要求 Python ≥3.12；沒有為此改 product／test。改以原有 subprocess runtime probe 驗部署 hook，並執行上表三個 3.9-compatible suites。

全 repo 靜態檢查未全綠：Ruff 91 findings／20 files；MyPy 152 errors／29 files。機械比對錯誤路徑與本弧 changed paths，交集皆空，均為 main 已有範圍外檔；本弧採上表 scoped 閘門，不修改無關檔案。MyPy 使用 follow-imports=skip 的 scoped 結果不代表完整 dependency typing。

本弧沒有新增需保留的 POC/demo；暫存 probes 的行為已由四個正式 tests 與本檔 evidence 承接。來源未變的早期雙 runtime、docs fresh、Muse intent 回執繼續有效；新 integration delta 已另驗。外部 bundle deployment 仍 pending，未執行 push；本機 live harness 事件未測，不以 subprocess 與 dry-run 冒充安裝驗收。

### 正常提交閘門的環境修正

第一次 commit 的 pre-commit suite 為 1 failed、1865 passed、2 skipped，commit 未成立。主 session 把 `PYTEST_ADDOPTS=--basetemp=<WT>/.agent-tmp/commit-fixtures` 傳入 git，test_segment_receipt.py 的 nested pytest 繼承同值；子程序 cwd 在該 basetemp 之內，pytest 明確拒絕 `basetemp must not be ... any parent directory of it`（config source: via PYTEST_ADDOPTS），exit 4。此錯誤已以原 fixture 獨立重現，非產品變更。

移除 PYTEST_ADDOPTS，改用 `TMPDIR=<WT>/.agent-tmp/commit-tmp`＋同一 GIT_CEILING_DIRECTORIES，讓各 pytest 自行建立獨立暫存目錄；原 test_pytest_capture_column 複驗 1 passed。正常提交閘門保留、不使用 no-verify；最終 commit 是否存在由 Git 判定，未用此單例通過代替完整 pre-commit suite。
