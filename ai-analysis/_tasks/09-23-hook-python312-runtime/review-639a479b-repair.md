# 639a479b 審查修復

狀態：三項修復完成，最終機械驗證、fresh 複審、intent 最終快照與 Muse instruction 第二意見均已收斂，無未處理阻擋項。僅在 AIR-174 WT，未 commit／merge／deploy。

## 範圍與裁決

本次接手只修使用者提供的 `.agent-tmp/air-174-review-639a479b.md` 三項必修。AIR-174 已有未提交的 Python 3.12 runtime migration；其 installer、registrations、其他 hooks 與既有測試修正均保留。本報告不宣告 migration 已部署或 AIR-174 結案。

| Finding | 裁決 | 驗收要求 |
|---|---|---|
| memory `description :` 繞過 | 採納 | generator 消費的 description 正規化與選值一致；Write／partial Edit 的過長、hash、日期、session id 受擋，合法值與既有 body-only allowance 保留 |
| compact marker 誤殺 | 採納 | 完整 producer envelope 才濾除；普通提及、tag 開頭討論保留；真實 entrypoint output roundtrip 證明遞迴抑制；最新 role／timestamp／byte budget 維持 |
| Python instruction 衝突 | 採納 | rules-reminder 指向 tool-discipline；python-standards 尊重 hook owner runtime compatibility；bundle dry-run 過閘 |
| AIR-174 保持 To Do | 不直接套用歷史判斷 | 639a479b 的確不構成 migration；但本次接手時 migration 已有實作。狀態應依當前卡與驗收，而非依舊報告倒退 |
| STATE 改取尾段 | 不採納 | 建議以 STATE append-only 為條件，未成立；此次維持 STATE 既有讀取契約 |
| 全測 Git 隔離條件 | 保留可重現命令 | repo 內 temporary fixtures 須設 GIT_CEILING_DIRECTORIES；不把缺少環境條件造成的測試失敗冒充產品 regression |

## 證據界線

CR freshness 回報此 WT 缺 `.code-reality/scip/index.scip`；可用工具沒有 LSP references 面。此次以 current source、文字引用掃描與 executable regression tests 驗證，未作 index 完整性宣稱。

修復前六個目標檔、副本與既有 working diff 已保存於 `.agent-tmp/review-639a479b-repair/`，hooks/AGENTS.md 在文件同步前另存。該目錄的 diff/worker logs 用於區分本次修復與既有 migration；長期判準與最終結果由本報告承接。

## 驗證與獨立審查

### 最終 revision 機械驗證

| 驗證 | 結果 |
|---|---|
| 新增 newline regression | RED 32 failed／8 passed → GREEN 40 passed |
| 兩個修改測試檔 | 230 passed，無 skip |
| memory／compact／hook／governance consumer sweep | 589 passed／1 skipped |
| 全套 `tests/` | 2030 passed／2 skipped |
| 兩個 hook 真實 interpreter subprocess | managed Python 3.12.13 與 system Python 3.9.6 均通過 spacing／newline deny-allow、marker mentions、producer envelope roundtrip |
| 四個修改 Python 檔 | Ruff check、format check、mypy 全過；git diff --check 通過 |
| bundle dry-run | 三端通過；36,779 bytes，Muse 36KiB gate 剩 85 bytes，有接近上限警告 |
| governance hooks dry-run | exit 0，三端 projection plan，零 live writes |
| preservation | 七個修復目標檔以外的既有 migration diff 逐區塊 byte-identical；七檔已 freeze SHA-256 並複核 |

Primary 最終 pytest 命令（cwd＝AIR-174 WT）：

```sh
GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-air-174/.agent-tmp PRE_COMMIT=1 uv run pytest tests/test_memory_hooks.py tests/test_memory_lifecycle.py tests/test_block_memory_hook_suffix.py tests/test_compact_tail_inject.py tests/test_hooks.py tests/test_matcher_parity.py tests/test_governance_verify.py tests/test_check_single_source.py -q -rs --basetemp=.agent-tmp/review-639a479b-repair/consumer-final-fixtures
GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-air-174/.agent-tmp PRE_COMMIT=1 uv run pytest tests/ -q -rs --basetemp=.agent-tmp/review-639a479b-repair/full-final-fixtures
```

