# AIR-327 Sol writer 最終交付（source frozen，待 parent 獨立驗收）

## Identity 與交付狀態

- WT：`/Users/ctai/Github/ai-guide-air-327`；branch `air-327`；HEAD/baseline `7dbfd020fec402ca3c0eabb2c55a5752ae6e2057`。開工核對 pwd/toplevel/branch/wt-identity.json。
- S1–S3 working-tree 實作完成，source 已凍結。無 actual implementation blocker；不宣稱卡 Done、最終 acceptance 或 live activation。
- 未 add/commit/checkout/backlog/deploy/memory/messages/delegation；主 session 的 EP/card/task index.html 未編輯。writer 的資料與證據只寫 `.agent-tmp/air327-writer/`；CR refresh 只寫本 WT graph/index。
- `source-frozen.patch`＝全部 tracked source diff，SHA-256 `f712089b2b671db3cb599237f0056ceeb0abb6c0ef63792ecf5461862969404a`。`changed-paths.txt` 與 `git-status-final.log` 為實際變更清單；staged diff 空，HEAD 不變。

## 實作

S1：manifest/handback schema 升 `/2`；producer 公開 `assigned_manifest_digest()` 是 canonical hash 單一源（整份 manifest 排除自身欄、sort_keys、compact、ensure_ascii=False、allow_nan=False、UTF-8 SHA-256）。join 共用 helper，重算 supplied artifact，核 stored/echo/dispatch expected 三值；CLI 必填 `--expected-digest`。非有限值拒絕，原 AC 結構診斷保留；正確 identity 的 FAIL/NOT-DONE 仍 exit0，completion 語義留給 Marshal。

producer 先 preflight 全組輸出：既有不同內容／malformed/nonfinite 拒絕，known conflict 不先寫其他輸出；同 canonical 內容保留原 bytes；新檔 exclusive creation，競爭 fail-loud。不同規格必用新 dispatch 路徑；不宣稱全組原子交易。

S2：移除空 commit／每修 commit 的強制證活；觀測使用程序輸出、exec/artifact 活動與 WT diff，尊重 worker 原 fence；沉默僅 advisory，terminal/hard-death/scope/retry-safe gates 仍指既有權威。work-order 與 agent-workflow 同步 dispatch path/digest、frozen artifact custody、legacy rejection、exit0≠completion。

S3：structure/governance 導航同步四 bundle、skills 母鏈、ZCode/grok agents、grok/ZCode/Codex registrations、CC 接線退役、single-file source、四 family bridge。先實改 blueprint HTML s12 與 s11 source navigation，再 --update：只有 structure 與 root audience 兩 upstream hash 改，其他三條未改；不新建投影引擎。

## 變更檔案（14）

- scripts/arc_manifest.py
- scripts/arc_handback_join.py
- tests/test_arc_manifest.py
- tests/test_arc_handback_join.py
- tests/fixtures/air-234/manifests/impl-a.json
- tests/fixtures/air-234/handback-pass.json
- tests/fixtures/air-234/handback-missing.json
- scripts/AGENTS.md
- skills/_common/work-order.md
- skills/agent-workflow/SKILL.md
- ai-analysis/blueprint/structure.md
- ai-analysis/blueprint/index.html（非 parent 的 task index.html）
- ai-analysis/blueprint/projection-manifest.toml
- governance/AGENTS.md

## RED／GREEN 與 mutation

| 指令 | 結果 | 證據 |
|---|---|---|
| `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py -q`（source 未改 baseline） | 48 passed | baseline.log |
| 同指令（新增 S oracle，production 未改） | 44 failed, 48 passed，exit1 | red.log、red-receipt.md |
| `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py -k 'TestDispatchCustody or TestAssignedIdentity' --basetemp=.agent-tmp/air327-writer/pytest-min -q` | 45 passed, 47 deselected | green-min.log |
| `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py --basetemp=.agent-tmp/air327-writer/pytest-green -q` | 92 passed | green-s1.log |
| `uv run pytest tests/test_arc_handback_join.py::TestAssignedIdentity::test_expected_only_oracle11 --basetemp=.agent-tmp/air327-writer/pytest-mutation -q`（暫移 expected 比對 tuple） | 1 failed：wrong expected 得 exit0，`assert 0 == 2` | oracle11-mutation.log |
| 同 test，`--basetemp=.agent-tmp/air327-writer/pytest-restored`（還原 tuple） | 1 passed | oracle11-restored.log |
| `uv run pytest tests/test_arc*.py --basetemp=.agent-tmp/air327-writer/pytest-arc -q`（還原、formatter 後最終源） | 386 passed | arc-suite.log |

