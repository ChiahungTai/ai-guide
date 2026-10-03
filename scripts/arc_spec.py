#!/usr/bin/env python
"""arc_spec——AIR-135.1 S1 schema-first compiler：ArcSpec／ArcPlan／DispatchSlice／receipt 四物欄位 schema＋fail-loud 校驗。

邊界（卡面 Plan D1-D8 已決策勿重辯）：
- D1：只做「卡面契約→派工單靜態物」的編譯與校驗；journal replay／admission
  限流／計量歸 AIR-135.7 runtime——本檔不建引擎。
- D2 ownership：ArcSpec＝ephemeral（編譯器寫）／ArcPlan＝穩定版控（recompile
  產新版本、禁原地改）／DispatchSlice＝派工時 JIT 填 runtime 欄／receipt＝
  worker 寫、marshal 驗。
- D3 欄位二分：machine-invariant（缺欄禁派工）vs llm-guidance（敘述性 prompt
  材料）——每欄顯式標注（`schema` 子命令輸出欄位表）。
- D6 終態語義：on_budget_exhausted=budget-limited（BudgetLimited 終態而非軟
  警告）、raise_cap=human-action（raise-cap 是人類動作）、settle_gate=human
  （settle 尾 commit/push outward 不在自動終態內）。

PLAN_CHANGES 修訂流（D4——本 slice 只定義流程文件，引擎不建）：
- implementer 禁改 ArcPlan 原文——只能往 `plan_changes[]` 追加偏差記錄
  （Deviations-only；grok 借鑑 #5）。
- 每筆 plan_changes 須附 `what`（偏差什麼）＋`diff`（原文→現行）——交驗收腿
  複核；「弱化／刪除／自利條款本身即駁回理由」。
- 卡面／契約層級的變更不走 plan_changes——走 recompile：新 ArcPlan 版本
  supersedes 舊版（D2 禁原地改；AC#1 supersedes trail）。

版本與 hash（AC#2）：ArcPlan 帶單調版本號＋決定性內容 hash
（sha256 of canonical JSON——sort_keys＋緊湊分隔符＋UTF-8；禁 process-salted
hash）。DispatchSlice 與 receipt 以 plan_version／plan_hash 回指。

acceptance_contract 區塊（AIR-135.1.1 C5b）：ArcPlan machine-invariant 選填
區塊——`scripts/arc_goal_compile.py` 從卡 AC explicit verifier 編出（producer
單一源；本檔只擁 schema＋validate）：predicates（ac_id/kind/verifier/expected/
satisfied/satisfied_at_baseline）＋judgment_required（ac_id/reason）＋ac_ids
（AC 全集——使集合不變式四條可在無卡環境機驗：predicates/judgment_required
exactly-once、聯集=全部、交集=空）。選填＝本弧 back-compat（既有 plan 無此塊
仍合法；AIR-135.1.2 lifecycle wiring 收緊必填）。

closure_coverage 硬閘（AIR-235）：ArcPlan machine-invariant 欄——收線鏈五站
post-build/review/judge/landing/settle 各 {station, unit_ref, owner, gate}；
compile stage 驗全站在場（waiver 站豁免）＋unit_ref 回指 work_units＋owner
站別一致（judge/landing/settle 恆 main-session、review 恆 dispatch）——缺站
逐行 fail-loud 列可用站別。顯式逃生口＝`chain_waiver`（stations＋reason 必填
——顯式勝於歧義）。coverage 只在 compile stage（plan 定版時驗；dispatch 不
重驗，slice 是 per-unit 物）。work_units.phase 收斂 enum build/post-build/
review/judge/land/settle（135.3 六站的操作軸映射，六站語義不重定）。

temporal_allocation 意圖欄（AIR-240）：ArcPlan machine-invariant 選填區塊
（頂層或 per-work_unit——兩處皆可，單位級細化頂層預設）；在場則七鍵全到
（禁部分宣告歧義）：preferred_family（枚舉＝FAMILIES）／planned_not_before
（ISO 8601 帶時區——排程意圖，未來時點合法）／on_unavailable（delay｜
fallback）／fallback_families（explicit-only：fallback policy 須帶非空顯式
集合、禁含 preferred_family、禁與 delay 並存——值歸 resolver 於派工當下
重驗 availability，schema 只鎖形）＋provenance 三鍵 entitlement_snapshot_ref/
hash/as_of。compile 機驗（provenance 不隨 stage 豁免——plan 是凍結物）：
ref 相對 plan 檔所在目錄解析且檔必存在、hash＝sha256(canonical JSON) 比對、
as_of 非未來且與快照 generated_at 一致、rows 非空且非全 stale（missing/
stale provenance 逐行 exit 2）。**stale 閾值 ownership 在 producer**
（entitlement_window_snapshot.py：probe 26h／spine 3d——AIR-239 單一時鐘
R2），本 validator 消費 rows[].freshness 標籤、不自備第二時鐘；牆鐘只用於
as_of 非未來（過去 frozen fixture 恆綠——AC 驗證器時間穩定）。**provenance
機驗＝producer-attested freshness（自簽自驗）；非防偽**——hash 只證明 plan
引到「這份內容」，不證明 freshness 計算可信；真閘＝dispatch JIT
AvailabilitySnapshot（resolver 七步第 4 步，model-routing 契約面）。
**易爛真值禁令**——禁令範圍＝temporal_allocation block 閉集＋**全 plan
volatile-key 黑名單**（頂層＋work_units[i] sibling，莖詞閉集
VOLATILE_TRUTH_STEMS：quota／reset／retryable_at／available_now——
quota_remaining／next_reset_at／reset_at 等現值欄經莖詞命中即錯）；
**非全 plan 白名單**（ArcPlan 載 producer 自選 Optional 區塊——全 plan
白名單會耦合每個 producer，非 volatile 新 key 不攔）。DispatchSlice carry-through：preferred_
family／on_unavailable／fallback_families 同欄投影（選填 machine-invariant
、值歸 resolver，schema 留欄）。FAMILIES 擴 grok（AIR-240 裁決：AIR-226
bridge-grok-grok-4.7 binding 在場——有 binding 的 family 須有合法 slice 值
；與 catalog.toml families 閉集的軸差＝grok bindings 的 catalog family
label 為 xai，顯式映射表釘在 tests/test_arc_spec.py
TestFamiliesCatalogConsistency）。model-routing 契約面：EntitlementWindow
Snapshot／ArcPlan temporal 意圖＝advisory planning evidence；Availability
Snapshot＝dispatch 唯一 live authority（resolver 七步不動——窄改記於
model-routing SKILL.md）。

fail-loud 文案形（codex multi_agents_common.rs:395-442）：
    Unknown model `X` for spawn_agent. Available models: A, B
本檔同形：缺欄列出全部必填、未知枚舉列出可用值、雙 authoritative 值／非有限
預算即錯——讓呼叫方可自修，不靜默猜。

檔案形態：四物以「人類可讀 markdown＋```json 區塊」承載（卡面作者＝user/LLM
可讀；機器驗 json 區塊）——`validate` 同時收 .json 直檔。

CLI：
- `uv run python scripts/arc_spec.py schema [--kind KIND]`——欄位表（含
  machine-invariant／llm-guidance 標注；人類與 LLM 的 schema 讀取面）
- `uv run python scripts/arc_spec.py validate --kind KIND [--stage compile|dispatch] FILE`
  — exit 0＝通過；exit 2＝校驗失敗／contract 錯（錯誤逐行 stderr）
  （exit 契約對齊 reconcile_memory_pool 慣例：2＝contract/infra 錯）

stage 語義（D5）：compile＝ArcPlan 編譯當下（resolver 欄可缺席）；dispatch＝
派工當下（family/model/binding/ledger/dispatch_id 必到——值歸 model-routing
resolver 於呼叫面填，schema 只留欄）。
"""

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_ARC_SPEC = "arc-spec/1"
SCHEMA_ARC_PLAN = "arc-plan/1"
SCHEMA_DISPATCH_SLICE = "dispatch-slice/1"
SCHEMA_SLICE_RECEIPT = "slice-receipt/1"
# acceptance_contract 區塊 schema marker（AIR-135.1.1 C5b——區塊非第五 artifact：
# 無 KINDS/validate 入口，producer＝arc_goal_compile.py）
ACCEPTANCE_CONTRACT_SCHEMA = "acceptance-contract/1"
# predicate kind 枚舉（v1 唯一產出 command_expected；餘為保留枚舉）
PREDICATE_KINDS = ("command_expected", "artifact", "schema", "state_transition")
# judgment_required reason 枚舉（C5b v1 唯一值）
JUDGMENT_REASONS = ("no-explicit-verifier",)

KINDS = ("arc-spec", "arc-plan", "dispatch-slice", "receipt")
STAGES = ("compile", "dispatch")

