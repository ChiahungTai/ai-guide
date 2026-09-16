#!/usr/bin/env python3
"""Single-source invariant checker for ai-guide.

機械驗證 ai-guide 的「唯一/單一源/真相源」宣稱沒被 drift。

背景：2026-06 的 code-review 發現 review-engine 重構「正確診斷、不足處方」——
single-source 宣稱用散文維護，靠 AI 紀律 + 手動 rg，沒有機械力把「定義源」與
「schema 源」綁住（信心水準就是第一個受害者：review-engine 定義了，DimensionVerdict
schema 卻沒欄位）。本檔是當初少開的那張處方：把 single-source 變成可機械檢查的登記。

Run: uv run python skills/scan-project/scripts/check_single_source.py
Exit: non-zero if any critical/important finding（未來可掛 commit gate）。
"""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# scripts/ -> scan-project -> skills -> repo root
REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# REGISTRY —— 每個「唯一/單一源/真相源」宣稱一筆。
# 新增 single-source 宣稱 = 在此加一筆 = 宣告單一源本來該付的成本。
# （本檔出現前，散文宣稱是欠了這成本沒付 → drift 必然。）
# ---------------------------------------------------------------------------
INVARIANTS = [
    {
        "id": "severity",
        "type": "enum",
        "source": "skills/review-engine/SKILL.md",  # 唯一定義源
        "values": ["critical", "important", "suggestion"],
        "enforced_by": {
            "file": "skills/_common/workflow-review-pattern.md",
            "schema": "DimensionVerdict",
        },
        "note": "review-engine 是嚴重度唯一定義源；DimensionVerdict schema 必須含 severity 欄位",
    },
    {
        "id": "confidence",  # 信心水準
        "type": "enum",
        "source": "skills/review-engine/SKILL.md",  # 定義源
        "values": ["confirmed", "evidence-based", "inferred"],
        "enforced_by": {
            "file": "skills/_common/workflow-review-pattern.md",
            "schema": "DimensionVerdict",
        },
        "note": "review-engine 宣稱『每個 finding 必須標信心水準』；DimensionVerdict 必須含 "
        "confidence 欄位，否則 Workflow 模式（唯一有 schema 強制的模式）結構性丟棄此訊號",
    },
    {
        "id": "audience_self_declare",
        "type": "classification",
        "source": "CLAUDE.md",  # 受眾模型（外部分類源）
        "consumers": [
            "skills/illustrate/SKILL.md",
            "skills/debrief/SKILL.md",
            "skills/smell-detector/SKILL.md",
        ],  # layer 3 人類 viewport
        "must_contain_any": ["layer 3", "人類 viewport", "B 軸", "受眾"],
        "note": "CLAUDE.md 分類為 layer 3 的命令本體必須自標受眾 —— 與 /code-review axis 3 "
        "共用 arch-thinking skill 的消歧對稱（外部分類 + 命令不自知 = drift 溫床）",
    },
    {
        "id": "skill_allowlist_coverage",
        "type": "coverage",
        "source_glob": "skills/*/SKILL.md",  # 定義源：每個 skill 的 frontmatter name
        "source_field": "name",
        "enforced_by": {
            "file": "settings.json",
            "extract": r"Skill\(([^)]+)\)",  # 從 allow-list 提取已授權 skill name 集合
        },
        "note": "skills/*/SKILL.md 的 name 是 skill 唯一定義源；settings.json allow-list 必須覆蓋每個 "
        "Skill(<name>) — rename 後新名缺 allow-list = drift（memory code-review-settings-sync "
        "反覆性，靠機械閘門根治）。單向：只抓 missing；dead entry（舊名殘留）因 settings 含 "
        "commands/built-in/plugin 需分類不抓，危害僅 noise 且 rename 必伴隨 missing 觸發修復。",
    },
    {
        "id": "base_perspective",
        "type": "source_contains",
        "source": "skills/review-engine/SKILL.md",
        "must_contain_any": ["預設 3 agent", "3-perspective"],
        "note": "review-engine base 點 4 定義 3-perspective（clean/UC/Correctness）為單一源 —— "
        "防未來 drift 回 2-perspective。消費者反向（活躍文檔 rg 2-perspective 應 0 hits）"
        "靠 rg + EP Review 兜底（消費者引用形態不一，機械反向 check 留未來）",
    },
    {
        "id": "deploy_bundle_freshness",
        "type": "deploy_freshness",
        "note": "部署 bundle 是 rules/ + guide（單一源）的衍生 snapshot；非 Claude 三端"
        "（~/.zcode、~/.codex、~/.config/muse 的 AGENTS.md）只讀 bundle，stale = "
        "session 讀舊規則。Claude 端 ~/.claude/rules/ 目錄 symlink 即時，不在檢查範圍。"
        "真實案例：2026-08-18 發現部署版落後 source 六條 rules（tool-discipline 新紀律"
        "缺席）——編輯 rules 的 ZCode session 讀不到部署紀律（紀律在 meta rule，不進 "
        "bundle），drift 靠外部 session 偶然發現。此檢查把「編輯後須 deploy」從散文"
        "紀律變機械閘門",
    },
    {
        "id": "report_shell_provenance",
        "type": "shell_provenance",
        "generator": "scripts/check_report_shells.py",
        "note": "任務家殼（tracked ai-analysis/**/index.html）是 source 的 "
        "projection——互斥 SHA／stale projection／file:// 絕對路徑／raw .md "
        "route（viewer-only 合約）都是已發生的失真形態（codex 09-06 全 repo "
        "審查 I-7；followup 補 raw-route 規則與本接線）。委派 generator 腳本，"
        "rc1＝violation 逐行轉 important。",
    },
    {
        "id": "hook_registration",
        "type": "hook_registration",
        "registrations": ["settings.json", "hooks/zcode-registration.json"],
        # 僅接 Claude 端的 hook：settings.json 是 local-only（gitignored），
        # fresh clone 上缺場 → 這些 hook 豁免（註冊事實存在於本機設定，
        # repo 內不可驗證）；settings.json 在場時仍照常檢查
        "claude_only": ["compact-tail-inject.py"],
        # 非 entry 的共用庫（被 sensor import，自身不是 hook 入口）——
        # 任何機器都不該要求註冊（註冊它反而是錯的接線）
        "exempt": ["memory_hook_common.py"],
        "note": "hooks/*.py 是「code 在、接線不在」的孤兒溫床（真實案例 "
        "2026-08-29 F8：compact-tail-inject.py 兩處註冊面皆無、從未生效——"
        "防線看起來存在，實際從未攔截）。每個 hook 腳本至少要出現在一個註冊處"
        "（settings.json = Claude 端、hooks/zcode-registration.json = ZCode 端"
        "範本），否則 critical",
    },
    {
        "id": "zcode_live_parity",
        "type": "zcode_live_parity",
        "template": "hooks/zcode-registration.json",
        "live": "~/.zcode/cli/config.json",
        "note": "zcode-registration.json（repo 模板）的每個 hook 接線必須已部署到 "
        "live ~/.zcode/cli/config.json 且 hooks.enabled=true——template 有、live 無 "
        "= hook 不會 fire（F8 形狀：防線看起來存在實際從未攔截；2026-08-30 實例："
        "block-python-file-write 在模板、live 缺席直到人工補）。live 檔不存在"
        "（非 ZCode 機器）→ skip 不 false positive。單向 template→live：live 端 "
        "UI 手加的 hook 不誤報（coverage 語義同 skill_allowlist_coverage）；"
        "結構比對（event/matcher/檔名三元組）——掛錯 matcher 或 .bak 殘字樣不算已部署",
    },
    {
        "id": "agents_projection_sync",
        "type": "agents_projection_sync",
        "generator": "scripts/sync_agents.py",
        "source_dir": "agents/roles/",
        "targets": ["agents/zcode/", "agents/claude/"],
        "note": "roles/ 是 role authoring 單一源；zcode/claude/ 是生成物（ownership "
        "marker）。委派 sync_agents --check（純比對、零寫入）：drift＝critical"
        "（生成物與源不一致——手改生成物或漏跑 sync）；generator 缺席＝important"
        "（單一源宣稱欠了機械閘門）。",
    },
    {
        "id": "bridge_model_vocab",
        "type": "forbidden_pattern",
        "source": "skills/model-routing/SKILL.md",
        "must_contain_all": ["native-ID-only", "GLM-5.3-Flash"],
        "scan": [
            "ai-development-guide.md",
            "AGENTS.md",
            "rules/",
            "skills/",
            "agents/",
            "hooks/",
        ],
        "forbid": [
            {
                "pattern": r"(?i)--model[ =]+['\"]?(sonnet|opus)\b",
                "gate": r"(?i)--family",
                "why": "bridge --model 只收 native ID（VR-1，AIR-78）——CC 詞彙字串＝bug",
            },
            {
                "pattern": r"(?i)\b(?:glm[\w.\-]*(?:sonnet|opus)|(?:sonnet|opus)[\w.\-]*glm)",
                "why": "禁 native＋alias 複合 slug（vocabulary invariant，AIR-78 AC#5）",
            },
        ],
        "note": "AIR-78 AC#6 機械 guard：alias 退役（d4 VR-1）後 bridge 委派範例的 "
        "CC 詞彙殘留＝bug。CC harness 自身接線（tier 表 CC 詞彙欄、`model: opus` "
        "frontmatter／CC CLI invocation 形）不在此列——flag 形以同行 `--family` "
        "gate 限定在 bridge 語境；compound-slug 無 gate（任何複合皆錯）；歸檔面"
        "（ai-analysis、ref-docs）不掃。錨點＝must_contain_all（逐一缺席各 critical）。",
    },
    {
        "id": "model_routing_current_doctrine",
        "type": "forbidden_pattern",
        "source": "skills/model-routing/SKILL.md",
        "must_contain_all": ["WorkUnitContract", "catalog.toml", "presets.toml"],
        "scan": [
            "ai-development-guide.md",
            "AGENTS.md",
            "rules/",
            "skills/",
            "agents/",
            "hooks/",
        ],
        "forbid": [
            {
                "pattern": r"(?i)^#{2,6}\s.*\btier\b.*[→×]",
                "why": "舊 tier 權威表 header（tier → (model,effort)／tier × provider）"
                "＝AIR-91 S2 已移除的單軸強度檔權威形，重現於任何 active 檔＝"
                "current-doctrine drift",
            },
            {
                "pattern": r"(?i)^#{2,6}\s.*\brole\b.*(?:→|->).*"
                r"(?:requirement|tier)\b",
                "why": "role → requirement（tier）分配表 header＝舊 role→tier 兩跳權威形"
                "（S2 移除）——Role 指派只來自 WorkUnitContract",
            },
            {
                "pattern": r"(?i)\b(?:execution-plan|implement|judge-review|post-build"
                r"|ep-review|code-review)\s*[=＝]\s*(?:full|lite|vision)\b",
                "why": "workflow 整體綁單一 tier（如 post-build=full）＝誤導整鏈單模型的"
                "舊寫法（EP 問題 #4）——workflow 擁有的是 per-phase work-unit rows",
            },
            {
                "pattern": r"(?i)\bvision[\s-]?tier\b|\btier\s*[=＝:：]\s*vision\b",
                "why": "vision tier＝把 capability filter 與強度列並排的舊單軸語義"
                "（EP 問題 #2）——native_vision 是 ModelIdentity capability",
            },
            {
                "pattern": r"(?i)^tier\s*:",
                "why": "roles frontmatter tier tag＝AIR-91 S2 已移除項（description 不帶 "
                "tier 標記）——projection gate 不攔未知 frontmatter 鍵，回歸由此抓",
            },
        ],
        "note": "AIR-91 S4 current-doctrine guard（S4A 腿）：agents_projection_sync 只守 "
        "registry bytes parity，守不住 Markdown 面重現的舊 tier 權威形。掃描面同 "
        "bridge_model_vocab（僅 .md；tests/ 排除——guard fixtures 合法引用禁用形；"
        "catalog.toml／presets.toml 非 .md 不在面內）。header 錨定避開 S2 移除標記"
        "註解與決策記錄（historical-exclusion）；清單＝S4A broad rg 掃描反推的最小集合"
        "（ai-analysis/_tasks/_archived/09-15-model-capability-routing/references/"
        "current-consumers.md）——lite/full 作為 presets 相容 requirement token、"
        "slug 名（lite-verify）、handoff「建議執行 tier」欄（管轄對照已裁定非 drift）、"
        "memory-audit full/lite 級別、EP 規模 full 皆合法不在禁止列。錨點＝"
        "must_contain_all（新 doctrine 三源：contract schema／供給 catalog／部署 "
        "presets——逐一缺席各 critical）。",
    },
]


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def rel(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT))