兩個 intentional skips＝`tests/test_githooks.py:296` 的 PRE_COMMIT 對照腿，以及 `tests/test_matcher_parity.py:96` 的 live drift 偵測；屬 `PRE_COMMIT=1` 既有隔離策略。未因此宣稱 live firing／deployed-config parity。完整 logs 在 scratch 的 `consumer-final-tests.log`、`full-final-tests.log`；各 interpreter 與 TDD 明細見 `code-receipt.md`。

初次 `uv run mypy` 因環境未安裝 mypy 而無法 spawn（exit 2）；改用 `uv run --with mypy mypy --follow-imports=silent --ignore-missing-imports` 檢查四檔，exit 0、no issues found。未修改 project dependency。

### 第一輪與追加發現（尚非最終驗收）

- 原始修復 RED：40 failed／24 passed；第一輪 focused GREEN：64 passed；owned tests：154 passed（runtime 參數擴充前）。主 session consumer sweep：549 passed／1 skipped。
- Muse external (`job-mudxzuo8-2pgycm`，model request `muse-spark-1.3`、effort high) 三份 instruction delta 審查無阻擋項。三個 advisory 暫不改：ai-guide 限定的 owner pointer 沒有宣稱他 repo 也有該檔；型別例外已限定「相容性所需」，無須重刻 whitelist；uv 口訣非新的 runtime authority。其 A2 把 `X | None` 說成 3.9 parse failure 不精確，主要是 annotation evaluation/import compatibility，不能只靠 syntax gate 證明；本次以真實雙 runtime entrypoint 複驗補強。
- Native intent docs leg (`01a0cdbf-3ab2-7c02-b8ca-d64ac13a0db7`) 無 actionable finding；普通 script、hook fire、隔離複驗、共用 helper、rollback typing 的選擇符合預期。屬輕量 application 輸出，未執行命令，非完整 control/treatment 行為實證。
- Native fresh (`01a0cdc0-3908-7420-90b8-775f7a31ea02`) finding **CR1／Important／confirmed**：原始 content 的 lone CR 未正規化，但 generator `Path.read_text()` 會 universal-newline 轉成 LF，因此修復 parser 的首行判斷新增 CR-only Write 繞過。採納；primary 已用真實 write_bytes/read_text 複現換行差異。要求補讀檔型 consumer oracle、CR-only／mixed newline 與 Write／Edit regression，再修 parser。先前 GREEN 不代表此缺口已關閉，當時進行中的 full run 只作 superseded evidence。

Bridge waiter 因 repo checkout binary 不提供可辨版本而 exit 2；未重派 job、未重試 waiter，改由同 job 原生 `wait --json` 回收 completed 與非空 finalText。外審全文已保存 scratch，沒有把 worker terminal 狀態單獨當 review 證據。

### CR1 closure

Fresh reviewer 原 context 回頭驗收最終 revision：CR1 已關閉，無新 blocking finding；20 個 CR／mixed × Write／partial Edit × deny-allow probes 通過，8 個 legacy body-only 對照仍放行。確認 test oracle 已經過真實 write_bytes→read_text→generator parser。

已審產品 SHA-256：

```text
6945c4d08817f5bc38b0e83549b82705f81d9abd23140b58c746e31465ccd408  hooks/block-memory-index-write.py
39f6dee2ca0a0aed48be7554574cdde2183cd32a6dbe9dfe63ddf84ea046da33  hooks/compact-tail-inject.py
```

### 最終獨立審查回執

Intent reviewer (`01a0cdbf-3ab2-7c02-b8ca-d64ac13a0db7`) 再讀 CR1 修復與讀檔型 oracle、核對七檔實際 hash 與 frozen manifest 一致，最終 `APPROVE / no-blocking`。Fresh reviewer 的 CR1 closure 與 Muse 三份 instruction review 均已回收。主 session 裁決：三項必修全部採納並實作；CR1 採納並補修；Muse 非阻擋 advisory 維持前述不採納理由，沒有 pending finding。

Receipt：`classification=boundary / review=fresh+intent+Muse external complete（本報告各腿 ID、證據與裁決） / session-freshness=fresh（current WT source 與最終 hashes 已核對；未更新 live guidance） / deployment-surfaces=unverified（未部署）`。

剩餘工作邊界：本次 review-repair 已完成；AIR-174 整體 migration 的既有 post-build ledger、live deployment／新 session firing、commit／merge 與卡片結案需另依其 owner 流程結算，不能由本報告取代。未修改 primary board metadata，也未把舊 ledger 的 migration findings 擅自標成 closed。