ROLES = ("implement", "review", "verify", "test", "intent-review")
# work_units.phase 收斂 enum（AIR-235）：收線鏈操作站別，取 v2 已實踐語彙追認
# 為正式詞彙——非 135.3 六站直抄（六站＝obligation 層人類 gate 站牌，phase 是
# transport 層操作軸；六站無 Land 站，直套＝跨層綁定）。映射一行：build↔Build、
# post-build/review↔Verify、judge↔exit Align、land/settle↔Settle 域——六站語義不重定。
PHASES = ("build", "post-build", "review", "judge", "land", "settle")
# 收線鏈 coverage（AIR-235）：五必含站＋owner/gate 枚舉——compile stage 驗；
# owner 站別一致性：judge/landing/settle 恆 main-session（codex/glm 共識：把
# 這三站塞 dispatch 是假語義）、review 恆 dispatch；post-build 兩形皆可。
COVERAGE_STATIONS = ("post-build", "review", "judge", "landing", "settle")
COVERAGE_OWNERS = ("main-session", "dispatch")
COVERAGE_GATES = ("human", "commit-consent", "none")
STATION_OWNER_FIXED = {
    "judge": "main-session",
    "landing": "main-session",
    "settle": "main-session",
    "review": "dispatch",
}
READ_SET_POLICIES = ("full-context", "problem-contract-only", "chain-exclusion")
# AC#2 role-dependent read-set（0919 外部收割＋0920 修訂）：same page ≠ same
# projection——review/verify/test 只給 problem/behavior contract（禁逐字繼承
# implementer reasoning）；intent-review＝chain-exclusion（只給 entry 六欄凍結
# 基線＋final artifact＋機械驗證證據包，禁含中間 plan／review／court 討論）。
ROLE_READ_SET: dict[str, tuple[str, ...]] = {
    "implement": READ_SET_POLICIES,
    "review": ("problem-contract-only",),
    "verify": ("problem-contract-only",),
    "test": ("problem-contract-only",),
    "intent-review": ("chain-exclusion",),
}
# family 枚舉（AIR-240 擴 grok）：AIR-226 bridge-grok-grok-4.7 binding 在場
# ——有 binding 的 family 須有合法 slice 值（delegate-bridge 四家族語彙）。
# local＝in-harness spawn（無 catalog binding）。與 catalog.toml families 閉
# 集的軸差＝grok bindings 的 catalog family label 為 xai——顯式映射表釘在
# tests/test_arc_spec.py TestFamiliesCatalogConsistency。
FAMILIES = ("local", "muse", "codex", "glm", "grok")
# temporal 意圖欄（AIR-240）：on_unavailable 枚舉＋planning snapshot schema
# marker＋block 閉集（易爛真值禁令的機械落點——閉集外 key 即錯）
TEMPORAL_ON_UNAVAILABLE = ("delay", "fallback")
TEMPORAL_SNAPSHOT_SCHEMA = "entitlement-window-snapshot/1"
TEMPORAL_ALLOCATION_KEYS = (
    "preferred_family",
    "planned_not_before",
    "on_unavailable",
    "fallback_families",
    "entitlement_snapshot_ref",
    "entitlement_snapshot_hash",
    "entitlement_snapshot_as_of",
)
# 易爛真值黑名單（AIR-240 R1——repair-1）：全 plan volatile-key 掃描的莖詞
# 閉集（key 子串命中即錯）——quota_remaining／next_reset_at／reset_at／quota
# 及現值變體皆經莖詞覆蓋。黑名單非白名單：非 volatile 新 key 不攔（extension
# surface 開放）；temporal_allocation block 另有閉集（更嚴）。
VOLATILE_TRUTH_STEMS = ("quota", "reset", "retryable_at", "available_now")
TERMINALS = ("completed", "budget-limited", "blocked-human-decision", "failed")
CAPABILITY_MODES = ("ReadOnly", "ReadWrite", "Execute", "All")
AUTHORITIES = ("writer", "read-only")
COLLECTION_MODES = ("waiter", "bounded-receipt", "manual")
DELIVERY_VERDICTS = ("delivered", "undelivered", "manual-anchor", "not-assessed")
COMMIT_DELEGATIONS = ("none", "conditional-this-repo")
# 135.3 AC#7（S3 接線）：Intent Review 驗收腿回寫 verdict 枚舉——receipt.intent_review 欄
INTENT_REVIEW_VERDICTS = ("GO", "GO-WITH-FIXES", "NO-GO")

TERMINAL_SEMANTICS_FIXED = {
    "on_budget_exhausted": "budget-limited",
    "raise_cap": "human-action",
    "settle_gate": "human",
}
BASELINE_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ArcSpecError(Exception):
    """contract/infra 錯（未知 kind/stage、schema marker 不符、檔案壞）——fail loud。"""


@dataclass(frozen=True)
class FieldSpec:
    """單欄定義——D3 二分（machine-invariant vs llm-guidance）的最小單位。

    required_at：always＝兩 stage 皆必填；compile/dispatch＝該 stage 必填
    （另一 stage 可缺席）；conditional＝必填性由該 artifact 深檢決定（如
    accept——sink 為 artifact 時才必帶）；never＝llm-guidance（自由選填）。
    """

    name: str
    kind: str  # "machine-invariant" | "llm-guidance"
    required_at: str  # "always" | "compile" | "dispatch" | "conditional" | "never"
    desc: str
    values: tuple[str, ...] | None = None  # 枚舉（codex 式錯誤列可用值）
    noun: str = ""  # 錯誤文案的欄名詞（預設＝name）
    plural: str = ""  # "Available <plural>: ..."（預設＝noun+"s"）
    nullable: bool = False  # key 在場時允許 null/[]（如 supersedes、初始 plan_changes）；key 缺席仍 fail-loud


@dataclass(frozen=True)
class ArtifactSpec:
    kind: str
    schema_marker: str
    title: str
    ownership: str
    fields: tuple[FieldSpec, ...]