def extract_schema_block(text: str, schema_name: str) -> str | None:
    """回傳 '### <schema_name>' 標題下的第一個 ```json block 內容；找不到回 None。"""
    pat = re.compile(
        r"^#{2,4}\s.*?" + re.escape(schema_name) + r".*?$.*?```(?:json)?\n(.*?)\n```",
        re.DOTALL | re.MULTILINE,
    )
    m = pat.search(text)
    return m.group(1) if m else None


def check_enforced_by(inv: dict) -> list[tuple[str, str, str]]:
    """定義在 source、強制 schema 在 enforced_by.file → schema 必須真的含該欄位。

    抓「定義源 / schema 源分離」的 drift：review-engine 定義了信心水準，
    但 DimensionVerdict schema 沒欄位 → 高規格 Workflow 審查結構性丟棄該訊號。
    """
    if inv.get("type") != "enum":
        return []  # check_enforced_by 是 enum 專屬（定義 values + schema 強制欄位）；coverage 的 enforced_by 語意不同（extract pattern），由 check_coverage 處理
    eb = inv.get("enforced_by")
    if not eb:
        return []
    f = REPO_ROOT / eb["file"]
    if not f.exists():
        return [(inv["id"], "critical", f"enforced_by 檔案不存在: {eb['file']}")]
    text = read_text(f)
    field = inv["id"]
    schema_name = eb.get("schema")
    if schema_name:
        block = extract_schema_block(text, schema_name)
        if block is None:
            return [
                (
                    inv["id"],
                    "important",
                    f"{eb['file']} 找不到 schema 區段 '{schema_name}'（標題或 ```json 格式變了？）",
                )
            ]
        if f'"{field}"' not in block:
            return [
                (
                    inv["id"],
                    "critical",
                    f"{eb['file']} 的 {schema_name} schema 缺少 '{field}' 欄位 —— "
                    f"定義在 {inv['source']} 卻未反映在強制 schema（定義源/schema 源分離 drift）",
                )
            ]
    else:
        if f'"{field}"' not in text:
            return [(inv["id"], "critical", f"{eb['file']} 缺少 '{field}'")]
    return []


