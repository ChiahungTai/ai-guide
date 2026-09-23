# AIR-174 combined landing receipt

中間檢查點：實作與整合測試完成；等待最後 Codex followup、Muse Arbiter followup，再結算卡與 commit／merge。本檔後段最終結算優先於此檢查點。

AUTH: user said "那修好合併進來吧"

使用者另強調「原本rule hooks的修正是最重要的，你不要漏掉」。原始任務 `01a0cb9c-5c76-7011-8044-85df1f3359fd` 的 hardening 已在 main commit `639a479b5588e0f0e30821ec9411be536ea501bd`；這次基底 `7016266e61afc050062e1254ccd1ddcd7c52e33d` 包含它。此次收線涵蓋原 hardening 的三項審查修復、AIR-174 runtime migration 及其 consumer parity 修復。

## 原始 rules／hooks 保全

以 `git show 639a479b:<path>` 對目前內容逐檔比對原 commit 的全部 27 個檔案；未觸及的規則保持逐字相同。可執行驗證包含原有測試與新增反例，不以檔案存在冒充行為證據。

| 原始項目 | 本次結果 |
|---|---|
| H1 memory log 寫入目的地安全 | `memory_hook_common.py` 邏輯未改，僅 runtime docstring 更新；memory tests 通過 |
| H2 Edit final description admission | 保留 candidate 驗證；補 parser／generator normalization、duplicate key、CR-only／mixed newline 等價及 allow 對照 |
| H3 newest bounded compact tail | 保留 UTF-8 tail、JSON escape 與 bytes 上限；只排除完整 producer envelope，普通提及 marker 的內容保留 |
| H4 AST Python heredoc admission | `block-python-file-write.py` 與原 commit 逐字相同；原始 H4 regression 繼續通過 |
| R1 部署順序與落地 gate | `rules/AGENTS.md` 逐字保留；只做 authoring dry-run，未寫 live config |
| R2 carrier 背景能力契約 | tool-discipline、agent-workflow 逐字保留；rules-reminder 移除重複 Python 命令規則、改指向 owner |
| R3 查詢路由與 zero-hit 證據界線 | review-engine 及原有引用閉合檔逐字保留 |
| R4 hook runtime／registration owner | 更新為 installer 解析 managed 3.12；mixed-session rollback 仍保留 3.9 相容，compact restore 由 canonical ZCode template 管理 |
| R5 POC／NaN／carrier 細節 | 原修正保留；python-standards 補 hook owner compatibility 指針 |

三項修復細節、TDD 與 CR newline 補審見 [review-639a479b-repair.md](review-639a479b-repair.md)。原 hardening 的完整意圖與證據見 [原 EP](../rules-hooks-hardening/ep.md) 與 [原驗證報告](../rules-hooks-hardening/validation.md)。

## Runtime 與 consumer 收斂

- Installer 只在 install/check/verify 解析已安裝的 uv-managed Python 3.12 絕對路徑；hook fire 直接執行 interpreter，不經 uv／PATH／project discovery。
- CC 用 command＋args；ZCode 用 process argv；Codex shell string 經 shell-safe quoting。帶空白／單引號路徑由 fixture 驗證。
- Uninstall 使用不需 interpreter 的 identity render；missing resolver 在 check 回 drift exit 1，probe helper 回 GUARD，不破壞 tuple contract。
- 全 registration runtime token、registered hooks 的 Python 3.9 grammar、external UserPromptSubmit group preservation 均有 regression。
- 原 apply receipt 提到的 CC scanner 缺口已補：`_cc_wiring` 同時讀 command＋args；缺少 live exec hook 會報 critical，exec／legacy 兩方向 parity 都驗。新增三例先 RED，測試檔 97 passed。
- 靜態清理只涉及既存 lint/type 問題：bootstrap guard 與 rollback timezone 保留並附精準 noqa，stream annotation 改 TextIO，serialization kwargs 改 TypedDict，等價短路條件與明示 check=False。Formatter 的部分另做 AST 等價比對，21 個受檢檔全相同；未把 formatter 等價冒充其他修改的等價證據。

## 最終整合驗證

