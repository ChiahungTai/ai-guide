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
from pathlib import Path

SCHEMA_ARC_SPEC = "arc-spec/1"
SCHEMA_ARC_PLAN = "arc-plan/1"
SCHEMA_DISPATCH_SLICE = "dispatch-slice/1"
SCHEMA_SLICE_RECEIPT = "slice-receipt/1"

KINDS = ("arc-spec", "arc-plan", "dispatch-slice", "receipt")
STAGES = ("compile", "dispatch")

ROLES = ("implement", "review", "verify", "test", "intent-review")
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
FAMILIES = ("local", "muse", "codex", "glm")
TERMINALS = ("completed", "budget-limited", "blocked-human-decision", "failed")
CAPABILITY_MODES = ("ReadOnly", "ReadWrite", "Execute", "All")
AUTHORITIES = ("writer", "read-only")
COLLECTION_MODES = ("waiter", "bounded-receipt", "manual")
DELIVERY_VERDICTS = ("delivered", "undelivered", "manual-anchor", "not-assessed")
COMMIT_DELEGATIONS = ("none", "conditional-this-repo")

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
                      "工作單元列表——unit_id 錨 card node id（唯一）、role 枚舉、phase 引用 135.3 六站語彙（不重定）、depends_on 拓撲"),
            FieldSpec("budget_context", "machine-invariant", "always",
                      "預算 context——revert_exposure_cap（敞口帽）＋usage_cap（用量帽）分欄（AC#6）；數值須有限且 ≥0"),
            FieldSpec("terminal_semantics", "machine-invariant", "always",
                      "終態語義（D6）：on_budget_exhausted=budget-limited、raise_cap=human-action、settle_gate=human"),
            FieldSpec("plan_changes", "machine-invariant", "always",
                      "PLAN_CHANGES 修訂流（D4）：每筆須附 what＋diff 交驗收腿複核；初始為空列表", nullable=True),
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
                      "role-dependent read-set：{policy, pointers}（AC#2：same page ≠ same projection；review/verify/test=problem-contract-only、intent-review=chain-exclusion）"),
            FieldSpec("sink", "machine-invariant", "always",
                      "artifact 預期路徑或 receipt-only：{mode, path?}（AC#2；欄位語義 owner＝135.7）"),
            FieldSpec("accept", "machine-invariant", "conditional",
                      "accept 機驗：{predicate, anchors}——sink 為 artifact 時必帶（預設 exists+readable+nonempty；terminal≠complete）"),
            FieldSpec("budget_context", "machine-invariant", "always",
                      "超支即停機械判準（AC#6）：revert_remaining＋slice_budget（有限 ≥0）＋debit_events 指針"),
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


def _check_arc_spec(data: dict, stage: str, errors: list[str]) -> None:
    baseline = data.get("card_baseline")
    if baseline is not None and not BASELINE_RE.match(str(baseline)):
        errors.append(
            f"Invalid card_baseline `{baseline}` for arc-spec — "
            f"需 hex 7-40 位（card tree baseline SHA）"
        )


def _check_arc_plan(data: dict, stage: str, errors: list[str]) -> None:
    kind = "arc-plan"
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
            for key in ("unit_id", "title", "phase"):
                if key in wu and not _present_nonempty(wu[key]):
                    errors.append(
                        f"work_units[{i}].{key} 不得為空 for {kind}"
                    )
            if "depends_on" in wu and not isinstance(wu["depends_on"], list):
                errors.append(
                    f"work_units[{i}].depends_on must be a list for {kind}"
                )

    budget = data.get("budget_context")
    if isinstance(budget, dict):
        for key in ("revert_exposure_cap", "usage_cap"):
            _check_budget_num(f"budget_context.{key}", budget.get(key), kind, errors)

    _check_terminal_semantics("terminal_semantics", data.get("terminal_semantics"), kind, errors)

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


def _check_dispatch_slice(data: dict, stage: str, errors: list[str]) -> None:
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
        for key in ("revert_remaining", "slice_budget"):
            _check_budget_num(f"budget_context.{key}", budget.get(key), kind, errors)
        if "debit_events" in budget and not isinstance(budget["debit_events"], list):
            errors.append(
                f"`budget_context.debit_events` must be a list for {kind}（扣款事件指針）"
            )

    _check_terminal_semantics("terminal_semantics", data.get("terminal_semantics"), kind, errors)


def _check_receipt(data: dict, stage: str, errors: list[str]) -> None:
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

    projection = data.get("bounded_receipt_projection")
    if isinstance(projection, dict):
        flag = projection.get("final_text_non_empty")
        if "final_text_non_empty" in projection and not isinstance(flag, bool):
            errors.append(
                f"`bounded_receipt_projection.final_text_non_empty` must be a boolean "
                f"for {kind}, got {type(flag).__name__}"
            )


_CHECKERS = {
    "arc-spec": _check_arc_spec,
    "arc-plan": _check_arc_plan,
    "dispatch-slice": _check_dispatch_slice,
    "receipt": _check_receipt,
}


def validate(kind: str, data: object, stage: str = "dispatch") -> list[str]:
    """校驗一個 artifact dict，回傳錯誤列表（空列表＝通過）。

    contract 錯（未知 kind/stage、schema marker 不符、data 非 dict）raise
    ArcSpecError；欄位級錯誤逐條收集（一次報全部，不逐次擠牙膏）。
    """
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

    _CHECKERS[kind](data, stage, errors)
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
        errors = validate(args.kind, data, stage=args.stage)
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