ARTIFACTS: dict[str, ArtifactSpec] = {
    "arc-spec": ArtifactSpec(
        kind="arc-spec",
        schema_marker=SCHEMA_ARC_SPEC,
        title="ArcSpec——目標契約（entry 六欄正規化）",
        ownership="D2：編譯器寫、ephemeral（不進版控；ArcPlan 封存後即棄）",
        fields=(
            FieldSpec("schema", "machine-invariant", "always", "schema marker",
                      values=(SCHEMA_ARC_SPEC,), noun="schema marker", plural="schema markers"),
            FieldSpec("card_id", "machine-invariant", "always",
                      "卡節點身分——work unit identity 錨點（AC#5）"),
            FieldSpec("card_baseline", "machine-invariant", "always",
                      "弧啟動釘住的 card tree baseline SHA，hex 7-40 位（AC#1；baseline 後卡面變更＝recompile 新版本）"),
            FieldSpec("source_card", "machine-invariant", "always",
                      "卡檔 repo 相對路徑（provenance）"),
            FieldSpec("intent_verbatim", "machine-invariant", "always",
                      "entry 欄 1：原始意圖逐字凍結（禁改寫）"),
            FieldSpec("non_goals", "machine-invariant", "always", "entry 欄 2：不做什麼"),
            FieldSpec("revert_budget", "machine-invariant", "always",
                      "entry 欄 3：revert 預算（priced-autonomy；AC#1 缺場禁派工）"),
            FieldSpec("pre_authorizations", "machine-invariant", "always",
                      "entry 欄 4：預授權類（priced-autonomy；AC#1）"),
            FieldSpec("assumptions", "machine-invariant", "always", "entry 欄 5：假設台帳"),
            FieldSpec("success_predicate", "machine-invariant", "always",
                      "entry 欄 6：成功謂詞（priced-autonomy；AC#1）"),
            FieldSpec("context_notes", "llm-guidance", "never",
                      "敘述性背景材料（D3：prompt 材料禁入 machine-invariant 欄）"),
        ),
    ),
    "arc-plan": ArtifactSpec(
        kind="arc-plan",
        schema_marker=SCHEMA_ARC_PLAN,
        title="ArcPlan——穩定計畫（版本號＋內容 hash）",
        ownership="D2/D4：編譯器寫、穩定版控；recompile 產新版本 supersedes、禁原地改；implementer 只能加 plan_changes 偏差記錄",
        fields=(
            FieldSpec("schema", "machine-invariant", "always", "schema marker",
                      values=(SCHEMA_ARC_PLAN,), noun="schema marker", plural="schema markers"),
            FieldSpec("card_id", "machine-invariant", "always", "卡節點身分回指"),
            FieldSpec("card_baseline", "machine-invariant", "always", "card tree baseline SHA（承 ArcSpec）"),
            FieldSpec("version", "machine-invariant", "always",
                      "單調版本號，正整數（recompile 產新版本、禁原地改）"),
            FieldSpec("plan_hash", "machine-invariant", "always",
                      "sha256(canonical JSON−plan_hash)，hex 64 位；禁 process-salted hash（AC#2）"),
            FieldSpec("supersedes", "machine-invariant", "always",
                      "前一版本號或 null（supersedes trail；須小於自身版本）", nullable=True),
            FieldSpec("work_units", "machine-invariant", "always",
                      "工作單元列表——unit_id 錨 card node id（唯一）、role 枚舉、"
                      "phase 枚舉 build/post-build/review/judge/land/settle（135.3 六站"
                      "映射：build↔Build、post-build/review↔Verify、judge↔exit Align、"
                      "land/settle↔Settle 域——transport 層操作軸，六站語義不重定）、"
                      "depends_on 拓撲"),
            FieldSpec("closure_coverage", "machine-invariant", "compile",
                      "收線鏈 coverage（AIR-235）：五站 post-build/review/judge/landing/"
                      "settle 各 {station, unit_ref, owner, gate}——owner 枚舉 "
                      "main-session/dispatch、gate 枚舉 human/commit-consent/none；"
                      "compile stage 驗全站在場（waiver 站豁免）＋unit_ref 回指 "
                      "work_units＋owner 站別一致（judge/landing/settle 恆 main-session、"
                      "review 恆 dispatch）；dispatch 不重驗（slice 是 per-unit 物）",
                      nullable=True),
            FieldSpec("chain_waiver", "machine-invariant", "never",
                      "顯式逃生口（AIR-235）：{stations: [...], reason: str}——列出豁免 "
                      "coverage 的站別；reason 必填（缺席/空字串＝exit 2）——顯式勝於歧義"),
            FieldSpec("temporal_allocation", "machine-invariant", "never",
                      "temporal 意圖欄（AIR-240，選填——在場則七鍵全到）：頂層或 "
                      "per-work_unit；preferred_family（枚舉＝FAMILIES）／"
                      "planned_not_before（ISO 8601 帶時區）／on_unavailable（"
                      "delay｜fallback）／fallback_families（explicit-only）＋"
                      "provenance entitlement_snapshot_ref/hash/as_of——ref 相對 "
                      "plan 檔目錄、sha256 canonical 比對、as_of 非未來且與快照 "
                      "generated_at 一致、rows 非空非全 stale（missing/stale "
                      "provenance exit 2）。易爛真值禁令：閉集鎖定，quota 現值/"
                      "reset 時刻等欄禁入"),
            FieldSpec("budget_context", "machine-invariant", "always",
                      "預算 context——revert_exposure_cap（敞口帽，純數值有限 ≥0）＋"
                      "usage_cap（用量帽三態：有限數 ≥0＝具體帽、null＝未設、"
                      "\"unlimited\"＝無帽）分欄（AC#6）"),
            FieldSpec("terminal_semantics", "machine-invariant", "always",
                      "終態語義（D6）：on_budget_exhausted=budget-limited、raise_cap=human-action、settle_gate=human"),
            FieldSpec("plan_changes", "machine-invariant", "always",
                      "PLAN_CHANGES 修訂流（D4）：每筆須附 what＋diff 交驗收腿複核；初始為空列表", nullable=True),
            FieldSpec("acceptance_contract", "machine-invariant", "never",
                      "C5b acceptance contract 區塊（AIR-135.1.1）：{schema, card_id, source_card, "
                      "card_baseline?, ac_ids, predicates[], judgment_required[]}——producer＝"
                      "arc_goal_compile.py（卡 AC explicit verifier 的 deterministic 編譯）；"
                      "選填＝本弧 back-compat（135.1.2 wiring 收緊）；在場時深檢集合不變式四條"),
            FieldSpec("objective_notes", "llm-guidance", "never",
                      "計畫寫作約束（grok 借鑑 #7）：specify outcomes, not architecture；為最弱執行模型可讀而寫"),
        ),
    ),
    "dispatch-slice": ArtifactSpec(
        kind="dispatch-slice",
        schema_marker=SCHEMA_DISPATCH_SLICE,
        title="DispatchSlice——派工單（JIT runtime 欄）",
        ownership="D2：ArcPlan 衍生、marshal 於派工時 JIT 填 runtime 欄；缺 machine-invariant 欄禁派工（AC#1 對偶）",
        fields=(
            FieldSpec("schema", "machine-invariant", "always", "schema marker",
                      values=(SCHEMA_DISPATCH_SLICE,), noun="schema marker", plural="schema markers"),
            FieldSpec("slice_id", "machine-invariant", "always", "本 slice 身分"),
            FieldSpec("card_id", "machine-invariant", "always", "卡節點身分回指"),
            FieldSpec("card_baseline", "machine-invariant", "always", "card tree baseline SHA（承 plan）"),
            FieldSpec("plan_version", "machine-invariant", "always",
                      "回指 ArcPlan 版本號（AC#2）"),
            FieldSpec("plan_hash", "machine-invariant", "always", "回指 ArcPlan 內容 hash，hex 64 位"),
            FieldSpec("unit_id", "machine-invariant", "always",
                      "work unit 錨 card node id（AC#5：跨 plan recompile 穩定）"),
            FieldSpec("role", "machine-invariant", "always", "工作角色",
                      values=ROLES, noun="role", plural="roles"),
            FieldSpec("authority", "machine-invariant", "always", "執行權限（AC#6）",
                      values=AUTHORITIES, noun="authority", plural="authorities"),
            FieldSpec("capability_mode", "machine-invariant", "always",
                      "能力枚舉軸（grok 借鑑 #13：替代逐 tool 白名單）",
                      values=CAPABILITY_MODES, noun="capability mode", plural="capability modes"),
            FieldSpec("owning_wt", "machine-invariant", "always",
                      "owning WT identity：{path, branch}（AC#6；跨 worktree 正規化沿 AIR-141 basename 收斂）"),
            FieldSpec("read_set", "machine-invariant", "always",
                      "role-dependent read-set：{policy, pointers}（AC#2：same page ≠ same projection；review/verify/test=problem-contract-only、intent-review=chain-exclusion；pointers 選填＝S1 顯式決策：dispatch 當下無讀指針的 slice 合法（如 receipt-only 通知型），S2 覆核）"),
            FieldSpec("sink", "machine-invariant", "always",
                      "artifact 預期路徑或 receipt-only：{mode, path?}（AC#2；欄位語義 owner＝135.7）"),
            FieldSpec("receipt_sink", "machine-invariant", "never",
                      "slice 回執落點（N6：muse 審查腿——回執欄位集有 schema、落點無欄可指）；"
                      "選填不進 required 集；未填＝慣例路徑 <wt>/.agent-tmp/<卡id>/<slice-id>-receipt.md"),
            FieldSpec("accept", "machine-invariant", "conditional",
                      "accept 機驗：{predicate, anchors}——sink 為 artifact 時必帶（預設 exists+readable+nonempty；terminal≠complete）"),
            FieldSpec("budget_context", "machine-invariant", "always",
                      "超支即停機械判準（AC#6）：revert_remaining（純數值有限 ≥0）＋"
                      "slice_budget（三態：有限數 ≥0＝具體帽、null＝未設、"
                      "\"unlimited\"＝無帽）＋debit_events 指針"),
            FieldSpec("terminal_semantics", "machine-invariant", "always", "終態語義（D6，承 plan）"),
            FieldSpec("carrier", "machine-invariant", "always", "承載載體（如 zcode-agent／bridge job）"),
            FieldSpec("collection_mode", "machine-invariant", "always",
                      "liveness/collection 模式（AC#6：欄位由 DispatchSlice 產出、135.7 台帳消費，禁兩處各自定義）",
                      values=COLLECTION_MODES, noun="collection mode", plural="collection modes"),
            FieldSpec("dispatch_id", "machine-invariant", "dispatch",
                      "派工 id（JIT；135.7 liveness 六欄表）"),
            FieldSpec("family", "machine-invariant", "dispatch",
                      "跨家族欄（D8 留形狀）；值由 resolver 於呼叫面填（D5）",
                      values=FAMILIES, noun="family", plural="families"),
            FieldSpec("model", "machine-invariant", "dispatch",
                      "model binding（D5：schema 留欄、resolver 填值、禁進模型呼叫面）"),
            FieldSpec("binding", "machine-invariant", "dispatch",
                      "binding 註記（preset 鎖設定層；D5）"),
            FieldSpec("ledger", "machine-invariant", "dispatch",
                      "帳本歸屬欄（D8；如 .delegate-bridge/jobs.json——計量歸 135.7）"),
            FieldSpec("commit_delegation", "machine-invariant", "always",
                      "commit 委任範圍（AC#6：僅本 repo 審查通過弧、跨 repo 寫恆停；settle 尾人類 gate 見 terminal_semantics.settle_gate）",
                      values=COMMIT_DELEGATIONS, noun="commit delegation", plural="commit delegations"),
            FieldSpec("preferred_family", "machine-invariant", "never",
                      "temporal 意圖 carry-through（AIR-240，選填）：計畫偏好 family"
                      "——值歸 resolver 於派工當下重驗 availability，schema 留欄",
                      values=FAMILIES, noun="preferred family",
                      plural="preferred families"),
            FieldSpec("on_unavailable", "machine-invariant", "never",
                      "temporal 意圖 carry-through（AIR-240，選填）：preferred family "
                      "不可用時的 policy——delay（等窗）或 fallback（限顯式 "
                      "fallback_families）",
                      values=TEMPORAL_ON_UNAVAILABLE, noun="on_unavailable policy",
                      plural="on_unavailable policies"),
            FieldSpec("fallback_families", "machine-invariant", "never",
                      "temporal 意圖 carry-through（AIR-240，選填）：explicit fallback "
                      "家族集合——explicit-only 契約（禁 resolver 製造跨家族 "
                      "fallback；禁含 preferred_family、禁與 delay 並存）"),
            FieldSpec("prompt_material", "llm-guidance", "never",
                      "任務敘述材料（D3：LLM guidance；禁入 machine-invariant 欄）"),
            FieldSpec("guidance", "llm-guidance", "never", "方法論指針（skills／文檔 pointers）"),
        ),
    ),
    "receipt": ArtifactSpec(
        kind="receipt",
        schema_marker=SCHEMA_SLICE_RECEIPT,
        title="receipt——派工回執（worker 寫、marshal 驗）",
        ownership="D2/D7：worker 寫、marshal 驗；欄位集沿用 CollectionReceipt＋plan 版本回指；terminal≠complete",
        fields=(
            FieldSpec("schema", "machine-invariant", "always", "schema marker",
                      values=(SCHEMA_SLICE_RECEIPT,), noun="schema marker", plural="schema markers"),
            FieldSpec("slice_id", "machine-invariant", "always", "回指 DispatchSlice"),
            FieldSpec("card_id", "machine-invariant", "always", "卡節點身分回指"),
            FieldSpec("unit_id", "machine-invariant", "always", "work unit 錨點回指"),
            FieldSpec("plan_version", "machine-invariant", "always", "plan 版本回指（D7）"),
            FieldSpec("plan_hash", "machine-invariant", "always", "plan 內容 hash 回指（D7），hex 64 位"),
            FieldSpec("job_id", "machine-invariant", "always", "bridge/spawn job id（帳本回指）"),
            FieldSpec("family", "machine-invariant", "always", "家族（D8）",
                      values=FAMILIES, noun="family", plural="families"),
            FieldSpec("status", "machine-invariant", "always",
                      "終態（D6）：completed 須配 delivery.verdict=delivered/manual-anchor（terminal≠complete）",
                      values=TERMINALS, noun="status", plural="terminals"),
            FieldSpec("delivery", "machine-invariant", "always",
                      "CollectionReceipt delivery 欄位集（D7 沿用）：mode/sink/l1_present/l2_anchor/anchor_hits/verdict"),
            FieldSpec("bounded_receipt_projection", "machine-invariant", "always",
                      "bounded receipt：final_text_non_empty（bridge_waiter 慣例投影）"),
            FieldSpec("intent_review", "machine-invariant", "never",
                      "Intent Review 驗收腿回寫面（S3/135.3 AC#7）：{verdict, leg, read_set_exclusion}"
                      "——verdict 枚舉 GO／GO-WITH-FIXES／NO-GO、leg＝審查腿身份、read_set_exclusion＝"
                      "chain-exclusion 自述；選填（required_at=never，同 receipt_sink N6 慣例）＝"
                      "閘外小弧自報為足，閘內獨立腿缺失＝exit Align 未過關"),
            FieldSpec("plan_hash_source", "machine-invariant", "never",
                      "被 hash 的來源檔指針（muse N-2：receipt 只存 hash 不存源——"
                      "ad-hoc 慣例＝brief 檔 path；正式＝ArcPlan 檔 path）"),
            FieldSpec("top_findings", "llm-guidance", "never", "語義欄——判定歸 caller（bridge_waiter 慣例）"),
            FieldSpec("blockers", "llm-guidance", "never", "阻礙清單"),
            FieldSpec("unverified", "llm-guidance", "never", "未驗面誠實申報（Fail Loud）"),
            FieldSpec("pending_human_decision", "llm-guidance", "never", "待人類裁決項（grok blocking 分類借鑑 #22）"),
        ),
    ),
}


# ---------------------------------------------------------------------------
# hash（AC#2：決定性內容 hash，禁 process-salted）
# ---------------------------------------------------------------------------