def check_classification(inv: dict) -> list[tuple[str, str, str]]:
    """source（如 CLAUDE.md）分類的 commands，本體必須自標受眾。"""
    if inv.get("type") != "classification":
        return []
    must = inv["must_contain_any"]
    out = []
    for cmd in inv.get("commands", []):
        p = REPO_ROOT / cmd
        if not p.exists():
            out.append((inv["id"], "important", f"分類命令不存在: {cmd}"))
            continue
        text = read_text(p)
        if not any(t in text for t in must):
            out.append(
                (
                    inv["id"],
                    "important",
                    f"{cmd} 被 {inv['source']} 分類但本體未自標受眾（需含其一: {must}）",
                )
            )
    return out


def check_coverage(inv: dict) -> list[tuple[str, str, str]]:
    """source_glob 下每個檔案的 source_field（frontmatter name）必須被 enforced_by 的 extract 覆蓋。

    抓「定義源目錄 ↔ 執行源 allow-list」覆蓋 drift：skills/ 定義 skill name，settings.json
    allow-list 漏了 → 顯式呼叫觸發權限提示（rename 後最常見）。

    單向（定義源 → 執行源）：只抓 missing；不抓 dead entry（執行源有定義源無的）——
    settings 含 commands/built-in/plugin，精確判 dead 需 external allowlist，危害僅 noise，
    且 rename 必伴隨 missing 觸發修復。
    """
    if inv.get("type") != "coverage":
        return []
    src_files = sorted(REPO_ROOT.glob(inv["source_glob"]))
    field_pat = re.compile(
        rf"^{re.escape(inv['source_field'])}:\s*(.+?)\s*$", re.MULTILINE
    )
    defined: dict[str, str] = {}
    for f in src_files:
        m = field_pat.search(read_text(f))
        if m:
            defined[m.group(1).strip().strip('"').strip("'")] = rel(f)
    eb = inv["enforced_by"]
    ef = REPO_ROOT / eb["file"]
    if not ef.exists():
        return []  # enforced_by 檔不存在（settings.json 是 local/gitignored）→ skip，不 false positive
    allowed = set(re.findall(eb["extract"], read_text(ef)))
    return [
        (
            inv["id"],
            "important",
            f"skill '{name}'（{src}）未在 {eb['file']} allow-list 找到 "
            f"（缺 Skill({name}) — rename 後新名未同步 allow-list？）",
        )
        for name, src in defined.items()
        if name not in allowed
    ]