oracle11 的 manifest、stored digest、handback 都正確且一致，只有 dispatch expected 改成 64 個 0；測試先證正向 exit0，再要求此負向 exit2，無其他結構 fault 掩護。mutation 已還原；最終 `scripts/arc_handback_join.py:91` 保留 expected 比對、`:230` 將 CLI expected 傳進 join。

新 oracle provenance＝S（accepted EP S1 oracle1–11，pre-GREEN 凍結）。GREEN 只遷移既有 `/1` fixtures/harness、補 subprocess check=False 與 formatter，不削弱新斷言。pre-GREEN test byte hashes 在 red-receipt.md；最終 hashes 見下。

## EP oracle 對帳

| EP oracle | 覆蓋 |
|---|---|
| 1 | 正確配對、JSON key order/whitespace、same-content retry |
| 2 | contract_hash/verifier/expected/predicate subset 各 mutation，stored digest 保留與重算兩形態 |
| 3 | echo digest 缺／wrong type／wrong value |
| 4 | 正確 identity 下 missing/duplicate/unknown verdict、empty evidence 沿既有診斷拒絕 |
| 5 | FAIL/NOT-DONE 正確 identity exit0；instruction 明示不等於完成 |
| 6 | 真 script producer→落檔→handback→join 正負，subprocess 與獨立 CLI logs |
| 7 | NaN/±inf 在 producer input 與 join manifest/handback 均拒絕 |
| 8 | tampered artifact 舊 stored digest 拒絕；新 digest 配舊 echo/expected 拒絕；另真 producer 新路徑 reprojection |
| 9 | AC 子集重派、contract_hash 不變而 assigned digest 改；舊回執拒絕；same-content retry 通過 |
| 10 | 保留 bytes 的冪等重跑／不同內容拒絕／全組 known conflict 零先寫／exclusive-create race／兩 CLI finite-negative exit2 |
| 11 | expected-only 正負、缺 flag CLI exit2、移除 expected check mutation 得 RED、還原 GREEN |

## 真 CLI（修改後 executable 實跑）

以下以 digest `961b585ef468a5a3861a04800d4a9ee7da1d63c6151d3cd3f8b7e3699d66b5f1` 為本 fixture dispatch 的獨立 frozen expectation；非 collection 即時從 supplied artifact 推導。

1. `uv run python scripts/arc_manifest.py tests/fixtures/air-234/contract.json --units tests/fixtures/air-234/units.json --out-dir .agent-tmp/air327-writer/dispatch-cli` → exit0，3 units/7 predicates（cli-producer.log）。
2. `uv run python scripts/arc_handback_join.py --manifest .agent-tmp/air327-writer/dispatch-cli/impl-a.json --handback tests/fixtures/air-234/handback-pass.json --expected-digest 961b585ef468a5a3861a04800d4a9ee7da1d63c6151d3cd3f8b7e3699d66b5f1` → exit0，join OK 3 predicates（cli-join-pass.log）。
3. 同 join 指令、expected 改 `0000000000000000000000000000000000000000000000000000000000000000` → exit2，唯一 diagnostic 是 dispatch expected identity mismatch（cli-join-expected-reject.log）。
4. `uv run python scripts/arc_manifest.py .agent-tmp/air327-writer/nonfinite-contract.json --units tests/fixtures/air-234/units.json --out-dir .agent-tmp/air327-writer/dispatch-nonfinite` → exit2，finite JSON required，無輸出（cli-producer-nonfinite.log）。
5. `uv run python scripts/arc_handback_join.py --manifest .agent-tmp/air327-writer/dispatch-cli/impl-a.json --handback .agent-tmp/air327-writer/nonfinite-handback.json --expected-digest 961b585ef468a5a3861a04800d4a9ee7da1d63c6151d3cd3f8b7e3699d66b5f1` → exit2，finite JSON required（cli-join-nonfinite.log）。
6. `uv run python .agent-tmp/air327-writer/cli-reprojection-probe.py` → exit0；內部真 producer 各 exit0，changed-contract/new-path 與同 contract 的 reassigned-subset 各搭舊 echo/expected join exit2。完整 actual commands、輸出在 cli-reprojection.log；後者另斷言 contract_hash 未變。
7. 缺 --expected-digest 的真 CLI subprocess → exit2，在 `TestAssignedIdentity.test_real_cli_producer_join_and_required_expected`，arc-suite.log 受測。