| Gate | 實際結果 |
|---|---|
| Repair focused／consumer | 230 passed；589 passed／1 intentional skip（先前 frozen repair revision） |
| Static cleanup affected tests | 448 passed；最小 5 passed |
| Combined full suite | **2083 passed／2 intentional skips，82.24s**（包含 IR1／IR2 最終修復） |
| Changed Python Ruff／format | 28 檔 Ruff 通過；27 檔 format 通過，write-path fixture 的既存格式債保留 |
| Scoped mypy | 27 檔通過；scanner 另有既存 15 errors，與 HEAD 的 error messages／類別相同，未新增，未擴張修復 |
| Python runtime | direct managed 3.12.13 與 `/usr/bin/python3` 3.9.6 entrypoints；registered hook 3.9 grammar gate 通過 |
| Isolated verify pipe | managed 3.12 執行真 memory gate，合成寫 MEMORY.md payload 被拒 exit 2，PASS |
| Bundle dry-run | 36,779 bytes；三端成功，Muse 36KiB gate 剩 85 bytes（既有容量警示） |
| Governance hooks dry-run | exit 0；只計畫、不寫 live config |
| Governance hooks check | exit 1，22 項 live drift；包含尚未投影 runtime、既有 duplicate groups、Codex trust Modified，未偽裝 parity 綠 |
| Diff whitespace | `git diff --check` 通過 |

完整測試命令：

```sh
GIT_CEILING_DIRECTORIES=/Users/ctai/Github/ai-guide-air-174/.agent-tmp PRE_COMMIT=1 uv run pytest tests/ -q -rs --basetemp=.agent-tmp/air174-landing/full-ir2-fixtures
```

兩個 skip 是 `test_githooks.py` PRE_COMMIT 巢跑 live 對照與 `test_matcher_parity.py` live drift；live parity 由 installer check 如實回報。Full host `--verify` 未重跑：Codex host fixture 會寫 memory canary、呼叫真 carrier，不以孤立 pipe PASS 代稱 host-level acceptance。未安裝或 approve live config，亦未推遠端。合併會更新 canonical symlink 指向的 rules／skills／hook source；新 runtime registration 與非 Claude bundles 仍待正式 deployment。

CR freshness preflight 缺 WT index，採 source／rg fallback，未宣稱 index 完整性。靜態型別檢查保留既存 untyped-body notes，不宣稱已檢查所有動態 fixture。

機械 logs、原 Muse judge/apply 回執、source hashes、AST receipts 在 `.agent-tmp/air174-landing/`；收 WT 前將保留到 primary `.agent-tmp/air174-landing-archive/`。主要結論與 finding 決策會隨本目錄進版控。

## Integration review amendment IR1（中間檢查點）

Native combined review found a confirmed ownership bug: shell quoting makes the raw-text identity regex miss package script paths under a repo root containing spaces. A same-event/matcher external Stop group can be overwritten, and uninstall leaves four package groups. Main adopts IR1 as Critical; previous full-suite green and Muse approval do not close C1/C2. Assigned bounded writer owns installer plus contract regression tests; require RED/GREEN and independent followup before commit. Original H1-H4/R1-R5 source preservation verified by the reviewer.

## Deployment 與 finalization 對帳

Surface registry 已枚舉四個 owner：rule-bundle 與 canonical skills/rules symlink 觸及；Muse plugin／code-reality binary 未觸及。三條宣告 symlink 均存在且指向 primary canonical，healthy。sync-sources 在 WT 回 0 critical／3 important（bundle 與未合併 source 不同）；primary 合併前已有三端 bundle stale 與 compact-restore 孤兒 registration 共 4 critical，非本次新造。此次 canonical registration 會修 orphan source，bundle deployment 依 authoring AC4 保留 pending，不能聲稱三端 runtime 已更新。live 22 drift 清單見 governance-check.log；待 canonical install、bundle deploy 與 trust approval 的驗收由 AIR-174 卡 Final Summary 持有，未擅開新卡或修改其他卡。

Tour corpus gate exit 0 但提示本 WT 無 .tour，沒有可驗證 corpus；無 snapshot pair，不產 delta tour。任務家無 HTML Report Shell，報告採既有 Markdown。Memory 不寫入；池索引查本弧無相關條目，無本弧 memory 清理。Improvement signals 為中間 review 殘留与全 repo commit recurrence，已有本弧修復／ledger 承接，沒有足夠新 actionable residue 另開候選。