def check_source_contains(inv: dict) -> list[tuple[str, str, str]]:
    """source 檔必須含 must_contain_any 之一（定義源自身驗證，防 drift 回非預期值）。"""
    if inv.get("type") != "source_contains":
        return []
    src = REPO_ROOT / inv["source"]
    if not src.exists():
        return [(inv["id"], "important", f"source 檔不存在: {inv['source']}")]
    if not any(t in read_text(src) for t in inv["must_contain_any"]):
        return [
            (
                inv["id"],
                "critical",
                f"{inv['source']} 缺少定義源應含的: {inv['must_contain_any']} —— drift 回非預期值？",
            )
        ]
    return []


def check_forbidden_pattern(inv: dict) -> list[tuple[str, str, str]]:
    """forbidden_pattern：掃 instruction 活面的禁用字串（單一源契約的殘留 guard）。

    行級匹配：pattern 與選配 gate（同時命中同一行才算）——gate 用於把 flag 形
    限定在可辨識的委派語境（如 `--family` 在場），避免誤中合法 CC CLI 形。
    錨點檢查＝must_contain_all 語義（每個 token 缺席各發一條 critical）。
    """
    if inv.get("type") != "forbidden_pattern":
        return []
    findings: list[tuple[str, str, str]] = []
    src = REPO_ROOT / inv["source"]
    if not src.exists():
        return [(inv["id"], "important", f"source 檔不存在: {inv['source']}")]
    src_text = read_text(src)
    for token in inv.get("must_contain_all", []):
        if token not in src_text:
            findings.append(
                (inv["id"], "critical", f"{inv['source']} 缺契約錨點: {token}")
            )
    compiled = [
        (
            re.compile(spec["pattern"]),
            re.compile(spec["gate"]) if spec.get("gate") else None,
            spec["why"],
        )
        for spec in inv.get("forbid", [])
    ]
    for entry in inv.get("scan", []):
        p = REPO_ROOT / entry
        if p.is_dir():
            files = sorted(p.rglob("*.md"))
        elif p.exists():
            files = [p]
        else:
            findings.append(
                (inv["id"], "important", f"scan entry 不存在（guard 面縮小）: {entry}")
            )
            continue
        for f in files:
            for lineno, line in enumerate(read_text(f).splitlines(), 1):
                for pat, gate, why in compiled:
                    m = pat.search(line)
                    if m and (gate is None or gate.search(line)):
                        findings.append(
                            (
                                inv["id"],
                                "important",
                                f"{rel(f)}:{lineno}: 禁用字串 {m.group(0)!r} —— {why}",
                            )
                        )
    return findings