## 其他驗證

- `uv run ruff check scripts/arc_manifest.py scripts/arc_handback_join.py tests/test_arc_manifest.py tests/test_arc_handback_join.py` → All checks passed（ruff-final.log）。初次 5 lint findings 已修：unused noqa、import order、3 個 explicit check=False；未留 suppression。
- `uv run ruff format --check` 同四檔 → 4 files already formatted（format-final.log）。
- `uv run python -c …` → AST/import/fixture JSON/projection TOML 通過；實際 import 斷言 consumer helper 與 producer helper 是同一 function（syntax-import.log）。
- LSP `check_file` 對兩 executable 各 count=0。使用在場 pyrefly LSP face，未宣稱跑過 mypy。
- `uv run python scripts/projection_freshness.py --manifest ai-analysis/blueprint/projection-manifest.toml`：baseline 1/5 root audience drift（projection-before.log）；先改 HTML，再 --update 2/5；最後 fresh 5 upstream（projection-update.log、projection-after.log）。
- `uv run python skills/scan-project/scripts/check_single_source.py` → 15 invariants，critical0/important0（single-source.log）。
- `git diff --check` → exit0（diff-check.log；封存前再次 exit0）。
- `code-reality build --repo /Users/ctai/Github/ai-guide-air-327` 成功；freshness fresh=true、serves=current-tree、indexed/current identity 同 `caea62e3cdceac0560ad8d75aab43aa8ea9feba44479212f117c9688185b56cc`（cr-build.log、cr-freshness-final.json）。
- 最終 CR callers：shared helper 被 producer project_unit 與 consumer join 各一處呼叫；join 被 main 一處呼叫（cr-digest-callers.log、cr-join-callers.log）。graph 不覆盖所有动态/instruction literal consumers，與 literal inventory 分開列。

## Consumer inventory／disposition

- executable consumers：兩支 Arc CLI；測試 literal 機械反查只命中兩個直接測試檔；整合回歸仍跑全部 tests/test_arc*.py。
- active instruction：work-order Handback closure、agent-workflow collection join；均同步 `/2`/required expected/path/digest custody。scripts AGENTS 補 owner/入口 navigation。
- historical contract fixture `tests/fixtures/air-234/contract.json` 保留原 bytes 與 contract_hash H anchor；其舊 verifier/evidence 字串為歷史測試投影資料，未當現行 executable recipe 使用。manifest/handback fixture 介面已遷 `/2`。consumer-after.log 明列这些殘留，非漏掃；舊 schema `/1` 的其他命中只在拒絕測試／legacy rejection prose。
- S2 唯一強制證活 commit 源為 agent-workflow:99，已改；roles/impl-lite 與 generated copies 原本禁止 commit，保留。handoff/autonomous-execution/sitrep 的 AIR-296 引用已看，未自帶強制 commit，不需改。rebase 空 commit 語義、test setup commits 非證活用途，不改。liveness-consumers.log 保留掃描。
- S3 以 governance manifest/deploy generator/root source 核對，Flash 的只讀 anchors 作定位、非 runtime 證據；source 與 HTML 受影響段同形更新。
- archived tasks/reports、model catalog、watchers、hook implementation、primary/live 接線未擴改。

## 限制與 parent 下一步

