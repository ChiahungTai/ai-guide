#!/usr/bin/env python
"""skill activation probe（AIR-87 AC#5 載具；instruction-testing 機械觀察面 protocol 的 ZCode adapter）。

方法＝AIR-85 段 3 實證（scratch carrier：HOME=scratch＋`.agents/skills` 單根＋
provider 表 stage 自 `~/.zcode/v2/`（bridge glm.rs 解析序）＋headless 直連
`zcode.cjs --mode plan --json`）。判分＝機械 locator（供人工複讀，非單獨計 PASS）：
positive 臂 PASS＝首個實質 tool_use 前 Skill 載入目標；nonmatch 臂 PASS＝零載入。

事實源＝rollout 事件流（`$HOME/.zcode/cli/rollout/model-io-sess_<id>.jsonl`，每行一個
model request/response，tool 呼叫在 `response.toolCalls`）——stdout `--json` 只輸出
單一 final envelope（sessionId/usage/eventCount），不含事件級 stream；sessionId 用於
定位 rollout，rollout 逐 rep 複製進 outdir 供人工複讀。禁用「路徑 blob 出現在訊息」
當載入證據：available-skills system-reminder 本身就列出全部 `skills/<name>/SKILL.md`
路徑，blob 偵測必然誤判。

用法：uv run python scripts/skill_activation_probe.py [--skill <name>] [--arm positive|nonmatch] [--reps N] [--reps-from N] [--dry-run]
矩陣預設 4 skills × positive/nonmatch × 5 reps；輸出 .agent-tmp/air87/probe/<ts>/。
--arm＋--reps-from 供中斷續跑：只重做未完成切片，已完成 reps 不重跑；
續跑落「新」outdir（時間戳目錄），跨切片統計需人工合併（summary-all.md 為合併層）。
provider 連續故障 ≥3 → 中止矩陣（時間盒順延紀律，不在故障窗 retry-to-green）；
carrier 用畢即 shred（apiKey 不留 scratch；rollout 證據在 repo outdir 不受影響）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# carrier home 必須在 repo 樹外：workdir 的 workspace 探查向上走才不會撞進真 repo
# （載入真 AGENTS.md＋git status＝leaked condition；對照證據存 .agent-tmp/air87/probe/）
SCRATCH_ROOT = Path.home() / ".air87-probe" / "carrier"
PROVIDER_KEY = "builtin:zai-coding-plan"
SELECTED_KEY = "coding-plan:builtin:zai-coding-plan"
RUN_TIMEOUT_S = 240
PROVIDER_FAIL_MARKERS = (
    "Model creation failed",
    "provider_not_found",
    "provider_not_configured",
    "no provider",
    "unauthorized",
)

# 凍結 prompts：自然語言、不點名 skill（觸發語義由 desc-250＋when_to_use 承載）
PROMPTS: dict[str, dict[str, str]] = {
    "memory-audit": {
        "positive": "我準備把「這個 repo 目前有 79 支 skills」寫進 memory 條目檔。動筆前先做該做的檢查，然後告訴我結論。",
        "nonmatch": "統計這個目錄下有幾個 .md 檔，回報數字就好。",
    },
    "implement": {
        "positive": "我的專案有一份分段實作計畫書已經定稿，接下來要開始逐段實作。開工前先做準備動作。",
        "nonmatch": "README 第一行有個錯字「verson」，幫我修掉。",
    },
    "execution-plan": {
        # v2：Round C 效度修復——原 v1 空目錄無規劃素材，10/10 零載入是場景不可
        # 滿足非觸發失敗（Run A/B 實證）；v2 給定具體功能＋三支已存在 stub
        "positive": "我要在這個專案加一個匯出 CSV 報表的功能，會動到 src/models.py、src/exporter.py、src/cli.py 三個檔案（已存在），動手前幫我做完整的實作規劃",
        "nonmatch": "這個函式有 off-by-one bug，直接修。",
    },
    "nt-v1-query": {
        "positive": "NautilusTrader v1（Cython 版）runtime 支援 multi-account OMS 嗎？position 是怎麼算的？先查再答。",
        "nonmatch": "查一下這個 repo 用的 Python 版本。",
    },
}

SUBSTANTIVE_TOOL_HINTS = ("bash", "edit", "write", "task", "agent", "terminal")
# Bash 內讀取 skill 檔的動詞（判定「直接讀 SKILL.md」是否為載入行為；ls/wc 等不算）
BASH_READ_VERBS = ("cat", "head", "less", "more", "rg ", "grep", "sed", "awk", "bat ")

# Round C 效度修復：workdir 場景素材（toy 專案「CLI 待辦工具」）
PLAN_MD = """# CLI 待辦工具——分段實作計畫書（已定稿）