def _main_worktree() -> Path | None:
    """git 主 worktree 路徑（`worktree list` 首條＝main）；無法判定回 None。

    部署 authority 顯式化：bundle 只該從 main worktree 部署出去；linked
    worktree（feature/audit 用）與部署目標的差異不代表 stale。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("worktree "):
            return Path(line.split(" ", 1)[1])
    return None


def _is_detached_head() -> bool | None:
    """HEAD 是否 detached；無法判定回 None（detached＝checkout 的是任意修訂，非部署權威）。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() == "HEAD"


def check_deploy_freshness(inv: dict) -> list[tuple[str, str, str]]:
    """非 Claude 三端的部署 AGENTS.md 必須 == 當前 source 重建的 bundle（byte 比對）。

    單一源是 repo 內 rules/ + guide；部署檔是衍生 snapshot。skip 條件（不 false
    positive）：目標不存在（該機器未用該 harness）、無 generator header marker
    （非 deploy_agents.py 產出，用戶自管檔）。差異僅在 main worktree（非 detached）
    才判 critical＋開 deploy 處方——非 main worktree / detached / 無法判定 worktree
    時降 important：差異可能只是版本不同，照 deploy 處方執行會用非權威版本覆寫
    三個 harness 的 always-on policy。
    """
    if inv.get("type") != "deploy_freshness":
        return []
    deploy_py = REPO_ROOT / "scripts" / "deploy_agents.py"
    if not deploy_py.exists():
        return [(inv["id"], "important", f"deploy script 不存在: {deploy_py}")]
    try:
        spec = importlib.util.spec_from_file_location("deploy_agents", deploy_py)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "expected_bundle_for"):
            # per-target 預期（含 muse 變體；S3 draft-3 A 案後 full bundle 比 muse 恆假）
            expected = [(t, mod.expected_bundle_for(t)) for t in mod.TARGETS]
        else:
            # 舊形態（無變體）：單一 full bundle 比全部 TARGETS
            bundle = mod.build_bundle(
                # "neutral" 綁定 deploy_agents main() 的 --scope default；default 改變時此處需同步
                mod.discover_rules(mod.RULES_DIR, {"neutral"}),
                "neutral",
            ).encode("utf-8")
            expected = [(t, bundle) for t in mod.TARGETS]
    except Exception as exc:  # load/build 失敗（如 deploy_agents 編輯後 SyntaxError）
        return [(inv["id"], "important", f"無法以 source 重建 bundle: {exc!r}")]
    # marker 取自 HEADER 首行（單一源）——不硬編碼字串複製品，HEADER 改版自動跟隨
    marker = mod.HEADER.splitlines()[0].encode("utf-8")
    out = []
    for target, bundle in expected:
        data = target.read_bytes() if target.exists() else None
        if data is None or marker not in data:
            continue
        if data == bundle:
            continue
        main_wt = _main_worktree()
        if main_wt is None:
            out.append(
                (
                    inv["id"],
                    "important",
                    f"{target} 與本 checkout 重建 bundle 不一致，但無法判定 main "
                    "worktree（git 失敗？）——不排除版本差異，至 main checkout 重跑"
                    "確認後才考慮 deploy",
                )
            )
            continue
        if main_wt.resolve() != REPO_ROOT.resolve():
            out.append(
                (
                    inv["id"],
                    "important",
                    f"{target} 與本 checkout 重建 bundle 不一致，但本 checkout 非 main "
                    f"worktree（main＝{main_wt}）——差異可能僅是版本不同，不代表部署 "
                    "stale；至 main checkout 重跑本檢查確認，勿在非 main worktree 跑 "
                    "deploy（會把非權威版本覆寫三個 harness）",
                )
            )
            continue
        if _is_detached_head():
            out.append(
                (
                    inv["id"],
                    "important",
                    f"{target} 與 source 重建 bundle 不一致，但 HEAD detached——無法"
                    "判定部署 authority；回到 branch 上重跑確認",
                )
            )
            continue
        out.append(
            (
                inv["id"],
                "critical",
                f"{target} 與 source 重建 bundle 不一致（stale 部署）——非 Claude "
                f"session 正在讀舊規則；跑 `uv run python scripts/deploy_agents.py` 同步",
            )
        )
    return out