- 本交付是 writer implementation＋evidence，獨立 consistency/review、GLM-5.3 外審、instruction pressure/application scenarios、裁決與 finalization 由 parent 接續；writer 沒有派工或以自述冒充這些驗收。
- S2 no-commit worker／silent active／authoritative terminal 三情境的独立 behavioral review 尚待 parent；本腿只提供源修改與殘留核對。
- 未跑全 repo pytest（已跑全部 Arc 386）；parent 視風險決定。沒有 scope 內 unresolved failing test。
- HTML 是 bounded source content refresh；未做瀏覽器/vision layout 驗收。既有非本弧全圖敘述（例如 invariant 舊計數、L4 schedule 快照、onboarding 舊敘事）未全面重審；projection hash fresh 只證 source fingerprint 對齊，不證所有 source 或機器現況正確。
- 未 merge/deploy；不宣稱 canonical/live 生效。producer 對未知並行 race 的多輸出集合不保證原子性；identity 不是認證簽章，artifact custody 仍歸 Marshal，均為 accepted EP 邊界。

## Frozen source hashes

- scripts/arc_manifest.py：`4817cbac70384a0f3a0297036de9013779dd29949d681702773d27db49bded38`
- scripts/arc_handback_join.py：`48434c04efeef8aefd1a6d5dac1c71600a2c864db67766a81bdb5712f119232c`
- tests/test_arc_manifest.py：`4bfc1ca4bcf35114f8c8c39e14622bbeea8eadf3cb8914763b773f7c51c6fd5d`
- tests/test_arc_handback_join.py：`cfa0834f0ffc9df9c43feda3ac2d96155b28912be917c4f5f3b797e30a5f340d`

Receipt scope: classification=boundary；writer evidence delivered；independent review/final acceptance parent-owned pending；deployment-surfaces=pending（未授權、本腿不執行）。

## Repair R1 最終追加回執（最新 source snapshot）

本節承接 Marshal 在獨立 GLM intent/fresh findings 與實際重現後授權的 bounded repair；上文初次交付與 hash 為歷史 snapshot，以下是最新凍結版本。WT/branch/HEAD 不變，未 staged/commit、未改 EP/card/report/ledger/docs/fixtures、未 delegation。R1 只改兩 executable 與兩個直接測試檔；無新 blocker。

### 四項處置

- **intent-F1**：`scripts/arc_handback_join.py:81` 只在 identity try 捕捉 `UnicodeEncodeError`，回穩定 `invalid: identity reason=manifest JSON 須能 UTF-8 編碼（孤立 Unicode surrogate）` 與 exit2。digest canonical definition／schema／expected binding 不變。
- **fresh-F1（pre-existing）**：`:155` grouping 前逐 verdict 驗 `ac_id` 為非空 string，非法 list/dict 先報 `invalid: verdicts[i] reason=ac_id 須為非空字串`，再沿原集合檢查報缺失；未捕捉任意 TypeError。
- **fresh-F2**：`tests/test_arc_manifest.py:381` 舊 `test_units_top_level_non_object_fails_clean` 回原 TestCli；原斷言不變。AST 機验其唯一 owner=TestCli，該 case 實跑通過，所有既有測試保留。
- **fresh-F3**：`scripts/arc_manifest.py:249` 在 `_manifest_filename` 的 suffix boundary 精確拒絕 NUL，raise ManifestError、unit_id 用 repr 安全診斷，exit2 且無輸出；未 blanket 捕捉其他 ValueError。

### RED → GREEN

新增 malformed-input regressions 前已讀兩份 GLM review 與 `.agent-tmp/air327-adjudication-repro.json`（parent 的 surrogate/list-ac/NUL 實際 exit1 重現）。新增 oracle 來源為 H 的實際 malformed input＋Marshal 先行採納的 exit2 目標，非 implementation 衍生。

| 指令 | 結果 | 證據 |
|---|---|---|
| `uv run pytest tests/test_arc_handback_join.py::TestMalformedInputRepair tests/test_arc_manifest.py::TestMalformedFilenameRepair --basetemp=.agent-tmp/air327-writer/pytest-r1-red -q`（fix 前） | **4 failed**：surrogate CLI exit1、list/dict 分組 TypeError、NUL ValueError | repair-r1-red.log |
| 上述兩 class 加 `tests/test_arc_manifest.py::TestCli::test_units_top_level_non_object_fails_clean`，`--basetemp=.agent-tmp/air327-writer/pytest-r1-min -q` | **5 passed** | repair-r1-min.log |
| `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py --basetemp=.agent-tmp/air327-writer/pytest-r1-target -q` | **96 passed** | repair-r1-target.log |
| `uv run pytest tests/test_arc*.py --basetemp=.agent-tmp/air327-writer/pytest-r1-arc -q` | **390 passed** | repair-r1-arc.log |

