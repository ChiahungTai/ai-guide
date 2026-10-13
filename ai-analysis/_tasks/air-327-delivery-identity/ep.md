# AIR-327：交付身份與工作流一致性

> ep_type: implementation
> baseline: 7dbfd020fec402ca3c0eabb2c55a5752ae6e2057
> classification: boundary
> 狀態：S1–S3＋R1 修正完成、post-build 收斂；source 未commit／merge，另接歷史dry-run。

## 意圖與授權

AUTH: user said "ＯＫ就開卡實作吧，你可以sol 實作, flash, msue"

使用者已同意十月分析後開卡實作。卡 AIR-327 AC 為驗收源，主 session 為 Marshal/Arbiter，Sol 為唯一 writer，Flash 提供機械證據，Muse 提供獨立 findings。控制面 authoring 僅限 `/Users/ctai/Github/ai-guide-air-327`，primary 留 main；不得 commit、部署、改 memory 或寄信。主 session 管卡與回執。前期報告與 Muse 兩輪輸出位於 primary `.agent-tmp/oct-architecture-20261013/`。

## 段落 0：已完成研究與決策

歷史分析基線 9007350e；350 項 Arc 契約測試通過，15 個單一源 invariant 通過；不代表新身份要求已受測。既有 join 只核 card/unit/AC/verdict/evidence。原始 fixture PASS；修改 manifest contract_hash/verifier/expected 仍 PASS；刪 verdict 則 missing。可執行探針記錄在 primary `.agent-tmp/oct-architecture-20261013/join-replay-probe.log`。

owner：manifest 產生端 `scripts/arc_manifest.py`，collection 消費端 `scripts/arc_handback_join.py`，worker instruction owner `skills/_common/work-order.md`；監督 owner `skills/agent-workflow/SKILL.md`；部署事實 owner `governance/manifest.toml`。Blueprint 只合成，不是第二政策源。

### UC 與 invariant

- UC1：Marshal 收回 worker 交付時，確認它屬於當時分派的規格，拒絕舊規格回執。
- UC2：worker 可在 no-commit 權限下工作並提供活動證據，不以 commit 證活。
- UC3：新 session 從架構合成視角能找到當前部署定義源，不被退役描述引導。
- 身份通過與語義接受分離；FAIL/NOT-DONE 可結構有效，但不能宣稱完成。
- 不修改既有判死門檻、不合併 mail/bridge/harness watcher、不新增 cron。
- 不修改 model qualification policy/catalog，不重造派工引擎；SC 測試提案未獨立核實，另保留。

## S1：派工 manifest 與 handback 身份

Context：現行 manifest 具有 contract_hash，但 handback 無 echo；相同 card/unit/AC 不足以識別更新後的驗收條件。此段新增 shared contract，因此 full tier。

設計：以 assigned manifest 的 canonical JSON 內容計算 SHA-256，涵蓋所有語義欄位，包括 contract_hash、card/unit、完整 predicates；若 digest 為 manifest 的輸出欄位，自身欄位排除以避免遞迴。只允許 JSON 有限值，固定排序 key 與編碼；純 formatting/key order 不改 identity。producer 與 consumer 共用一個可測的定義，不複製 hash 規則。handback 必帶 digest，缺失或不符 fail-closed；未綁定的舊 handback 不默默通過。

dispatch 保存本次 assigned manifest 並把 digest 交給 worker；collection 必須用該凍結 artifact，不得重新投影最新 contract 來驗舊回執。修訂 plan 時另存新分派 artifact，禁止覆寫已發出的版本。此機制是 identity consistency，不是防惡意 worker 的認證簽章；artifact custody 仍歸 Marshal。不得用新增 attempt 綁定誤殺同規格合法 retry。

流程示意：既有 producer 投影 → 凍結 artifact/digest → worker 原樣引用 digest → join 檢查身份＋既有結構 → 獨立 review/judge。

EP review 裁決後的凍結契約：
- manifest schema=`arc-manifest/2`、handback schema=`arc-handback/2`，兩者欄位均名 `assigned_manifest_digest`。舊 `/1` 明確拒絕，既有在飛工作由 Marshal 用新規格重新確認／分派，不自動重派或重新造 PASS；本弧無在飛舊 Arc worker。
- digest 唯一定義放既有 producer `scripts/arc_manifest.py` 的公開純 helper；consumer 使用該 helper，不複製 canonicalization。內容為整份 manifest 排除自身 `assigned_manifest_digest` 欄位後，JSON sorted keys、compact separators、ensure_ascii=False、allow_nan=False 的 UTF-8 bytes SHA-256，輸出小寫 hex。此處只定本 manifest 契約，不順手抽取其他 Arc hash 系統。
- join 必須重算 supplied manifest digest，與 manifest 自報、handback echo、dispatch-recorded expected digest 三者比對；不能只比較兩個儲存欄位。join CLI 新增必填 `--expected-digest`，值由 Marshal 從 dispatch 記錄取出，不能從收線當下 manifest 臨時推導來替代。
- producer 對既有輸出檔只允許同 canonical 內容冪等重跑；任何不同內容或 malformed 既有檔 fail-closed，禁止靜默覆寫。先檢查整組輸出衝突再寫，並以 exclusive creation 保護新檔；遇並行競爭明確失敗，不宣稱整組交易原子性。
- dispatch 工單記錄 artifact path＋digest，`--out-dir` 使用本次 dispatch 唯一路徑；保存到本弧驗收與證據承接完成。修改規格產生新路徑，不覆寫舊 dispatch 目錄。

範圍：`scripts/arc_manifest.py`、`scripts/arc_handback_join.py`、必要的共用 helper、相關 tests/fixtures，及實際引用該契約的 active instruction。歷史報告與 archived tasks 不回寫。改動前查所有 active consumers，禁止只修 fixture 讓測試自洽。