def check_hook_registration(inv: dict) -> list[tuple[str, str, str]]:
    """hooks/*.py 每檔至少出現在一個註冊處——抓孤兒 hook。

    註冊處由 inv['registrations'] 列（相對 REPO_ROOT 的文字檔；不存在者
    skip 不 false positive）。以檔名子字串比對——註冊處以絕對路徑引用
    hook 腳本，檔名是穩定鍵。
    """
    if inv.get("type") != "hook_registration":
        return []
    hook_files = sorted((REPO_ROOT / "hooks").glob("*.py"))
    if not hook_files:
        return []
    registered = ""
    claude_side_present = False
    for rel in inv["registrations"]:
        p = REPO_ROOT / rel
        if p.exists():
            registered += read_text(p)
            if rel == "settings.json":
                claude_side_present = True
    claude_only = set(inv.get("claude_only", []))
    exempt = set(inv.get("exempt", []))
    out = []
    for hf in hook_files:
        # word-boundary 比對——純子字串會讓 a.py 被 xa.py 的註冊行誤判
        if re.search(rf"\b{re.escape(hf.name)}\b", registered):
            continue
        if hf.name in exempt:
            continue  # 共用庫非 hook 入口（exempt 清單＝invariant 定義顯式列舉）
        if hf.name in claude_only and not claude_side_present:
            continue  # Claude 端註冊檔 local-only：缺場機器上豁免
        out.append(
            (
                inv["id"],
                "critical",
                f"hooks/{hf.name} 未出現在任何註冊處（{inv['registrations']}）——"
                "孤兒 hook：code 在、接線從未存在，防線是假的（刪掉或接線）",
            )
        )
    return out