R1 pre-fix RED test bytes SHA-256：test_arc_manifest.py `6892c815c4047f063c6d7195ee16ca59f2de7290ec9b0387cfcbe7c22ddd0c05`；test_arc_handback_join.py `111f145792296e3be81d42180c5366943ad784d55484d9f653baef142105aeb2`。之後只有 formatter 與 F2 已授權 method 搬位，沒有削弱新增斷言。oracle11 仍在套件中通過；原 expected-only mutation 的移除／還原證據保留，R1 未移除或重寫該檢查（consumer 現在 :95）。

### 真 executable CLI malformed checks

`uv run python .agent-tmp/air327-writer/repair-r1-cli-probes.py` → exit0。完整四個 actual `uv run python scripts/<modified executable>` 指令與 stdout/stderr 保存在 **repair-r1-cli.log**；fixture variants 位於 repair-r1-cli/。

- supplied manifest `surrogate="\ud800"`：join exit2，identity UTF-8 diagnostic，無 traceback。
- handback list-valued ac_id：join exit2，`invalid: verdicts[2]`＋`missing: ac_id=3`，無 traceback。
- handback dict-valued ac_id：join exit2，同上，無 traceback。
- producer unit suffix embedded NUL：exit2，`不可含 NUL（檔名邊界）`，無 traceback；output directory 未建立。

所有 probe 走真 CLI/process/file boundary；case data 未重新計算 expected 來掩護故障。兩 modified executable 的正常 CLI 亦在 target/Arc 套件 subprocess 接縫案例實跑通過。

### 限定驗證與新鮮度

- `uv run ruff check scripts/arc_manifest.py scripts/arc_handback_join.py tests/test_arc_manifest.py tests/test_arc_handback_join.py` → All checks passed（repair-r1-lint.log）。
- `uv run ruff format --check` 同四檔 → 4 files already formatted（repair-r1-format-check.log）；`git diff --check` exit0。
- `uv run python -c …` AST/import/old-test-owner/share-helper identity 機验通過（repair-r1-syntax-import.log）。
- LSP check_file 兩 executable 各 count=0。
- source freeze 後 **只執行一次** `code-reality build --repo /Users/ctai/Github/ai-guide-air-327`，成功（repair-r1-cr-build.log）；freshness `fresh=true`、`serves=current-tree`、indexed/current identity 同 `96e8274817529b7360de59639a22b71ac527fde05b75be395314d4e74a90c467`（repair-r1-cr-freshness.json）。
- 未跑 full-repo suite；沒有重做 parent 的 consistency/review/finalization，也沒有新的 broader scan。S2/S3 documents 與 frozen EP identity contract 完整保留。

### R1 frozen identity

全部 tracked 弧 diff：**source-r1-frozen.patch**，SHA-256 **`05c33e2b1fbec7b97f3af6229141300443442a98d936b295eb160e9fc6a170f8`**（相對 baseline）。初次 source-frozen.patch 保留，未覆蓋。

- scripts/arc_manifest.py：`afda7513a6f370a438a042e0221da09140dbe3e1df7f4cdbe983471df4385e86`
- scripts/arc_handback_join.py：`4a7c7a11c34ed4c2a4fe3951f2ac0a0aac469f6c045a35831c42fbb6dbd7140d`
- tests/test_arc_manifest.py：`aacb710b6a64aefe9a808432a096c2819b3cc86fe2eb02370d5da59e7134387a`
- tests/test_arc_handback_join.py：`3e134d209acf1a079ea1c1695b1780d9d3e000ea10bb84cc07553f6b84553536`

**R1 bounded writer receipt：四項已實作與驗證，無實作 blocker；parent followup／final acceptance pending。**部署/merge/卡結算仍 parent-owned，未執行、不宣稱生效。