def canonical_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def plan_content_hash(plan: dict) -> str:
    """sha256 of canonical JSON（排除 plan_hash 自身——self-hash exclusion）。"""
    payload = {k: v for k, v in plan.items() if k != "plan_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 校驗主體
# ---------------------------------------------------------------------------


def _is_num(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _present_nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _require_object(label: str, value: object, kind: str, errors: list[str]) -> None:
    """dict 型 machine-invariant 欄的型別 guard——非 dict 即歧義值，fail-loud。"""
    if value is not None and not isinstance(value, dict):
        errors.append(
            f"`{label}` must be an object for {kind}, got {type(value).__name__}"
        )


def _require_list(label: str, value: object, kind: str, errors: list[str]) -> None:
    """list 型 machine-invariant 欄的型別 guard——非 list 即歧義值，fail-loud（muse N1）。"""
    if value is not None and not isinstance(value, list):
        errors.append(
            f"`{label}` must be a list for {kind}, got {type(value).__name__}"
        )


def _required_names(art: ArtifactSpec, stage: str) -> list[str]:
    return [
        f.name
        for f in art.fields
        if f.kind == "machine-invariant" and f.required_at in ("always", stage)
    ]


def _unknown_enum(f: FieldSpec, value: object, kind: str) -> str:
    noun = f.noun or f.name
    plural = f.plural or f"{noun}s"
    return (
        f"Unknown {noun} `{value}` for {kind}. "
        f"Available {plural}: {', '.join(f.values or ())}"
    )


def _check_budget_num(
    field_path: str, value: object, kind: str, errors: list[str]
) -> None:
    """比較式驗證 gate：非有限值 fail-closed（codex 預算先例：非有限值 Fatal）。"""
    if not _is_num(value):
        errors.append(
            f"Budget field `{field_path}` must be a number for {kind}, "
            f"got {type(value).__name__}"
        )
    elif not math.isfinite(float(value)):
        errors.append(
            f"Budget field `{field_path}` must be finite for {kind}, got {value} "
            f"— 非有限值 fail-closed（NaN 比較恆 False，禁 fail-open）"
        )
    elif not float(value) >= 0:
        errors.append(
            f"Budget field `{field_path}` must be >= 0 for {kind}, got {value}"
        )


_BUDGET_CAP_AVAILABLE = (
    'Available cap values: a finite number >= 0, null (unset), "unlimited"'
)


def _check_budget_cap(
    field_path: str,
    value: object,
    kind: str,
    errors: list[str],
    *,
    present: bool,
) -> None:
    """cap 欄三態（晨間合議定案——0-佔位同值異義防再犯）：有限數（≥0）＝具體帽
    （0＝零自治）、null（key 在場）＝未設（消費端自行判讀，不當無帽用）、
    "unlimited"＝無帽（decision-5「無額度帽」政策語義的顯式形）；其他型別/值或
    key 缺席＝fail-loud 列可用值。"""
    if not present:
        errors.append(
            f"Budget field `{field_path}` missing for {kind} — "
            f"cap 態須顯式（禁 key 缺席歧義）. {_BUDGET_CAP_AVAILABLE}"
        )
        return
    if value is None:
        return  # 未設——消費端自行判讀；不當無帽用
    if isinstance(value, str) and value == "unlimited":
        return  # 無帽——decision-5 政策語義的顯式形
    if not _is_num(value):  # str 其他值／bool／list 等皆此路
        errors.append(
            f"Unknown budget cap `{value}` for {kind} field `{field_path}`. "
            f"{_BUDGET_CAP_AVAILABLE}"
        )
        return
    if not math.isfinite(float(value)):
        errors.append(
            f"Budget field `{field_path}` must be finite for {kind}, got {value} "
            f"— 非有限值 fail-closed（NaN 比較恆 False，禁 fail-open）"
        )
        return
    if not float(value) >= 0:
        errors.append(
            f"Budget field `{field_path}` must be >= 0 for {kind}, got {value}"
        )


def _check_terminal_semantics(
    label: str, value: object, kind: str, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        errors.append(
            f"`{label}` must be an object for {kind}, got {type(value).__name__}"
        )
        return
    for key, expected in TERMINAL_SEMANTICS_FIXED.items():
        if value.get(key) != expected:
            errors.append(
                f"`{label}.{key}` must be `{expected}` for {kind} "
                f"（D6 終態語義）, got `{value.get(key)}`"
            )


def _check_arc_spec(
    data: dict, stage: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    baseline = data.get("card_baseline")
    if baseline is not None and not BASELINE_RE.match(str(baseline)):
        errors.append(
            f"Invalid card_baseline `{baseline}` for arc-spec — "
            f"需 hex 7-40 位（card tree baseline SHA）"
        )


def _check_acceptance_contract(
    contract: dict, kind: str, errors: list[str]
) -> None:
    """C5b acceptance_contract 區塊深檢（AIR-135.1.1）——欄位契約＋集合不變式
    四條（ac_ids 承載 AC 全集，故可在無卡環境機驗）。producer 單一源＝
    arc_goal_compile.py；本檔只擋形狀與集合違約，不重編譯。"""
    label = "acceptance_contract"
    if contract.get("schema") != ACCEPTANCE_CONTRACT_SCHEMA:
        errors.append(
            f"Unknown schema marker `{contract.get('schema')}` for {kind}.{label}. "
            f"Available schema markers: {ACCEPTANCE_CONTRACT_SCHEMA}"
        )
    for key in ("card_id", "source_card"):
        if not _present_nonempty(contract.get(key)):
            errors.append(f"`{label}.{key}` 不得為空 for {kind}")

    ac_ids = contract.get("ac_ids")
    if not isinstance(ac_ids, list) or not ac_ids:
        errors.append(
            f"`{label}.ac_ids` must be a non-empty list for {kind} — "
            f"AC 全集承載（集合不變式的輸入對照面）"
        )
        ac_ids = None
    elif not all(isinstance(a, str) and a.strip() for a in ac_ids):
        errors.append(f"`{label}.ac_ids` must be non-empty strings for {kind}")
        ac_ids = None
    elif len(set(ac_ids)) != len(ac_ids):
        dupes = sorted({a for a in ac_ids if ac_ids.count(a) > 1})
        errors.append(
            f"Duplicate ac_id {dupes} in `{label}.ac_ids` for {kind} — "
            f"AC 身分歧義（fail-loud）"
        )

    predicates = contract.get("predicates")
    _require_list(f"{label}.predicates", predicates, kind, errors)
    pred_ids: list[str] = []
    if isinstance(predicates, list):
        for i, p in enumerate(predicates):
            if not isinstance(p, dict):
                errors.append(
                    f"{label}.predicates[{i}] must be an object for {kind}, "
                    f"got {type(p).__name__}"
                )
                continue
            ac_id = p.get("ac_id")
            if not _present_nonempty(ac_id) or not isinstance(ac_id, str):
                errors.append(
                    f"{label}.predicates[{i}].ac_id 不得為空 for {kind}"
                )
                continue
            pred_ids.append(ac_id)
            satisfied = p.get("satisfied")
            if not isinstance(satisfied, bool):
                errors.append(
                    f"{label}.predicates[{i}].satisfied must be a boolean "
                    f"for {kind}, got {type(satisfied).__name__}"
                )
                satisfied = None

            p_kind = p.get("kind")
            if p_kind is not None and p_kind not in PREDICATE_KINDS:
                errors.append(_unknown_enum(
                    FieldSpec("kind", "machine-invariant", "always", "",
                              values=PREDICATE_KINDS, noun="predicate kind",
                              plural="predicate kinds"),
                    p_kind, f"{kind}.{label}",
                ))
            if satisfied is False and p_kind not in PREDICATE_KINDS:
                errors.append(
                    f"`{label}.predicates[{i}].kind` must be one of "
                    f"{', '.join(PREDICATE_KINDS)} for open predicates "
                    f"(satisfied=false) in {kind} — 無 verifier kind 的 open "
                    f"predicate＝無機驗面的 goal（禁）"
                )

            verifier = p.get("verifier")
            expected = p.get("expected")
            if p_kind == "command_expected":
                for key, val in (("verifier", verifier), ("expected", expected)):
                    if not _present_nonempty(val):
                        errors.append(
                            f"{label}.predicates[{i}].{key} 不得為空 for "
                            f"kind=command_expected in {kind}"
                        )
            elif verifier is not None or expected is not None:
                errors.append(
                    f"{label}.predicates[{i}].verifier/expected 僅定義於 "
                    f"kind=command_expected（v1）——kind=`{p_kind}` 帶之即 "
                    f"雙 authoritative 形狀（fail-loud）"
                )
            if verifier is None and satisfied is False:
                errors.append(
                    f"{label}.predicates[{i}] 無 verifier 且 satisfied=false "
                    f"for {kind} — 無機驗面的 open predicate（靜默 goal 化，禁；"
                    f"no-verifier AC 應在 judgment_required）"
                )

            baseline_at = p.get("satisfied_at_baseline")
            if satisfied is True:
                if not (isinstance(baseline_at, str) and BASELINE_RE.match(baseline_at)):
                    errors.append(
                        f"{label}.predicates[{i}].satisfied_at_baseline 需 hex "
                        f"7-40 位 for satisfied predicate in {kind} — 已滿足須帶 "
                        f"baseline 身份（重編譯不丟已完成證據）"
                    )
            elif baseline_at is not None:
                errors.append(
                    f"{label}.predicates[{i}].satisfied_at_baseline 須為 null "
                    f"for open predicate in {kind}, got `{baseline_at}`"
                )

    judgment = contract.get("judgment_required")
    _require_list(f"{label}.judgment_required", judgment, kind, errors)
    jud_ids: list[str] = []
    if isinstance(judgment, list):
        for i, j in enumerate(judgment):
            if not isinstance(j, dict):
                errors.append(
                    f"{label}.judgment_required[{i}] must be an object for {kind}, "
                    f"got {type(j).__name__}"
                )
                continue
            ac_id = j.get("ac_id")
            if not _present_nonempty(ac_id) or not isinstance(ac_id, str):
                errors.append(
                    f"{label}.judgment_required[{i}].ac_id 不得為空 for {kind}"
                )
                continue
            jud_ids.append(ac_id)
            reason = j.get("reason")
            if reason not in JUDGMENT_REASONS:
                errors.append(_unknown_enum(
                    FieldSpec("reason", "machine-invariant", "always", "",
                              values=JUDGMENT_REASONS, noun="judgment reason",
                              plural="judgment reasons"),
                    reason, f"{kind}.{label}",
                ))

    # 集合不變式四條（ac_ids 在場才可機驗——輸入對照面）
    if ac_ids is not None:
        if len(set(pred_ids)) != len(pred_ids):
            errors.append(
                f"Duplicate ac_id in `{label}.predicates` for {kind} — "
                f"exactly-once 違約（fail-loud）"
            )
        if len(set(jud_ids)) != len(jud_ids):
            errors.append(
                f"Duplicate ac_id in `{label}.judgment_required` for {kind} — "
                f"exactly-once 違約（fail-loud）"
            )
        pred_set, jud_set, all_set = set(pred_ids), set(jud_ids), set(ac_ids)
        lost = sorted(all_set - pred_set - jud_set)
        if lost:
            errors.append(
                f"AC id {lost} missing from acceptance_contract for {kind} — "
                f"集合不變式 3（聯集=全部）：judgment_required 靜默丟失為本編譯器"
                f"最危險失效形（fail-loud）"
            )
        extra = sorted((pred_set | jud_set) - all_set)
        if extra:
            errors.append(
                f"AC id {extra} not covered by `{label}.ac_ids` for {kind} — "
                f"集合不變式 3 反向包含：predicate/judgment 帶 AC 全集之外的 "
                f"ac_id＝身分脫離輸入對照面（fail-loud）"
            )
        overlap = sorted(pred_set & jud_set)
        if overlap:
            errors.append(
                f"AC id {overlap} in both predicates and judgment_required for "
                f"{kind} — 集合不變式 4（交集=空；雙重歸類）"
            )


def _check_contract_back_refs(
    plan: dict, contract: dict, kind: str, errors: list[str]
) -> None:
    """plan ↔ acceptance_contract 跨塊回指（fresh F3）——card_id／card_baseline
    兩側皆在場時須一致；不一致＝契約歸屬卡與 plan 歸屬卡分歧（fail-loud）。
    card_baseline 為選填欄（無 baseline 編譯合法），兩側在場才比。"""
    plan_id = plan.get("card_id")
    contract_id = contract.get("card_id")
    if (
        _present_nonempty(plan_id)
        and _present_nonempty(contract_id)
        and plan_id != contract_id
    ):
        errors.append(
            f"acceptance_contract.card_id `{contract_id}` != plan card_id "
            f"`{plan_id}` for {kind} — 跨塊回指不一致（契約歸屬卡與 plan 歸屬卡"
            f"分歧；雙 authoritative，fail-loud）"
        )
    plan_baseline = plan.get("card_baseline")
    contract_baseline = contract.get("card_baseline")
    if (
        _present_nonempty(plan_baseline)
        and _present_nonempty(contract_baseline)
        and plan_baseline != contract_baseline
    ):
        errors.append(
            f"acceptance_contract.card_baseline `{contract_baseline}` != plan "
            f"card_baseline `{plan_baseline}` for {kind} — 跨塊回指不一致"
            f"（編譯 baseline 與 plan baseline 分歧；fail-loud）"
        )


def _coverage_enum_field(name: str, values: tuple[str, ...], noun: str) -> FieldSpec:
    return FieldSpec(name, "machine-invariant", "always", "", values=values, noun=noun,
                     plural=f"{noun}s")


def _check_closure_coverage(
    data: dict, stage: str, kind: str, errors: list[str]
) -> None:
    """收線鏈 coverage 硬閘（AIR-235）——只在 compile stage（plan 定版時驗；
    dispatch 不重驗，slice 是 per-unit 物）。缺站逐行列出＋文案列可用站別；
    chain_waiver 顯式豁免（reason 必填——顯式勝於歧義）。"""
    if stage != "compile":
        return

    # waiver 先行——豁免集決定 coverage 必含面
    waived: set[str] = set()
    waiver = data.get("chain_waiver")
    if waiver is not None:
        if not isinstance(waiver, dict):
            errors.append(
                f"`chain_waiver` must be an object for {kind}, "
                f"got {type(waiver).__name__}"
            )
        else:
            stations = waiver.get("stations")
            _require_list("chain_waiver.stations", stations, kind, errors)
            if isinstance(stations, list):
                for s in stations:
                    if s not in COVERAGE_STATIONS:
                        errors.append(_unknown_enum(
                            _coverage_enum_field("station", COVERAGE_STATIONS,
                                                 "coverage station"),
                            s, f"{kind}.chain_waiver",
                        ))
                    else:
                        waived.add(s)
            reason = waiver.get("reason")
            if not (isinstance(reason, str) and reason.strip()):
                errors.append(
                    f"`chain_waiver.reason` 不得為空 for {kind} — waiver 顯式勝於"
                    f"歧義（reason 空字串/缺席＝exit 2）"
                )

    coverage = data.get("closure_coverage")
    _require_list("closure_coverage", coverage, kind, errors)
    covered: set[str] = set()
    if isinstance(coverage, list):
        work_units = data.get("work_units")
        unit_ids = {
            wu["unit_id"]
            for wu in (work_units or [])
            if isinstance(wu, dict)
            and isinstance(wu.get("unit_id"), str)
            and wu["unit_id"].strip()
        }
        for i, entry in enumerate(coverage):
            if not isinstance(entry, dict):
                errors.append(
                    f"closure_coverage[{i}] must be an object for {kind}, "
                    f"got {type(entry).__name__}"
                )
                continue
            station = entry.get("station")
            if station not in COVERAGE_STATIONS:
                errors.append(_unknown_enum(
                    _coverage_enum_field("station", COVERAGE_STATIONS,
                                         "coverage station"),
                    station, f"{kind}.closure_coverage",
                ))
                continue
            if station in covered:
                errors.append(
                    f"Duplicate coverage station `{station}` in closure_coverage "
                    f"for {kind} — 每站恰一 entry（雙 authoritative，fail-loud）"
                )
            covered.add(station)
            unit_ref = entry.get("unit_ref")
            if not (isinstance(unit_ref, str) and unit_ref.strip()):
                errors.append(
                    f"`closure_coverage[{i}].unit_ref` 不得為空 for {kind}"
                )
            elif unit_ref not in unit_ids:
                # R1（codex F1）：無 `unit_ids and` 前置——unit_ids 空集
                # （如 work_units=[{}]）時 ghost ref 一律報，禁 fail-open。
                available_ids = (
                    ", ".join(sorted(unit_ids))
                    if unit_ids
                    else "<none — work_units 無合法 unit_id>"
                )
                errors.append(
                    f"closure_coverage[{i}].unit_ref `{unit_ref}` not found in "
                    f"work_units for {kind} — unit_ref 須回指在場 unit_id. "
                    f"Available unit ids: {available_ids}"
                )
            owner = entry.get("owner")
            if owner not in COVERAGE_OWNERS:
                errors.append(_unknown_enum(
                    _coverage_enum_field("owner", COVERAGE_OWNERS, "owner"),
                    owner, f"{kind}.closure_coverage",
                ))
            else:
                fixed = STATION_OWNER_FIXED.get(station)
                if fixed is not None and owner != fixed:
                    errors.append(
                        f"closure_coverage[{i}] station `{station}` requires "
                        f"owner=`{fixed}` for {kind}, got `{owner}` — owner 站別"
                        f"一致性（judge/landing/settle 恆 main-session、review "
                        f"恆 dispatch）"
                    )
            gate = entry.get("gate")
            if gate not in COVERAGE_GATES:
                errors.append(_unknown_enum(
                    _coverage_enum_field("gate", COVERAGE_GATES, "gate"),
                    gate, f"{kind}.closure_coverage",
                ))

    for station in sorted(waived & covered):
        # R5（fresh F1）：豁免與覆蓋不得同站雙頭——矛盾授權 fail-loud。
        errors.append(
            f"chain_waiver station `{station}` also covered in closure_coverage "
            f"for {kind} — 豁免與覆蓋不得同站雙頭（fail-loud）"
        )

    for station in COVERAGE_STATIONS:
        if station not in waived and station not in covered:
            errors.append(
                f"closure_coverage missing station `{station}` for {kind} — "
                f"收線鏈五站必含（waiver 站豁免；顯式 chain_waiver 須帶 reason）. "
                f"Available stations: {', '.join(COVERAGE_STATIONS)}"
            )


def _check_volatile_truth_keys(
    block: dict, label: str, kind: str, errors: list[str]
) -> None:
    """易爛真值黑名單掃描（AIR-240 R1——repair-1）——key 命中莖詞閉集即逐行
    error。禁令範圍＝temporal_allocation block 閉集＋本黑名單（掃頂層 plan 與
    work_units[i] sibling）；**非全 plan 白名單**——非 volatile 新 key 不攔
    （extension surface 開放）。"""
    for key in block:
        if any(stem in key for stem in VOLATILE_TRUTH_STEMS):
            errors.append(
                f"Volatile truth key `{key}` in {label} for {kind} — "
                f"易爛真值禁令（現值欄如 quota 數字/reset 時刻禁入 plan；ArcPlan "
                f"是穩定版控 artifact，現值幾小時即腐爛，唯一合法歸宿＝snapshot "
                f"引用）. Volatile key stems: {', '.join(VOLATILE_TRUTH_STEMS)}"
            )


def _parse_iso_utc(value: object) -> datetime | None:
    """ISO 8601 tz-aware 解析——naive（無時區）＝不合法（AIR-239 R4 同姿態：
    禁與 aware 值混比時 TypeError）。"""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt


def _temporal_enum_field(name: str, values: tuple[str, ...], noun: str) -> FieldSpec:
    return FieldSpec(name, "machine-invariant", "always", "", values=values,
                     noun=noun, plural=f"{noun}s")


def _check_temporal_intent(
    block: dict, prefix: str, kind: str, errors: list[str], *,
    check_enums: bool,
) -> None:
    """temporal 意圖欄共用深檢（AIR-240）——枚舉／ISO 形／fallback 集合＋矛盾
    policy 三條。prefix＝錯誤文案欄位路徑前綴（slice 頂層欄傳 ""；plan 區塊
    傳 "temporal_allocation" 或 "work_units[i].temporal_allocation"）。

    check_enums：plan 區塊（dict 欄——generic FieldSpec 枚舉迴圈不下降）傳
    True；slice 頂層欄已由 generic 迴圈枚舉檢查（values= 註冊）——傳 False
    禁雙重報錯。

    矛盾 policy 三條（各自逐行 fail-loud）：
    1. fallback_families 含 preferred_family＝同家 fallback（相異家族才叫 fallback）
    2. on_unavailable=fallback 而集合空/缺席＝explicit-only 違約（禁 resolver
       製造跨家族 fallback）
    3. on_unavailable=delay 而集合非空＝雙 authoritative policy
    """
    p = f"{prefix}." if prefix else ""
    # enum 錯誤的 kind context 帶欄位路徑——per-unit 區塊錯誤可定位到 unit
    ctx = f"{kind}.{prefix}" if prefix else kind

    preferred = block.get("preferred_family")
    if check_enums and preferred is not None and preferred not in FAMILIES:
        errors.append(_unknown_enum(
            _temporal_enum_field("preferred_family", FAMILIES, "preferred family"),
            preferred, ctx,
        ))

    planned_raw = block.get("planned_not_before")
    if planned_raw is not None and _parse_iso_utc(planned_raw) is None:
        errors.append(
            f"`{p}planned_not_before` 須為 ISO 8601 且帶時區 for {kind}, "
            f"got `{planned_raw}`（naive ISO＝不合法，禁與 aware 值混比）"
        )

    on_unavailable = block.get("on_unavailable")
    if (
        check_enums
        and on_unavailable is not None
        and on_unavailable not in TEMPORAL_ON_UNAVAILABLE
    ):
        errors.append(_unknown_enum(
            _temporal_enum_field(
                "on_unavailable", TEMPORAL_ON_UNAVAILABLE, "on_unavailable policy"
            ),
            on_unavailable, ctx,
        ))

    fallbacks = block.get("fallback_families")
    fallback_list: list[object] = []
    if fallbacks is not None:
        if not isinstance(fallbacks, list):
            errors.append(
                f"`{p}fallback_families` must be a list for {kind}, "
                f"got {type(fallbacks).__name__}"
            )
        else:
            fallback_list = fallbacks
            for j, fam in enumerate(fallbacks):
                if fam not in FAMILIES:
                    errors.append(_unknown_enum(
                        _temporal_enum_field(
                            f"fallback_families[{j}]", FAMILIES, "fallback family"
                        ),
                        fam, ctx,
                    ))
            dupes = sorted({f for f in fallbacks if fallbacks.count(f) > 1})
            if dupes:
                errors.append(
                    f"Duplicate fallback family {dupes} in `{p}fallback_families` "
                    f"for {kind} — 雙 authoritative（fail-loud）"
                )

    if isinstance(preferred, str) and preferred in fallback_list:
        errors.append(
            f"`{p}fallback_families` contains preferred_family `{preferred}` "
            f"for {kind} — fallback 與 preferred 同家＝矛盾 policy（fallback 須為"
            f"相異家族 explicit set；fail-loud）"
        )
    if on_unavailable == "fallback" and not fallback_list:
        errors.append(
            f"`{prefix or 'slice'}` on_unavailable=`fallback` 須帶非空 "
            f"fallback_families for {kind} — explicit-only 契約：fallback 集須"
            f"顯式列舉（禁 resolver 製造跨家族 fallback；fail-loud）"
        )
    if on_unavailable == "delay" and fallback_list:
        errors.append(
            f"`{p}fallback_families` 在場但 on_unavailable=`delay` for {kind} — "
            f"雙 authoritative policy（delay 與 fallback 集矛盾；fail-loud）"
        )


def _load_snapshot_payload(
    path: Path, label: str, kind: str, errors: list[str]
) -> dict | None:
    """planning snapshot 檔載入——缺席／壞 json／schema marker 不符逐行報。"""
    if not path.is_file():
        errors.append(
            f"`{label}.entitlement_snapshot_ref` 指向的 snapshot 檔不存在: {path} "
            f"for {kind} — missing provenance（planning evidence 缺場＝禁定版，"
            f"fail-loud）"
        )
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            f"`{label}.entitlement_snapshot_ref` snapshot 檔不可讀或壞 json: "
            f"{path}（{exc}）for {kind}"
        )
        return None
    if not isinstance(payload, dict) or payload.get("schema") != TEMPORAL_SNAPSHOT_SCHEMA:
        errors.append(
            f"snapshot schema marker mismatch at {path} for {kind} — 須為 "
            f"`{TEMPORAL_SNAPSHOT_SCHEMA}`（planning evidence 契約面；producer＝"
            f"scripts/entitlement_window_snapshot.py）"
        )
        return None
    return payload


def _check_temporal_provenance(
    block: dict, label: str, kind: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    """provenance 三鍵機驗（AIR-240 compile gate）——「規劃當下有 fresh
    evidence」的機械面：ref 檔存在＋sha256 canonical 比對＋as_of 非未來且與
    快照 generated_at 一致＋rows 非空且非全 stale。stale 閾值 ownership 在
    producer（AIR-239 單一時鐘 R2）——本函數消費 rows[].freshness 標籤。"""
    ref = block.get("entitlement_snapshot_ref")
    if not (isinstance(ref, str) and ref.strip()):
        return  # 缺欄已由全鍵必到檢報過——此處不重複
    snap_path = Path(ref)
    if not snap_path.is_absolute():
        snap_path = base_dir / snap_path
    payload = _load_snapshot_payload(snap_path, label, kind, errors)
    if payload is None:
        return

    recorded_hash = block.get("entitlement_snapshot_hash")
    if isinstance(recorded_hash, str) and HEX64_RE.match(recorded_hash):
        recomputed = hashlib.sha256(
            canonical_json(payload).encode("utf-8")
        ).hexdigest()
        if recorded_hash != recomputed:
            errors.append(
                f"`{label}.entitlement_snapshot_hash` mismatch for {kind}: "
                f"recorded `{recorded_hash}`, recomputed `{recomputed}` — "
                f"planning evidence 內容已漂移（provenance 比對；fail-loud）"
            )
    elif recorded_hash is not None:
        errors.append(
            f"Invalid `{label}.entitlement_snapshot_hash` `{recorded_hash}` for "
            f"{kind} — 需 hex 64 位（sha256 canonical）"
        )

    as_of_raw = block.get("entitlement_snapshot_as_of")
    as_of = _parse_iso_utc(as_of_raw)
    if as_of_raw is not None and as_of is None:
        errors.append(
            f"`{label}.entitlement_snapshot_as_of` 須為 ISO 8601 且帶時區 for "
            f"{kind}, got `{as_of_raw}`（naive ISO＝不合法）"
        )
    elif as_of is not None:
        if as_of > now:
            errors.append(
                f"`{label}.entitlement_snapshot_as_of` 為未來時間戳 for {kind}: "
                f"`{as_of_raw}` — 未來非新（fail-loud；availability_snapshot F4 "
                f"同姿態）"
            )
        generated_raw = payload.get("generated_at")
        generated = _parse_iso_utc(generated_raw)
        if generated is None:
            # R2（repair-1）：generated_at 存在＋可解析＋tz-aware＝prerequisite
            # ——缺/壞即 fail-loud，禁靜默跳過 equality（原實作 fail-open）
            errors.append(
                f"snapshot `generated_at` 缺席或非合法 tz-aware ISO for {kind}: "
                f"`{generated_raw}` — provenance 綁定 prerequisite（as_of 主張須"
                f"錨定快照自身時戳；錨點缺席＝綁定不可機驗，fail-loud）"
            )
        elif as_of != generated:
            errors.append(
                f"`{label}.entitlement_snapshot_as_of` `{as_of_raw}` 與快照 "
                f"generated_at `{generated_raw}` 不一致 for {kind} "
                f"— provenance 綁定：as_of 主張須錨定快照自身時戳（fail-loud）"
            )

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append(
            f"snapshot at `{label}.entitlement_snapshot_ref` has zero/missing "
            f"rows for {kind} — 零 planning evidence（快照在場也禁；fail-loud）"
        )
        return
    malformed = [i for i, r in enumerate(rows) if not isinstance(r, dict)]
    if malformed:
        errors.append(
            f"snapshot rows malformed at indices {malformed} for {kind} — rows[] "
            f"須為 object（禁靜默跳過；fail-loud）"
        )
        return
    bad_freshness = [
        i for i, r in enumerate(rows) if r.get("freshness") not in ("fresh", "stale")
    ]
    if bad_freshness:
        errors.append(
            f"snapshot rows freshness 標籤不合法 at indices {bad_freshness} for "
            f"{kind} — 須為 fresh/stale（producer 契約面；fail-loud）"
        )
        return
    if all(r["freshness"] == "stale" for r in rows):
        errors.append(
            f"stale provenance for {kind}: `{label}.entitlement_snapshot_ref` 全 "
            f"rows freshness=stale — 零 fresh evidence 可規劃（missing/stale "
            f"provenance exit 2；閾值 ownership 在 producer 26h/3d——重出快照"
            f"而非調 plan）"
        )


def _check_temporal_allocation(
    block: object, label: str, kind: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    """temporal_allocation 區塊深檢（AIR-240）——在場則七鍵全到＋閉集鎖定
    （易爛真值禁令）＋意圖深檢＋provenance 機驗。"""
    if not isinstance(block, dict):
        errors.append(
            f"`{label}` must be an object for {kind}, got {type(block).__name__}"
        )
        return
    unknown = [k for k in block if k not in TEMPORAL_ALLOCATION_KEYS]
    if unknown:
        errors.append(
            f"Unknown temporal key(s) {', '.join(sorted(unknown))} in `{label}` "
            f"for {kind} — 易爛真值禁令（禁令範圍＝temporal_allocation block "
            f"閉集＋全 plan volatile-key 黑名單；非全 plan 白名單——現值欄如 "
            f"quota 數字/reset 時刻禁入 plan，唯一合法歸宿＝snapshot 引用）. "
            f"Known temporal keys: {', '.join(TEMPORAL_ALLOCATION_KEYS)}"
        )
    for key in TEMPORAL_ALLOCATION_KEYS:
        value = block.get(key)
        present = key in block and value is not None
        if key == "fallback_families" and present and isinstance(value, list):
            pass  # 空集合＝顯式「無 fallback」——delay policy 的合法值
        elif not present or not _present_nonempty(value):
            errors.append(
                f"`{label}.{key}` 不得缺席或為空 for {kind} — temporal 意圖欄在場"
                f"即全鍵必到（禁部分宣告歧義；provenance 三鍵齊備才可機驗 "
                f"planning evidence）"
            )
    _check_temporal_intent(block, label, kind, errors, check_enums=True)
    _check_temporal_provenance(
        block, label, kind, errors, now=now, base_dir=base_dir
    )


def _check_arc_plan(
    data: dict, stage: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    kind = "arc-plan"
    # R1（repair-1）：全 plan volatile-key 黑名單——頂層＋work_units sibling
    _check_volatile_truth_keys(data, "plan top level", kind, errors)
    version = data.get("version")
    version_ok = False
    if version is not None:
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            errors.append(
                f"Invalid version `{version}` for {kind} — 需正整數（單調版本號）"
            )
        else:
            version_ok = True

    supersedes = data.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes, int) or isinstance(supersedes, bool) or supersedes < 1:
            errors.append(
                f"Invalid supersedes `{supersedes}` for {kind} — 需正整數或 null"
            )
        elif version_ok and supersedes >= version:
            errors.append(
                f"Invalid supersedes `{supersedes}` for {kind} version `{version}` — "
                f"須小於自身版本（版本單調性）"
            )

    recorded = data.get("plan_hash")
    if isinstance(recorded, str) and HEX64_RE.match(recorded):
        recomputed = plan_content_hash(data)
        if recorded != recomputed:
            errors.append(
                f"Plan hash mismatch for {kind} version `{data.get('version')}`: "
                f"recorded `{recorded}`, recomputed `{recomputed}` — "
                f"ArcPlan 封存後內容已漂移（禁原地改；修訂走 plan_changes 或 recompile 新版本）"
            )
    elif recorded is not None:
        errors.append(
            f"Invalid plan_hash `{recorded}` for {kind} — 需 hex 64 位（sha256）"
        )

    _require_list("work_units", data.get("work_units"), kind, errors)
    work_units = data.get("work_units")
    if isinstance(work_units, list):
        seen: set[str] = set()
        for i, wu in enumerate(work_units):
            if not isinstance(wu, dict):
                errors.append(
                    f"work_units[{i}] must be an object for {kind}, "
                    f"got {type(wu).__name__}"
                )
                continue
            unit_id = wu.get("unit_id")
            if isinstance(unit_id, str) and unit_id.strip():
                if unit_id in seen:
                    errors.append(
                        f"Duplicate work unit id `{unit_id}` in {kind} — "
                        f"work unit 身分歧義（雙 authoritative，fail-loud）"
                    )
                seen.add(unit_id)
            role = wu.get("role")
            if role is not None and role not in ROLES:
                errors.append(_unknown_enum(
                    FieldSpec("role", "machine-invariant", "always", "",
                              values=ROLES, noun="role", plural="roles"),
                    role, kind,
                ))
            for key in ("unit_id", "title"):
                if key not in wu or not _present_nonempty(wu[key]):
                    errors.append(
                        f"work_units[{i}].{key} 不得缺席或為空 for {kind}"
                    )
            phase = wu.get("phase")
            if not _present_nonempty(phase):
                errors.append(
                    f"work_units[{i}].phase 不得缺席或為空 for {kind}. "
                    f"Available phases: {', '.join(PHASES)}"
                )
            elif phase not in PHASES:
                errors.append(_unknown_enum(
                    FieldSpec("phase", "machine-invariant", "always", "",
                              values=PHASES, noun="phase", plural="phases"),
                    phase, kind,
                ))
            if "depends_on" in wu and not isinstance(wu["depends_on"], list):
                errors.append(
                    f"work_units[{i}].depends_on must be a list for {kind}"
                )
            _check_volatile_truth_keys(wu, f"work_units[{i}]", kind, errors)
            if "temporal_allocation" in wu:
                # AIR-240：work-unit 級 temporal 意圖——與頂層區塊同深檢
                _check_temporal_allocation(
                    wu["temporal_allocation"],
                    f"work_units[{i}].temporal_allocation",
                    kind,
                    errors,
                    now=now,
                    base_dir=base_dir,
                )

    _require_object("budget_context", data.get("budget_context"), kind, errors)
    budget = data.get("budget_context")
    if isinstance(budget, dict):
        _check_budget_num(
            "budget_context.revert_exposure_cap",
            budget.get("revert_exposure_cap"),
            kind,
            errors,
        )
        _check_budget_cap(
            "budget_context.usage_cap",
            budget.get("usage_cap"),
            kind,
            errors,
            present="usage_cap" in budget,
        )

    _check_terminal_semantics("terminal_semantics", data.get("terminal_semantics"), kind, errors)

    _require_list("plan_changes", data.get("plan_changes"), kind, errors)
    changes = data.get("plan_changes")
    if isinstance(changes, list):
        for i, ch in enumerate(changes):
            if not isinstance(ch, dict):
                errors.append(
                    f"plan_changes[{i}] must be an object for {kind}, "
                    f"got {type(ch).__name__}"
                )
                continue
            for key in ("what", "diff"):
                if not _present_nonempty(ch.get(key)):
                    errors.append(
                        f"plan_changes[{i}] 缺 `{key}` for {kind} — "
                        f"PLAN_CHANGES 修訂須附 what＋diff 交驗收腿複核（D4；"
                        f"弱化／刪除／自利條款本身即駁回理由）"
                    )

    _require_object(
        "acceptance_contract", data.get("acceptance_contract"), kind, errors
    )
    contract = data.get("acceptance_contract")
    if isinstance(contract, dict):
        _check_acceptance_contract(contract, kind, errors)
        _check_contract_back_refs(data, contract, kind, errors)

    _check_closure_coverage(data, stage, kind, errors)

    if "temporal_allocation" in data:
        # AIR-240：頂層 temporal 意圖欄（provenance 機驗不隨 stage 豁免——plan
        # 是凍結物，ref/hash/as_of 的有效性與驗證時點的 stage 無關）
        _check_temporal_allocation(
            data.get("temporal_allocation"),
            "temporal_allocation",
            kind,
            errors,
            now=now,
            base_dir=base_dir,
        )


def _check_dispatch_slice(
    data: dict, stage: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    kind = "dispatch-slice"
    slice_id = data.get("slice_id") or "<unnamed>"

    for label in ("owning_wt", "read_set", "sink", "budget_context"):
        _require_object(label, data.get(label), kind, errors)
    owning_wt = data.get("owning_wt")
    if isinstance(owning_wt, dict):
        for key in ("path", "branch"):
            if not _present_nonempty(owning_wt.get(key)):
                errors.append(
                    f"`owning_wt.{key}` 不得為空 for {kind}（owning WT identity；AC#6）"
                )

    plan_version = data.get("plan_version")
    if plan_version is not None and (
        not isinstance(plan_version, int) or isinstance(plan_version, bool) or plan_version < 1
    ):
        errors.append(
            f"Invalid plan_version `{plan_version}` for {kind} — 需正整數（回指 ArcPlan 版本）"
        )
    plan_hash = data.get("plan_hash")
    if plan_hash is not None and not (
        isinstance(plan_hash, str) and HEX64_RE.match(plan_hash)
    ):
        errors.append(
            f"Invalid plan_hash `{plan_hash}` for {kind} — 需 hex 64 位（回指 ArcPlan 內容 hash）"
        )

    authority = data.get("authority")
    capability = data.get("capability_mode")
    if authority == "writer" and capability == "ReadOnly":
        errors.append(
            f"Conflicting authority for {kind} `{slice_id}`: "
            f"authority=`writer` with capability_mode=`ReadOnly` — "
            f"雙 authoritative 寫入語義矛盾（fail-loud）"
        )

    role = data.get("role")
    read_set = data.get("read_set")
    if isinstance(read_set, dict) and role in ROLE_READ_SET:
        policy = read_set.get("policy")
        allowed = ROLE_READ_SET[role]
        if policy not in allowed:
            errors.append(
                f"Unknown read_set policy `{policy}` for role `{role}` in {kind}. "
                f"Allowed read_set policies for role {role}: {', '.join(allowed)}"
            )
        pointers = read_set.get("pointers")
        if "pointers" in read_set and (
            not isinstance(pointers, list)
            or not pointers
            or not all(isinstance(p, str) and p.strip() for p in pointers)
        ):
            errors.append(
                f"`read_set.pointers` must be a non-empty list of non-empty strings "
                f"for {kind}"
            )

    sink = data.get("sink")
    accept = data.get("accept")
    if isinstance(sink, dict):
        mode = sink.get("mode")
        path = sink.get("path")
        if mode is not None and mode not in ("artifact", "receipt-only"):
            errors.append(
                f"Unknown sink mode `{mode}` for {kind}. "
                f"Available sink modes: artifact, receipt-only"
            )
        if mode == "artifact" and not _present_nonempty(path):
            errors.append(
                f"`sink.path` 不得為空 for {kind} — mode=`artifact` 須帶 artifact 預期路徑"
            )
        if mode == "receipt-only" and path is not None:
            errors.append(
                f"Conflicting authoritative sink for {kind} `{slice_id}`: "
                f"mode=`receipt-only` plus path=`{path}` — "
                f"雙 authoritative sink（fail-loud；AC#1）"
            )
        if mode == "artifact" and accept is None:
            errors.append(
                "Missing machine-invariant field `accept` for "
                f"{kind}（sink 為 artifact 時必帶：predicate＋anchors 機驗面；terminal≠complete）. "
                f"Required machine-invariant fields: {', '.join(_required_names(ARTIFACTS[kind], stage))}"
            )
    if accept is not None:
        if not isinstance(accept, dict):
            errors.append(
                f"`accept` must be an object for {kind}, got {type(accept).__name__}"
            )
        else:
            if "predicate" in accept and not _present_nonempty(accept["predicate"]):
                errors.append(f"`accept.predicate` 不得為空 for {kind}")
            anchors = accept.get("anchors")
            if "anchors" in accept and (
                not isinstance(anchors, list)
                or not anchors
                or not all(isinstance(a, str) and a.strip() for a in anchors)
            ):
                errors.append(
                    f"`accept.anchors` must be a non-empty list of non-empty strings "
                    f"for {kind}（錨點 token 供 sink 機驗）"
                )

    budget = data.get("budget_context")
    if isinstance(budget, dict):
        _check_budget_num(
            "budget_context.revert_remaining",
            budget.get("revert_remaining"),
            kind,
            errors,
        )
        _check_budget_cap(
            "budget_context.slice_budget",
            budget.get("slice_budget"),
            kind,
            errors,
            present="slice_budget" in budget,
        )
        if "debit_events" in budget and not isinstance(budget["debit_events"], list):
            errors.append(
                f"`budget_context.debit_events` must be a list for {kind}（扣款事件指針）"
            )

    _check_terminal_semantics("terminal_semantics", data.get("terminal_semantics"), kind, errors)

    # AIR-240：temporal carry-through 形狀＋矛盾 policy（選填欄——值歸
    # resolver，schema 留欄；在場才驗）
    _check_temporal_intent(data, "", kind, errors, check_enums=False)


def _check_receipt(
    data: dict, stage: str, errors: list[str],
    *, now: datetime, base_dir: Path,
) -> None:
    kind = "receipt"
    slice_id = data.get("slice_id") or "<unnamed>"

    for label in ("delivery", "bounded_receipt_projection"):
        _require_object(label, data.get(label), kind, errors)

    plan_version = data.get("plan_version")
    if plan_version is not None and (
        not isinstance(plan_version, int) or isinstance(plan_version, bool) or plan_version < 1
    ):
        errors.append(
            f"Invalid plan_version `{plan_version}` for {kind} — 需正整數（D7 plan 回指）"
        )
    plan_hash = data.get("plan_hash")
    if plan_hash is not None and not (
        isinstance(plan_hash, str) and HEX64_RE.match(plan_hash)
    ):
        errors.append(
            f"Invalid plan_hash `{plan_hash}` for {kind} — 需 hex 64 位（D7 plan 回指）"
        )

    delivery = data.get("delivery")
    if isinstance(delivery, dict):
        verdict = delivery.get("verdict")
        if verdict is not None and verdict not in DELIVERY_VERDICTS:
            errors.append(_unknown_enum(
                FieldSpec("verdict", "machine-invariant", "always", "",
                          values=DELIVERY_VERDICTS, noun="verdict", plural="verdicts"),
                verdict, kind,
            ))
        mode = delivery.get("mode")
        if mode is not None and mode not in ("artifact", "receipt-only"):
            errors.append(_unknown_enum(
                FieldSpec("mode", "machine-invariant", "always", "",
                          values=("artifact", "receipt-only"), noun="delivery mode",
                          plural="delivery modes"),
                mode, kind,
            ))
        for key in ("l1_present", "l2_anchor"):
            if key in delivery and delivery[key] is not None and not isinstance(delivery[key], bool):
                errors.append(f"`delivery.{key}` must be a boolean for {kind}")
        if "anchor_hits" in delivery and not isinstance(delivery["anchor_hits"], list):
            errors.append(f"`delivery.anchor_hits` must be a list for {kind}")

        status = data.get("status")
        if status == "completed" and verdict not in ("delivered", "manual-anchor"):
            errors.append(
                f"Conflicting terminal for {kind} `{slice_id}`: status=`completed` but "
                f"delivery.verdict=`{verdict}` — terminal≠complete（機驗面 fail-loud；"
                f"完成判定＝sink 存在＋anchor 命中，D7 receipt minimum）"
            )
        if status == "completed" and verdict == "manual-anchor":
            anchor_hits = delivery.get("anchor_hits")
            if not (isinstance(anchor_hits, list) and anchor_hits):
                errors.append(
                    f"manual-anchor verdict requires at least one anchor hit for {kind} "
                    f"— 人工驗收逃生口須附錨證（J-3 收緊；delivered 面 anchors 契約同構）"
                )

    projection = data.get("bounded_receipt_projection")
    if isinstance(projection, dict):
        flag = projection.get("final_text_non_empty")
        if "final_text_non_empty" in projection and not isinstance(flag, bool):
            errors.append(
                f"`bounded_receipt_projection.final_text_non_empty` must be a boolean "
                f"for {kind}, got {type(flag).__name__}"
            )

    review = data.get("intent_review")
    if review is not None:
        if not isinstance(review, dict):
            errors.append(
                f"`intent_review` must be an object for {kind}, got {type(review).__name__}"
            )
        else:
            verdict = review.get("verdict")
            if not _present_nonempty(verdict):
                errors.append(
                    f"`intent_review.verdict` 不得為空 for {kind} — "
                    f"Intent Review 回寫面 minimum＝verdict＋leg＋read_set_exclusion"
                )
            elif verdict not in INTENT_REVIEW_VERDICTS:
                errors.append(_unknown_enum(
                    FieldSpec("verdict", "machine-invariant", "always", "",
                              values=INTENT_REVIEW_VERDICTS, noun="intent review verdict",
                              plural="intent review verdicts"),
                    verdict, kind,
                ))
            for key in ("leg", "read_set_exclusion"):
                if not _present_nonempty(review.get(key)):
                    errors.append(
                        f"`intent_review.{key}` 不得為空 for {kind} — "
                        f"Intent Review 回寫面 minimum＝verdict＋leg＋read_set_exclusion"
                    )


_CHECKERS = {
    "arc-spec": _check_arc_spec,
    "arc-plan": _check_arc_plan,
    "dispatch-slice": _check_dispatch_slice,
    "receipt": _check_receipt,
}


def validate(
    kind: str,
    data: object,
    stage: str = "dispatch",
    *,
    now: datetime | None = None,
    base_dir: Path | None = None,
) -> list[str]:
    """校驗一個 artifact dict，回傳錯誤列表（空列表＝通過）。

    contract 錯（未知 kind/stage、schema marker 不符、data 非 dict）raise
    ArcSpecError；欄位級錯誤逐條收集（一次報全部，不逐次擠牙膏）。

    now（AIR-240）＝temporal as_of 非未來檢查的時鐘——預設 UTC 現在；測試
    注入固定時鐘（AIR-239 R2 單一時鐘姿態）。base_dir＝temporal snapshot ref
    的相對解析基準（CLI 傳 plan 檔所在目錄；預設 CWD）。
    """
    now = now or datetime.now(tz=UTC)
    base_dir = base_dir or Path.cwd()
    if kind not in ARTIFACTS:
        raise ArcSpecError(
            f"Unknown kind `{kind}`. Available kinds: {', '.join(KINDS)}"
        )
    if stage not in STAGES:
        raise ArcSpecError(
            f"Unknown stage `{stage}`. Available stages: {', '.join(STAGES)}"
        )
    if not isinstance(data, dict):
        raise ArcSpecError(
            f"artifact payload must be an object for {kind}, got {type(data).__name__}"
        )
    art = ARTIFACTS[kind]
    marker = data.get("schema")
    if marker != art.schema_marker:
        raise ArcSpecError(
            f"Unknown schema marker `{marker}` for kind `{kind}`. "
            f"Available schema markers: {', '.join(a.schema_marker for a in ARTIFACTS.values())}"
        )

    errors: list[str] = []
    for f in art.fields:
        present = f.name in data and data[f.name] is not None
        if f.kind == "machine-invariant" and f.required_at in ("always", stage):
            nullable_ok = f.nullable and f.name in data
            if not nullable_ok and not _present_nonempty(data.get(f.name)):
                note = "" if f.required_at == "always" else f"（required at {stage} stage）"
                blank = "（blank/empty counts as missing）" if f.name in data else ""
                errors.append(
                    f"Missing machine-invariant field `{f.name}` for {kind}{note}{blank}. "
                    f"Required machine-invariant fields: "
                    f"{', '.join(_required_names(art, stage))}"
                )
                continue
        if present and f.values is not None:
            value = data[f.name]
            if value not in f.values:
                errors.append(_unknown_enum(f, value, kind))
        if present and f.kind == "machine-invariant" and f.required_at != "conditional":
            value = data[f.name]
            if isinstance(value, str):
                if not value.strip():
                    errors.append(
                        f"Machine-invariant field `{f.name}` is blank for {kind} — "
                        f"空白值視同缺欄（fail-loud）"
                    )
            elif (
                isinstance(value, list)
                and value
                and all(isinstance(item, str) for item in value)
                and not all(item.strip() for item in value)
            ):
                # 只查「純字串列表含空白」；list-of-dict（work_units 等）歸深檢
                errors.append(
                    f"Machine-invariant field `{f.name}` contains blank strings "
                    f"for {kind} — 空白值視同缺欄（fail-loud）"
                )

    _CHECKERS[kind](data, stage, errors, now=now, base_dir=base_dir)
    return errors


# ---------------------------------------------------------------------------
# 檔案解析＋schema 渲染＋CLI
# ---------------------------------------------------------------------------


def parse_artifact_file(path: Path, kind: str) -> dict:
    """從 .md（```json 區塊）或 .json 直檔取 artifact payload。"""
    if kind not in ARTIFACTS:
        raise ArcSpecError(
            f"Unknown kind `{kind}`. Available kinds: {', '.join(KINDS)}"
        )
    if not path.exists():
        raise ArcSpecError(f"artifact not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        raw = text
    else:
        if "```json" not in text or "```" not in text.split("```json", 1)[1]:
            raise ArcSpecError(
                f"no ```json block in artifact file: {path} — "
                f"四物檔以 markdown＋json 區塊承載（人類可讀＋機器可驗）"
            )
        raw = text.split("```json", 1)[1].split("```", 1)[0]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ArcSpecError(f"bad json in artifact {path}: {e}") from e
    if not isinstance(data, dict):
        raise ArcSpecError(
            f"artifact payload must be an object in {path}, got {type(data).__name__}"
        )
    marker = data.get("schema")
    if marker != ARTIFACTS[kind].schema_marker:
        raise ArcSpecError(
            f"Unknown schema marker `{marker}` for kind `{kind}`. "
            f"Available schema markers: "
            f"{', '.join(a.schema_marker for a in ARTIFACTS.values())}"
        )
    return data


def render_schema(kind: str | None = None) -> str:
    """欄位表輸出——D3 標注的人類／LLM 讀取面。"""
    arts = [ARTIFACTS[kind]] if kind else [ARTIFACTS[k] for k in KINDS]
    blocks: list[str] = []
    for art in arts:
        lines = [
            f"kind: {art.kind}（schema marker: {art.schema_marker}）",
            f"title: {art.title}",
            f"ownership: {art.ownership}",
            "",
            f"{'field':<22} {'kind':<18} {'required@':<12} values / enum",
            "-" * 100,
        ]
        for f in art.fields:
            values = ", ".join(f.values) if f.values else ""
            lines.append(
                f"{f.name:<22} {f.kind:<18} {f.required_at:<12} {values}"
            )
        lines.append("")
        lines.append("field 說明：")
        for f in art.fields:
            lines.append(f"  {f.name}: {f.desc}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="AIR-135.1 S1 arc schema＋fail-loud 校驗（四物：arc-spec／arc-plan／dispatch-slice／receipt）"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("schema", help="輸出欄位表（machine-invariant／llm-guidance 標注）")
    ps.add_argument("--kind", help="限定單一 kind（缺＝印全部四物）")

    pv = sub.add_parser("validate", help="校驗 artifact 檔（.md 的 ```json 區塊或 .json）")
    pv.add_argument("--kind", required=True, help="artifact kind")
    pv.add_argument("--stage", default="dispatch", help="compile（plan 時；resolver 欄可缺席）｜dispatch（派工時；全必填）")
    pv.add_argument("file", help="artifact 檔路徑")

    args = p.parse_args(argv)

    if args.cmd == "schema":
        if args.kind and args.kind not in ARTIFACTS:
            print(
                f"[arc-spec] Unknown kind `{args.kind}`. Available kinds: {', '.join(KINDS)}",
                file=sys.stderr,
            )
            return 2
        print(render_schema(args.kind))
        return 0

    # validate
    if args.stage not in STAGES:
        print(
            f"[arc-spec] Unknown stage `{args.stage}`. Available stages: {', '.join(STAGES)}",
            file=sys.stderr,
        )
        return 2
    try:
        data = parse_artifact_file(Path(args.file), args.kind)
        errors = validate(
            args.kind,
            data,
            stage=args.stage,
            base_dir=Path(args.file).resolve().parent,
        )
    except ArcSpecError as e:
        print(f"[arc-spec] ERROR: {e}", file=sys.stderr)
        return 2
    if errors:
        for err in errors:
            print(f"[arc-spec] {err}", file=sys.stderr)
        print(
            f"[arc-spec] {len(errors)} validation error(s) — 禁派工（fail-loud）",
            file=sys.stderr,
        )
        return 2
    print(f"VALID {args.kind} ({args.stage} stage): {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