### IR1 implementation evidence

`_codex_group_identity` now TOML-decodes command strings and shell argv before canonical-path matching; Codex uninstall uses the same quoted renderer with interpreter resolution disabled. Nine new contract cases cover normal, space, single/double quote paths and preserve the exact external Stop group while all owned groups are removed. RED 6 failed/3 passed; GREEN 9 passed; governance focused 156 passed; scoped Ruff/format/mypy pass. Source frozen: installer `11b88181995737b0e50ab555c4eeb8925feddbfb6ebf5ee22ca5394a62601388`, contract tests `14e34c67bc2fb66cbe180c8b34d6b2187b11c7e355622b9fa8a5a40935c79494`.

### IR2 compatibility amendment（中間檢查點）

IR1 has independent native/Muse approval and post-fix full 2042 passed/2 skips. Native reviewer additionally reproduced a valid vendor command `printf ok # dont` with an apostrophe in the comment: default shlex parsing treats it as an unterminated quote, blocking management of unrelated package groups. Main accepts IR2, keeps C1/C2 pending, and requires comment-aware parsing plus comment/quoted-hash positive controls. The 2042 green result is pre-IR2 evidence, not final acceptance.

IR2 boundary decision: ownership is a conservative recognizer for package-generated direct hook commands, not validation of all foreign shell syntax. Unknown/complex foreign commands must remain unowned and byte-preserved; template-owned identities must be nonempty and unique so recognition failure cannot collide with foreign groups. Native candidate probes additionally found that shlex comments=True truncates literal midword # and can turn a vendor data argument into a package-script match; this candidate was rejected, not accepted as a fix. Coverage includes comments, heredocs, literal hash suffixes and hook paths supplied as data.

### IR2 final candidate evidence

Conservative exact direct forms landed; comments=False avoids truncating midword hash, unrecognized foreign commands remain untouched. Shared template ownership guard is nonempty/unique in merge/remove/check. Corrected the legacy write-path fixture to current canonical root and explicitly asserted nonempty identity. RED stages: 8 failed/12 passed; 14 failed/20 passed; final exact-forms 16 failed/20 passed. GREEN owned contract/write-path tests 86 passed; governance focused 197 passed. Final all-changed lint: 28 Python files Ruff pass; 27 format pass (the narrowly repaired write-path test retains verified pre-existing formatting debt); 27 mypy pass excluding scanner whose 15 baseline errors are unchanged.

Native Codex writer/reviewer reached usage limit after worker receipt persisted; native final IR2 review did not complete. Final IR2 independent review is reassigned to a fresh Muse context, job-mudzulxa-e1dpd1, muse-spark-1.3 xhigh, not counted as completed until nonempty verdict is collected. Previous native reviews and Muse Arbiter judgments remain evidence for unchanged scope only.

## 最終結算

IR1、IR2 均已修復；fresh Muse IR2 job-mudzulxa-e1dpd1 APPROVE，main judge 採納，無未處理 blocker。原生 fresh/intent 與 Muse Arbiter 先前已完成，其最後 IR2 複驗因 quota 中斷，明確由 fresh Muse 獨立 context 接手，未冒稱 native 最後回執。最終整包測試 **2083 passed／2 intentional skips，82.24s**；來源 hash 與審查一致。M4 的 per-process cache 建議維持不採納；其他舊 finding、CC parity、IR1/IR2 與 M5 metadata 全部完成，見 review-ledger.md。卡已結案、保留原有三方審查 notes、五項 AC 與終態圖。

Receipt: classification=boundary / review=native fresh+intent, Muse external+Arbiter, fresh Muse IR2 final APPROVE (job-mudzulxa-e1dpd1); main judge adopts closure / session-freshness=fresh (source hashes verified) / deployment-surfaces=pending (live configs and bundles not deployed).

已授權 commit／merge；正常 pre-commit 與 ff-only 收線結果記錄於 Git commit 和 primary scratch archive，未推遠端。source readiness 完成，deployment pending 不被合併或卡狀態取代。