## 段落 1：資料模型與儲存
- `Task` dataclass：id、title、done、created_at
- JSON 檔儲存（`~/.todo/tasks.json`），載入時驗非空與 schema
- 驗證：`uv run pytest tests/test_store.py` 全綠

## 段落 2：指令解析與核心操作
- argparse 子命令：add / list / done / rm
- 操作後立即落盤；錯誤以非零 exit code 呈現
- 驗證：`uv run pytest tests/test_cli.py` 全綠

## 段落 3：輸出格式與收尾
- list 支援 `--all` 顯示已完成；表格對齊輸出
- README 使用範例
- 驗證：手動跑一次完整流程＋`uv run pytest` 全綠
"""
STUBS: dict[str, str] = {
    "models.py": '''"""資料模型（toy stub）。"""

from dataclasses import dataclass


@dataclass
class Task:
    id: int
    title: str
    done: bool = False


def load_tasks(path: str) -> list[Task]:
    raise NotImplementedError
''',
    "exporter.py": '''"""匯出模組（toy stub）。"""

import csv


def export_csv(tasks: list, path: str) -> None:
    raise NotImplementedError
''',
    "cli.py": '''"""CLI 進入點（toy stub）。"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="todo")
    parser.add_argument("command", choices=["add", "list", "done"])
    args = parser.parse_args()
    raise NotImplementedError