def _wiring(data: dict) -> set[tuple[str, str, str]]:
    """(event, matcher, basename) 接線三元組——matcher 缺席＝""（Stop 型）。

    檔名以 negative lookahead 收尾（`ok.py.bak` 不算 ok.py）；從已 parse 的
    command/args 取樣，不對 live 文字做存在性比對（文字出現≠接線正確）。
    """
    out: set[tuple[str, str, str]] = set()
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return out
    events = hooks.get("events")
    if not isinstance(events, dict):
        return out
    for event, groups in events.items():
        if not isinstance(groups, list):
            continue
        for g in groups:
            if not isinstance(g, dict):
                continue
            matcher = g.get("matcher") or ""
            for h in g.get("hooks") or []:
                if not isinstance(h, dict) or h.get("enabled") is False:
                    continue
                text = (
                    str(h.get("command", ""))
                    + " "
                    + " ".join(str(a) for a in h.get("args") or [])
                )
                for name in re.findall(r"([A-Za-z0-9_-]+\.(?:py|sh))(?![\w.-])", text):
                    out.add((event, matcher, name))
    return out


def check_zcode_live_parity(
    inv: dict, live_path: Path | None = None
) -> list[tuple[str, str, str]]:
    """zcode-registration.json（repo 模板）的 hook 接線必須已部署到 live config。

    抓「註冊≠fire」的部署漂移：template 加了 hook、live config 沒 merge →
    hook 從未執行（F8 形狀）。**結構比對**（event＋matcher＋檔名三元組）：
    掛錯 matcher 或僅文字出現（如 `.bak` 殘字樣）都不算已部署。
    單向 template→live（live 端 UI 手加不誤報）；live 缺場（非 ZCode 機器）skip。
    matcher 視為精確字串（template 與 live 皆 repo 自管，同串即同語義）。
    """
    if inv.get("type") != "zcode_live_parity":
        return []
    tpl = REPO_ROOT / inv["template"]
    if not tpl.exists():
        return [
            (
                inv["id"],
                "important",
                f"template 檔不存在: {inv['template']}（INVARIANTS 路徑 typo？）",
            )
        ]
    live = Path(live_path) if live_path else Path(inv["live"]).expanduser()
    if not live.exists():
        return []
    try:
        tpl_data = json.loads(read_text(tpl))
        live_data = json.loads(read_text(live))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [
            (
                inv["id"],
                "important",
                f"template/live 非 JSON（手改壞？）: {tpl} / {live}",
            )
        ]
    if not isinstance(tpl_data, dict) or not isinstance(live_data, dict):
        return [(inv["id"], "important", "template/live JSON 非 object")]
    hooks_live = live_data.get("hooks")
    if not isinstance(hooks_live, dict):
        return [(inv["id"], "important", f"live config hooks 區塊非 object: {live}")]
    out: list[tuple[str, str, str]] = []
    if hooks_live.get("enabled") is not True:
        out.append(
            (
                inv["id"],
                "critical",
                f"{live} hooks.enabled 非 true——所有 ZCode hook 不會 fire",
            )
        )
    missing = _wiring(tpl_data) - _wiring(live_data)
    for event, matcher, name in sorted(missing):
        where = f"{event}/{matcher}" if matcher else event
        out.append(
            (
                inv["id"],
                "critical",
                f"{name}（{where}）在 template 的接線未以同 matcher 部署到 {live}"
                "——註冊≠fire（F8 形狀：防線存在但從未攔截）",
            )
        )
    return out