獨立 oracle（實作前凍結）：
1. 原始正確配對 PASS；同內容 JSON key order/whitespace 改變仍 PASS。
2. contract_hash、verifier、expected、分派 predicates 各改一项，保留舊 handback，均 identity reject。
3. handback digest 缺失、錯誤型別、錯誤值均 reject。
4. 有效 digest 加缺 verdict、重複/未知 AC 或空 evidence 仍沿既有診斷拒絕。
5. 正確 identity 的 FAIL/NOT-DONE 仍 join exit 0；instruction 不允許把此當完成。
6. 真正 CLI producer→落檔→handback→join 正負各一輪；不得只有自寫函數測試。
7. 非有限 JSON 值不得產生可接受 digest。
8. 直接竄改凍結 manifest 且保留舊 stored digest，與重新投影新 digest 各測一次；兩者帶舊 expected/handback 均拒絕。
9. contract_hash 不變、重新分配 AC 子集，digest 改變且舊回執拒絕；相同內容合法 retry 通過。
10. producer 同內容重跑可通過、不同內容重用輸出路徑拒絕且原 bytes 保留；一組已知衝突不得先寫其他輸出。兩 CLI 對非有限值 exit2。
11. manifest、stored digest、handback 均有效且一致，只改 dispatch expected digest 必 exit2；正確 expected exit0；CLI 缺 --expected-digest exit2。暫時移除 expected 比對的 mutation 必被此獨立負例抓到，修復後還原實作。

驗證：先 RED 再實作；`uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py`，再受影響 Arc 套件；逐一真跑變更的 executable script，import/語法與型別依 repo 慣例。獨立 reviewer 重跑至少一個 mutation oracle。

## S2：移除 commit 證活的 authority 矛盾

Context：agent-workflow 約 line99 強制空 commit/逐修 commit，與 work-order no-commit fence 相衝。

設計：刪除「為觀測存活強制 commit」要求；以既有程序輸出、活動記錄、工作樹變更觀測即可，不新增 sidecar daemon。保留 terminal 與 hard-death authoritative evidence 既有分層，沉默不授權 kill/redispatch。單一源引用掃描涵蓋相關 active skill/role，不改 scope 外政策。

驗證：instruction-writing single-source scan；跨情境獨立審查 no-commit writer、silent active worker、authoritative terminal 三類；不寫鏡像字串斷言測試冒充行為證據。
補充：對 active skills/roles 執行 allow-empty 與證活 commit 敘述殘留掃描並逐項處置；既有在飛工單不因改文件自動更新，本弧 writer prompt 明示 no-commit，舊證活要求不適用。

## S3：刷新合成文件

Context：blueprint structure 的三 bundle/Claude symlink/三家族敘事已過期；governance 導航漏 grok；既有 index projection freshness 有 drift。

設計：依 manifest 與當前 owner source 更新 `ai-analysis/blueprint/structure.md`、`governance/AGENTS.md` 及必要的現有投影。优先引用 source，不新增 runtime authority。讀 blueprint/AGENTS.md 判斷影響面；既有 projection manifest 觸及則刷新並更新 hash，無法重投影時明示 stale，不偽造 current。不得新造投影引擎。

驗證：對照現行定義源；consistency；`uv run python scripts/projection_freshness.py --manifest ai-analysis/blueprint/projection-manifest.toml`；`uv run python skills/scan-project/scripts/check_single_source.py`。若還有非本弧 drift，明列範圍與處置。
S3 凍結範圍：structure.md 的 bundle/symlink/bridge/退役 wrapper 描述、governance/AGENTS.md 註冊導航，以及受影響的 blueprint/index.html 與 projection-manifest.toml。先重投影受影響內容，再 --update hash；禁止只更新 hash 洗綠。其他發現列 scope 外，不自動擴寫。

## 整合與收尾

單 writer 順序 S1→S2→S3；無其他 source writer 並行。review profile boundary：fresh-eyes 與 intent 分 context，另有 Muse 跨家族第二意見。Flash 只提供可核對機械證據、不裁決。主 session 裁決後 Sol 修正，followup 最多三輪；新 scope 重新分級。

依 post-build 完成 review ledger、consistency、metadata、consumer propagation、deployment surface probes 與 anchored receipt。部署未授權不執行，回執如實 pending；控制面尚未 merge canonical 時不宣稱已生效。記錄原生 subagent 通知＋bridge waiter 收線，user 已否決自掛 cron，採主 session 持續回收，不建立 automation。

## 進度

- 開卡與隔離 WT 完成；EP review 待回收。未開始實作。
- Muse EP review job-mv6b3a53-9r9lnd completed，F1/F2/F3/F4/F6 採納並凍結上述契約，F5 採納殘留掃描，F7 同步卡 baseline。另一獨立 Sol EP reviewer 待回收。
- Sol EP reviewer 01a133fa-5e07-7a00-b06a-53d8b1fd159c completed：唯一 remaining F1 為 expected-only oracle 缺口，採納為 oracle11。CR fresh current-tree，refs/callers 已核；無其他新增 boundary blocker。Marshal 裁決接受修訂後計畫，允許 S1–S3 實作。
- 最終：Sol完成14檔，GLM-5.3依user替代Muse（quota）做fresh/intent；native Sol reviewer容量失敗未計coverage。Marshal實測採納4 finding、原writer完成R1、GLM followup四項verified。修後全repo3929passed/1skipped；最終diff05c33e2b1fbec7b97f3af6229141300443442a98d936b295eb160e9fc6a170f8。完整來源、限制、回執見[post-build.md](post-build.md)。上方「待回收／未開始」為過程紀錄，以此終態為準。