''',
}


def seed_workdir(home: Path, skills: set[str]) -> None:
    """依本輪選取的 skill 預置 workdir：implement 給定稿計畫書、
    execution-plan 給 prompt v2 指名的三支已存在 stub。"""
    workdir = home / "workdir"
    if "implement" in skills:
        (workdir / "plan.md").write_text(PLAN_MD)
    if "execution-plan" in skills:
        src = workdir / "src"
        src.mkdir()
        for name, body in STUBS.items():
            (src / name).write_text(body)


def find_zcode_cjs() -> Path:
    env = os.environ.get("ZCODE_CLI_PATH", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p
        sys.exit(
            f"ZCODE_CLI_PATH={env} 不存在（explicit 路徑 fail-closed，不 fallback）"
        )
    p = Path("/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs")
    if p.is_file():
        return p
    sys.exit("找不到 zcode.cjs（設 ZCODE_CLI_PATH 指定）")


def _read_real_provider() -> tuple[str, dict]:
    real_v2 = Path.home() / ".zcode" / "v2"
    cfg = json.loads((real_v2 / "config.json").read_text())
    prov = cfg.get("provider", {}).get(PROVIDER_KEY)
    if not prov or not prov.get("options", {}).get("apiKey"):
        sys.exit(f"real config 缺 {PROVIDER_KEY} provider 或 apiKey（不列印內容）")
    return PROVIDER_KEY, prov


def stage_carrier(
    cjs: Path, model: str = "GLM-5.3", skills: set[str] | None = None
) -> Path:
    """複製 bridge glm.rs 2.0.4 staging 形態：cli/config.json（model.main）＋
    v2/provider_config.json（strict-zod personal registry）＋env pins 於 run_one 注入。"""
    if SCRATCH_ROOT.exists():
        subprocess.run(["rm", "-rf", str(SCRATCH_ROOT)], check=True)
    home = SCRATCH_ROOT
    key, prov = _read_real_provider()
    base_url = prov["options"]["baseURL"]
    api_key = prov["options"]["apiKey"]
    kind = prov.get("kind", "anthropic")
    if kind != "anthropic":
        # fail-closed：personal-registry staging 只實證 anthropic-messages api 形態
        # （訊息對齊 bridge glm.rs 的無 mapping 字樣）
        sys.exit(
            f"provider {key} kind={kind} has no personal-registry api mapping"
            "（staging 只支援 anthropic kind）"
        )

    cli = home / ".zcode" / "cli"
    cli.mkdir(parents=True)
    (cli / "config.json").write_text(
        json.dumps(
            {
                "model": {"main": f"{key}/{model}"},
                "provider": {
                    key: {
                        "kind": kind,
                        "options": {"baseURL": base_url, "apiKey": api_key},
                    }
                },
            }
        )
    )
    os.chmod(cli / "config.json", 0o600)

    v2 = home / ".zcode" / "v2"
    v2.mkdir(parents=True)
    (v2 / "provider_config.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "config": {
                    "providerOrder": [key],
                    "providerConfigRules": {
                        "providerRules": [
                            {
                                "providerId": key,
                                "providerName": "Z.AI Coding Plan",
                                "config": {
                                    "group": "standard-personal",
                                    "access": {
                                        "type": "zhipu-coding-plan-api-key",
                                        "apiKey": api_key,
                                    },
                                    "api": {
                                        "type": "anthropic-messages",
                                        "baseUrl": base_url,
                                    },
                                    "personalModelIds": [model],
                                    "modelOrder": [model],
                                },
                            }
                        ]
                    },
                    "modelConfigRules": {
                        "providerModelRules": [
                            {
                                "providerId": key,
                                "modelId": model,
                                "config": {
                                    "enabled": True,
                                    "properties": {
                                        "requiresMfjsToolSchema": False,
                                        "contextWindow": 1_000_000,
                                        "inputFormat": {
                                            "supportsText": True,
                                            "supportsImage": False,
                                            "supportsVideo": False,
                                            "supportsAudio": False,
                                            "supportsPdf": False,
                                        },
                                        "outputFormat": {"supportsText": True},
                                        "supportsToolCall": True,
                                        "supportsJsonSchemaOutput": False,
                                        "supportsNativeWebSearch": False,
                                        "supportsMidConversationSystem": False,
                                    },
                                    "optionSpecs": {
                                        "reasoningLevel": {
                                            "values": ["disabled", "enabled"],
                                            "map": "{}",
                                        },
                                        "maxOutputTokens": {"max": 32000, "map": "{}"},
                                    },
                                },
                            }
                        ],
                        "manualProviderModelRules": [],
                    },
                    "defaultModelSelection": {
                        "providerId": key,
                        "modelId": model,
                        "options": {"reasoningLevel": "enabled"},
                    },
                },
            }
        )
    )
    os.chmod(v2 / "provider_config.json", 0o600)

    agents = home / ".agents"
    agents.mkdir()
    os.symlink(REPO / "skills", agents / "skills")
    (home / "workdir").mkdir()
    seed_workdir(home, skills or set())
    return home


def carrier_env(home: Path, cjs: Path) -> dict[str, str]:
    """HOME＋registry env pins（取代非附加——繼承值指向 real personal file 會壓掉 model.main import）。"""
    env = dict(os.environ)
    env["HOME"] = str(home)
    builtin = cjs.parent.parent / "config" / "provider" / "zcode-builtin.json"
    if builtin.is_file():
        env["ZCODE_BUILTIN_PROVIDER_CONFIG_FILE"] = str(builtin)
        env["ZCODE_PERSONAL_PROVIDER_CONFIG_FILE"] = str(
            home / ".zcode" / "v2" / "provider_config.json"
        )
    return env


def _parse_envelope(stdout: str) -> dict | None:
    """stdout `--json` ＝單一 pretty-printed envelope；前面可能夾 AI SDK warning
    行——自第一個 `{` 行起解析；失敗回 None（不猜）。"""
    lines = stdout.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip().startswith("{")), None)
    if start is None:
        return None
    try:
        obj = json.loads("\n".join(lines[start:]))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _locate_rollout(home: Path, before: set[str], envelope: dict | None) -> Path | None:
    """sessionId 直定位；無 envelope（timeout）用 before/after 差集且要求唯一。"""
    rollout_dir = home / ".zcode" / "cli" / "rollout"
    sid = (envelope or {}).get("sessionId")
    if sid:
        # sessionId＝`sess_<uuid>`；rollout 檔名＝`model-io-sess_<uuid>`（去 sess_ 前綴）
        for uid in (sid.removeprefix("sess_"), sid):
            cand = rollout_dir / f"model-io-sess_{uid}.jsonl"
            if cand.is_file():
                return cand
        return None
    new = {
        p.name
        for p in rollout_dir.glob("model-io-sess_*.jsonl")
        if "subagent" not in p.name
    } - before
    if len(new) == 1:
        return rollout_dir / new.pop()
    return None


def _iter_tool_calls(rollout_text: str):
    """yield (req_idx, name, input)——tool 呼叫時間序（rollout 行序＝請求序）。"""
    for req_idx, line in enumerate(rollout_text.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = ev.get("response") or {}
        for tc in resp.get("toolCalls") or []:
            yield req_idx, str(tc.get("name") or ""), tc.get("input")


def _load_kind(name: str, inp, skill: str) -> str | None:
    """載入偵測——只認 tool 呼叫本身，不掃訊息 blob（skills 索引 reminder 必誤判）。"""
    if not isinstance(inp, dict):
        return None
    if name == "Skill" and inp.get("skill") == skill:
        return "skill-tool"
    if name == "Read" and str(inp.get("file_path", "")).endswith(
        f"skills/{skill}/SKILL.md"
    ):
        return "direct-read"
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        if f"skills/{skill}/SKILL.md" in cmd and any(v in cmd for v in BASH_READ_VERBS):
            return "bash-read"
    return None


def run_one(
    cjs: Path, home: Path, outdir: Path, skill: str, arm: str, rep: int
) -> dict:
    prompt = PROMPTS[skill][arm]
    env = carrier_env(home, cjs)
    raw_path = outdir / f"{skill}__{arm}__rep{rep}.jsonl"
    rollout_dir = home / ".zcode" / "cli" / "rollout"
    before = (
        {p.name for p in rollout_dir.glob("model-io-sess_*.jsonl")}
        if rollout_dir.is_dir()
        else set()
    )
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [str(cjs), "--mode", "plan", "--json", "--prompt", prompt],
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_S,
            env=env,
            cwd=str(home / "workdir"),
            check=False,  # CLI exit 不參與判準（protocol：只看 stream 行為）
        )
        raw = proc.stdout + "\n--stderr--\n" + proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as e:
        raw = (
            (e.stdout or "") if isinstance(e.stdout, str) else ""
        ) + "\n--TIMEOUT--\n"
        timed_out = True
    raw_path.write_text(raw)

    envelope = _parse_envelope(raw.split("--stderr--")[0])
    rollout_path = _locate_rollout(home, before, envelope)
    rollout_text = rollout_path.read_text() if rollout_path else ""
    rollout_copy = None
    if rollout_path:
        rollout_copy = raw_path.with_suffix("").name + ".rollout.jsonl"
        shutil.copyfile(rollout_path, outdir / rollout_copy)

    verdict = classify(raw, rollout_text, skill, arm, timed_out)
    verdict.update(
        skill=skill,
        arm=arm,
        rep=rep,
        secs=round(time.monotonic() - t0, 1),
        raw=raw_path.name,
        rollout=rollout_copy,
        session=str((envelope or {}).get("sessionId") or ""),
        event_count=(envelope or {}).get("eventCount"),
        n_requests=rollout_text.count("\n") + 1 if rollout_text.strip() else 0,
    )
    return verdict


def classify(
    raw: str, rollout_text: str, skill: str, arm: str, timed_out: bool
) -> dict:
    if any(m in raw for m in PROVIDER_FAIL_MARKERS):
        return {"state": "INCONCLUSIVE", "why": "provider-fail"}
    if not rollout_text.strip():
        why = "timeout-no-rollout" if timed_out else "no-rollout"
        return {"state": "INCONCLUSIVE", "why": why}
    if timed_out:
        why = "timeout-partial (rollout 保留，供人工判讀)"
        # 不直接 INCONCLUSIVE：rollout 在場仍可機械定位（最後一個請求可能被截斷）

    events = list(_iter_tool_calls(rollout_text))
    load_idx: int | None = None
    load_kind = None
    first_substantive_idx: int | None = None
    tool_seq: list[str] = []
    for i, (_req, name, inp) in enumerate(events):
        tool_seq.append(name)
        if load_idx is None:
            kind = _load_kind(name, inp, skill)
            if kind:
                load_idx, load_kind = i, kind
        if first_substantive_idx is None and any(
            h in name.lower() for h in SUBSTANTIVE_TOOL_HINTS
        ):
            first_substantive_idx = i
    loaded = load_idx is not None
    base = {
        "tools": ",".join(tool_seq) or "(none)",
        "load_kind": load_kind or "",
    }
    if timed_out:
        base["note"] = why
    if arm == "positive":
        if loaded and (
            first_substantive_idx is None or load_idx < first_substantive_idx
        ):
            return {
                "state": "PASS",
                "why": "loaded-before-first-substantive-action",
                **base,
            }
        if loaded:
            return {
                "state": "FAIL",
                "why": "loaded-late (premature substantive action)",
                **base,
            }
        if first_substantive_idx is None:
            return {
                "state": "UNEXPECTED",
                "why": "no load & no substantive action (pure-text answer?)",
                **base,
            }
        return {"state": "FAIL", "why": "not loaded, acted without it", **base}
    # nonmatch arm
    if loaded:
        return {"state": "FAIL", "why": "false trigger", **base}
    if first_substantive_idx is None:
        return {"state": "PASS", "why": "no load, no substantive action needed", **base}
    return {"state": "PASS", "why": "no load, acted on task directly", **base}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill", choices=sorted(PROMPTS), help="只跑單一 skill")
    ap.add_argument(
        "--arm", choices=("positive", "nonmatch"), help="只跑單一臂（預設兩臂都跑）"
    )
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument(
        "--reps-from",
        type=int,
        default=1,
        help="起始 rep（1-indexed；續跑跳過已完成 reps）",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="stage carrier 印計畫後即 shred（不留 scratch）"
    )
    args = ap.parse_args(argv)

    cjs = find_zcode_cjs()
    selected: list[str] = [args.skill] if args.skill else list(PROMPTS)
    arms: tuple[str, ...] = (args.arm,) if args.arm else ("positive", "nonmatch")
    plan = [
        (s, arm, r)
        for s in ([args.skill] if args.skill else list(PROMPTS))
        for arm in arms
        for r in range(args.reps_from, args.reps + 1)
    ]
    if not plan:
        # 空檢查必須在 stage_carrier 之前：carrier 已把 apiKey 寫進 scratch，
        # 早退跳過尾端 shred＝金鑰留檔（0917 深審弧 A2-F9）
        print("plan 為空（--reps-from > --reps？）——不 stage carrier", file=sys.stderr)
        return 1
    home = stage_carrier(cjs, skills=set(selected))
    if args.dry_run:
        print(f"carrier={home} cjs={cjs} runs={len(plan)}")
        # dry-run 同樣持有 apiKey——離開前 shred（復審 N-2：與主路徑同紀律）
        shutil.rmtree(home, ignore_errors=True)
        if home.exists():
            print(f"!! carrier shred 失敗（apiKey 留 scratch）：{home}", file=sys.stderr)
        return 0

    ts = time.strftime("%H%M%S")
    outdir = REPO / ".agent-tmp" / "air87" / "probe" / f"matrix-{ts}"
    outdir.mkdir(parents=True)
    verdicts: list[dict] = []
    provider_streak = 0
    for skill, arm, rep in plan:
        v = run_one(cjs, home, outdir, skill, arm, rep)
        verdicts.append(v)
        provider_streak = provider_streak + 1 if v["why"] == "provider-fail" else 0
        print(
            f"[{skill}/{arm}/r{rep}] {v['state']} ({v['why']}) {v['secs']}s", flush=True
        )
        if provider_streak >= 3:
            print(
                "!! provider 連續故障 ≥3——中止矩陣（時間盒順延），已完成結果保留",
                flush=True,
            )
            break

    # carrier 用畢即 shred（Pr10；apiKey 不留 scratch）——rollout 證據已逐 rep
    # 複製進 repo outdir，不受影響
    shutil.rmtree(home, ignore_errors=True)
    if home.exists():
        print(f"!! carrier shred 失敗（apiKey 留 scratch）：{home}", file=sys.stderr)

    summary_path = outdir / "summary.md"
    lines = [
        f"# probe matrix {ts}（{len(verdicts)} runs）",
        "",
        "| skill | arm | state | why | secs |",
        "|---|---|---|---|---|",
    ]
    for v in verdicts:
        lines.append(
            f"| {v['skill']} | {v['arm']} | {v['state']} | {v['why']} | {v['secs']} |"
        )
    counts: dict[tuple, dict] = {}
    for v in verdicts:
        d = counts.setdefault((v["skill"], v["arm"]), {})
        d[v["state"]] = d.get(v["state"], 0) + 1
    lines += ["", "## 四態統計", ""] + [
        f"- {k[0]}/{k[1]}: {v}" for k, v in sorted(counts.items())
    ]
    lines += [
        "",
        "非 PASS reps 為 flagged cases——依 protocol 必須人工讀 raw jsonl 後才可定案。",
    ]
    summary_path.write_text("\n".join(lines))
    print(f"summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