def check_agents_projection_sync(inv: dict) -> list[tuple[str, str, str]]:
    """agents/roles/ 單一源 ↔ 生成 registry 的 drift gate（委派 sync_agents --check）。

    --check 是純比對（零寫入，測試有 tripwire 釘住）。rc==1＝drift（critical）；
    rc==2＝診斷分流的 important（parity drift／roles-mismatch——修 policy 或 skill 表，
    重跑 sync 修不了）；rc==3＝parity 未驗證（PARITY_SOURCE 缺席——registry bytes
    一致但 policy parity 無從校驗，不得當綠）；其他非零＝important（uv 缺席／
    呼叫失敗等，不誤導為 drift、不炸整個 checker）。
    """
    if inv.get("type") != "agents_projection_sync":
        return []
    generator = REPO_ROOT / inv["generator"]
    if not generator.exists():
        return [(inv["id"], "important", f"sync generator 不存在: {generator}")]
    if shutil.which("uv") is None:
        return [
            (inv["id"], "important", "uv 不在 PATH——無法執行 projection sync gate"),
        ]
    try:
        proc = subprocess.run(
            ["uv", "run", "--no-sync", "python", str(generator), "--check"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=REPO_ROOT,
            check=False,
        )
    except OSError as exc:
        return [(inv["id"], "important", f"projection gate 呼叫失敗: {exc}")]
    if proc.returncode == 1:
        drift = (proc.stdout + proc.stderr).strip().splitlines()
        head = "; ".join(drift[:5]) + ("…" if len(drift) > 5 else "")
        return [
            (
                inv["id"],
                "critical",
                f"生成 registry 與 roles/ 源 drift（{head}）——手改生成物或編輯 roles/ 後未跑 sync",
            )
        ]
    if proc.returncode == 2:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        return [
            (
                inv["id"],
                "important",
                f"projection gate fatal（parity drift 或 roles/policy mismatch——修 policy/"
                f"skill 表非重跑 sync）：{' | '.join(tail)}",
            )
        ]
    if proc.returncode == 3:
        return [
            (
                inv["id"],
                "important",
                "projection gate parity 未驗證（skills/model-routing/SKILL.md 缺席）"
                "——registry bytes 一致但 policy parity 無從校驗（checkout 不完整？）",
            )
        ]
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        return [
            (
                inv["id"],
                "important",
                f"projection gate 非預期退出 rc={proc.returncode}"
                f"（parity drift 或 roles/policy mismatch？）：{' | '.join(tail)}",
            )
        ]
    return []


def check_shell_provenance(inv: dict) -> list[tuple[str, str, str]]:
    """Report Shell provenance gate（委派 scripts/check_report_shells.py）。

    rc==1＝violation（[FAIL] 行逐行轉 important）；rc==2＝無法列舉
    （git 失敗）；uv 缺席／呼叫失敗＝important（不炸整個 checker）。
    """
    if inv.get("type") != "shell_provenance":
        return []
    script = REPO_ROOT / inv["generator"]
    if not script.exists():
        return [(inv["id"], "important", f"shell lint 不存在: {script}")]
    if shutil.which("uv") is None:
        return [
            (inv["id"], "important", "uv 不在 PATH——無法執行 shell provenance gate")
        ]
    try:
        proc = subprocess.run(
            ["uv", "run", "--no-sync", "python", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=REPO_ROOT,
            check=False,
        )
    except OSError as exc:
        return [(inv["id"], "important", f"shell provenance gate 呼叫失敗: {exc}")]
    if proc.returncode == 0:
        return []
    out = (proc.stdout + proc.stderr).strip().splitlines()
    fails = [
        ln.removeprefix("[FAIL] ").strip() for ln in out if ln.startswith("[FAIL]")
    ]
    if fails:
        return [(inv["id"], "important", msg) for msg in fails]
    return [
        (
            inv["id"],
            "important",
            f"shell provenance gate rc={proc.returncode}: {' | '.join(out[-3:])}",
        )
    ]


def main() -> int:
    findings: list[tuple[str, str, str]] = []
    for inv in INVARIANTS:
        findings += check_enforced_by(inv)
        findings += check_classification(inv)
        findings += check_coverage(inv)
        findings += check_source_contains(inv)
        findings += check_forbidden_pattern(inv)
        findings += check_deploy_freshness(inv)
        findings += check_hook_registration(inv)
        findings += check_zcode_live_parity(inv)
        findings += check_agents_projection_sync(inv)
        findings += check_shell_provenance(inv)

    crit = [f for f in findings if f[1] == "critical"]
    imp = [f for f in findings if f[1] == "important"]

    print(f"=== single-source check（{len(INVARIANTS)} invariants）===")
    print(f"critical: {len(crit)}  important: {len(imp)}")
    print()
    for inv_id, sev, msg in findings:
        print(f"[{sev.upper():9}] {inv_id}: {msg}")
    if not findings:
        print("✅ 所有 single-source invariant 通過")
    return 1 if (crit or imp) else 0


if __name__ == "__main__":
    sys.exit(main())
