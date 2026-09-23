#!/usr/bin/env python3
"""ai-guide governance installer——五部署面安裝單一入口（AIR-116）。

邊界：只收斂安裝/註冊面；閘行為本體零改動。wrap 面（rules/agents）子進程呼叫
既有權威工具，輸出透傳＋退出碼串接，禁重寫。動詞＝install/uninstall；bundle
部署（deploy_agents.py）是另一條線。設計決策 Q1-Q9 與安全模型（compute-then-
apply／plan journal／僅變更備份／malformed 拒寫／原子寫）見 governance/README.md
與 EP：ai-analysis/_tasks/0917-air116-unified-governance/ep.md。
"""

# R5 Python 地板守衛——任何 tomllib import 之前（machine python3=3.9）。
import sys

if sys.version_info < (3, 11):  # noqa: UP036 -- bootstrap must explain unsupported system Python before tomllib import.
    print(
        "ai-guide governance installer 需要 Python 3.11+（tomllib）。\n"
        "請改用：uv run python governance/install.py …",
        file=sys.stderr,
    )
    sys.exit(2)

import argparse
import copy
import datetime
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.toml"
REPO_TOKEN = "{{REPO}}"
HOME_TOKEN = (
    "{{HOME}}"  # AIR-110 G4：plist 源機器 home 路徑佔位（registrations 同款 render）
)
HOOK_PYTHON_TOKEN = "{{HOOK_PYTHON}}"
JOURNAL_DIR = Path.home() / ".local/share/ai-guide/governance-plan-journal"
BAK_KEEP = 3
JOURNAL_KEEP = 10

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_GUARD = 2
EXIT_NOT_IMPL = 3
EXIT_EXEC = 4  # 執行錯誤（malformed／lost-update／子進程失敗）——journal 有線索

# S6 穩定契約（[bootstrap_cli] 機器可讀投影的 argv 面錨點——兩面對帳防 drift）。
CLI_SURFACES = ["rules", "skills", "hooks", "agents", "memory", "monitor", "all"]
CLI_FLAGS = ["--dry-run", "--uninstall", "--check", "--verify"]


# P0-2 凍結：CC/ZCode live config 逐字重現參數（＋尾換行）。
class _SerializeParams(TypedDict):
    indent: int
    ensure_ascii: bool


SERIALIZE_PARAMS: _SerializeParams = {"indent": 2, "ensure_ascii": False}

_DRY_RUN = (
    False  # 結構性防線：dry-run 模式下任何寫入 chokepoint 直接 raise（1201 事故教訓）
)


class GovernanceError(Exception):
    """fail-loud 執行錯誤（malformed config、lost-update、子進程失敗）。"""


def set_dry_run() -> None:
    global _DRY_RUN
    _DRY_RUN = True


# ── 基礎 helpers ─────────────────────────────────────────────────


def _canonical_root() -> Path:
    """git main worktree 根＝控制面部署錨點（card WT/任意 basename checkout 通吃）。

    live symlink/hook 路徑必須指 canonical——card WT 安裝指自己的話，WT 關閉後
    live 指向已刪路徑（deny 閘靜默失效）。git rev-parse --git-common-dir 在
    canonical checkout 回相對 ".git"（→REPO_ROOT）、在 worktree 回絕對
    "/<main>/.git"（→其父）。解析失敗退 REPO_ROOT（行為同無 git 環境）。
    快取以 REPO_ROOT 為 key（tests monkeypatch REPO_ROOT 後自動重算）。
    """
    key = str(REPO_ROOT)
    if key not in _CANONICAL_CACHE:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            out = proc.stdout.strip()
            # 相對輸出（".git"）須對 REPO_ROOT 解析——對進程 cwd resolve 會在
            # cwd≠REPO_ROOT 時誤判 canonical（復審 N-1）；絕對輸出（worktree 形態）
            # 與 REPO_ROOT 相除後即自身，兩形態同一式
            root = (
                (REPO_ROOT / out).resolve().parent
                if (proc.returncode == 0 and out)
                else REPO_ROOT
            )
        except (OSError, subprocess.SubprocessError):
            root = REPO_ROOT
        _CANONICAL_CACHE[key] = root
    return _CANONICAL_CACHE[key]


_CANONICAL_CACHE: dict[str, Path] = {}


def _hook_path_pattern() -> re.Pattern:
    """套件 hook 路徑辨識（identity 用）——錨定 canonical 與本 checkout 兩根。

    舊版字面 "/ai-guide/hooks/" 耦合 checkout basename：非 ai-guide basename
    的 checkout（persistent card WT、未來 rename、fork clone）render 出的路徑
    不匹配 → group identity 塌縮碰撞 → check 假 drift／merge 重複 append。
    """
    key = (str(_canonical_root()), str(REPO_ROOT))
    if key not in _HOOK_PATTERN_CACHE:
        alt = "|".join(sorted(re.escape(r) for r in set(key)))
        _HOOK_PATTERN_CACHE[key] = re.compile(rf"(?:{alt})/hooks/[\w.\-]+")
    return _HOOK_PATTERN_CACHE[key]


_HOOK_PATTERN_CACHE: dict[tuple[str, str], re.Pattern] = {}


_HOOK_PYTHON_CACHE: str | None = None


def resolve_hook_python() -> str:
    """Return the installed uv-managed CPython 3.12 used by deployed hooks."""
    global _HOOK_PYTHON_CACHE
    if _HOOK_PYTHON_CACHE is not None:
        return _HOOK_PYTHON_CACHE

    uv = shutil.which("uv")
    if uv is None:
        raise GovernanceError(
            "uv 缺席，無法解析治理 hook Python 3.12。"
            "先安裝 uv，再執行 `uv python install 3.12`。"
        )
    argv = [
        uv,
        "python",
        "find",
        "--managed-python",
        "--no-python-downloads",
        "--no-project",
        "--no-config",
        "--no-cache",
        "3.12",
    ]
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GovernanceError(f"解析治理 hook Python 3.12 失敗：{exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()[:300]
        raise GovernanceError(
            "找不到已安裝的 uv-managed Python 3.12。"
            "先執行 `uv python install 3.12` 後重跑 governance installer。"
            + (f"\n{detail}" if detail else "")
        )
    raw = proc.stdout.strip()
    path = Path(raw)
    if (
        not raw
        or not path.is_absolute()
        or not path.exists()
        or not os.access(path, os.X_OK)
    ):
        raise GovernanceError(f"uv 回傳不可執行的 Python 3.12 路徑：{raw!r}")
    _HOOK_PYTHON_CACHE = raw
    return raw


def render(text: str) -> str:
    rendered = text.replace(REPO_TOKEN, str(_canonical_root())).replace(
        HOME_TOKEN, str(Path.home())
    )
    if HOOK_PYTHON_TOKEN in rendered:
        rendered = rendered.replace(HOOK_PYTHON_TOKEN, resolve_hook_python())
    return rendered


def render_uninstall(text: str) -> str:
    """Uninstall identity render：只展開 REPO/HOME，保留 {{HOOK_PYTHON}}。

    移除 identity 只認 matcher＋hook script 路徑（C1）——uninstall 不得要求
    resolver（uv/managed 3.12 缺席時 rollback 仍須能清 package-owned 條目）。
    """
    return text.replace(REPO_TOKEN, str(_canonical_root())).replace(
        HOME_TOKEN, str(Path.home())
    )


def _toml_basic_escape(text: str) -> str:
    """TOML basic-string 跳脫（`\\`／`"`）——shell-quoted 片段內含引號時仍是合法 TOML 源。"""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_codex(text: str, *, resolve_python: bool = True) -> str:
    """Codex 面 render：command 字串走 shell 解析，無 hook args 欄位（C2）。

    interpreter 與 repo 根皆 shlex.quote（再經 TOML basic-string 跳脫）——
    含空白／引號路徑仍是單一 argv；無特殊字元時兩層皆恆等，parity 不漂移。
    uninstall 關閉 resolve_python，保留 interpreter token，但沿用相同路徑 quoting。
    """
    rendered = text.replace(
        REPO_TOKEN, _toml_basic_escape(shlex.quote(str(_canonical_root())))
    ).replace(HOME_TOKEN, _toml_basic_escape(shlex.quote(str(Path.home()))))
    if resolve_python and HOOK_PYTHON_TOKEN in rendered:
        rendered = rendered.replace(
            HOOK_PYTHON_TOKEN, _toml_basic_escape(shlex.quote(resolve_hook_python()))
        )
    return rendered


def render_plist(text: str) -> str:
    """G4 plist render（AIR-110 R2 codex#5）：parse-modify-dump——plistlib.loads
    (源) → 只對已知路徑欄位（ProgramArguments 各元素／WorkingDirectory／
    StandardOutPath／StandardErrorPath／EnvironmentVariables 值）做 token 替換
    → plistlib.dumps()。

    禁 XML 全文 .replace：XML 註解禁 ASCII 雙連字號——token 字樣或 home 路徑
    含 `--` 會毒化註解使嚴格 parser 拒讀（launchd 寬容不等於合法）；dump 卸除
    註解即免疫，且非路徑欄位（如 Label）的 token 字樣不被誤替換。
    """
    import plistlib

    try:
        doc = plistlib.loads(text.encode())
    except plistlib.InvalidFileException as exc:
        raise GovernanceError(
            f"版控源非合法 plist，拒 render fail-loud：{exc}"
        ) from exc
    if not isinstance(doc, dict):
        raise GovernanceError("版控源 plist 根非 dict（launchd 形態），拒 render")
    args = doc.get("ProgramArguments")
    if isinstance(args, list):
        doc["ProgramArguments"] = [render(a) if isinstance(a, str) else a for a in args]
    for key in ("WorkingDirectory", "StandardOutPath", "StandardErrorPath"):
        if isinstance(doc.get(key), str):
            doc[key] = render(doc[key])
    env = doc.get("EnvironmentVariables")
    if isinstance(env, dict):
        doc["EnvironmentVariables"] = {
            k: render(v) if isinstance(v, str) else v for k, v in env.items()
        }
    return plistlib.dumps(doc).decode()


def home_path(p: str) -> Path:
    return Path(os.path.expanduser(p))


def real_target(target: Path) -> Path:
    """P0-3 鐵律：symlink 目標先 resolve（原子寫直打 symlink 路徑＝斷鏈）。"""
    return target.resolve() if target.is_symlink() else target


def load_manifest() -> dict:
    with open(MANIFEST_PATH, "rb") as fh:
        return tomllib.load(fh)


def serialize_json(obj: object) -> str:
    return json.dumps(obj, **SERIALIZE_PARAMS) + "\n"


def read_json_config(path: Path) -> dict:
    if not path.exists():
        return {}  # 乾淨機器：檔案缺席＝自空根建（EP Q3——malformed 只指 parse 失敗）
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise GovernanceError(
            f"malformed config，拒寫 fail-loud：{path}\n{exc}"
        ) from exc


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode()).hexdigest()


# ── plan journal（Q3/R2：中途 kill 可精確 resume/回滾）────────────


def journal_path(surface: str) -> Path:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")  # noqa: DTZ005 -- preserve existing local-naive journal/backup timestamp format.
    return JOURNAL_DIR / f"{ts}-{surface}.json"


def write_journal(path: Path, plan: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    _prune_glob(JOURNAL_DIR, "*.json", JOURNAL_KEEP)


def mark_done(jp: Path, plan: dict, index: int) -> None:
    plan["targets"][index]["done"] = True
    write_journal(jp, plan)


def _prune_glob(directory: Path, pattern: str, keep: int) -> None:
    files = sorted(directory.glob(pattern))
    for old in files[:-keep] if len(files) > keep else []:
        old.unlink(missing_ok=True)


def backup_target(real: Path) -> Path:
    """R7：僅變更備份（caller 保證內容將變）；copy2 保 mtime；保留最近 3 份（限自家命名）。"""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")  # noqa: DTZ005 -- preserve existing local-naive journal/backup timestamp format.
    bak = real.with_name(
        f"{real.name}.bak-{ts}-{os.getpid()}-gov"
    )  # pid 防同秒碰撞（S-4）
    shutil.copy2(real, bak)
    # 只 prune 自家後綴（他弧手工 bak 不入額度）；按 mtime 排序非檔名（1201 事故教訓——
    # 檔名排序把最新備份當最舊刪）。
    own = sorted(
        (real.parent).glob(f"{real.name}.bak-*-gov"), key=lambda p: p.stat().st_mtime
    )
    for old in own[:-BAK_KEEP] if len(own) > BAK_KEEP else []:
        old.unlink(missing_ok=True)
    return bak


# ── 原子寫（temp＋parse 驗證＋preimage 對比＋os.replace）──────────


def apply_text_change(
    real: Path,
    new_text: str,
    *,
    toml_validate: bool = False,
    plist_validate: bool = False,
) -> str:
    """唯一寫入 chokepoint。回 "noop"（byte-equal 零寫入零備份）或 "written"。

    通用 preimage 防線：寫入前 live 若變（codex runtime 寫 [hooks.state]、
    ZCode runtime 併發重寫 config——1201 事故實證）即 fail/retry。
    """
    if _DRY_RUN:
        raise GovernanceError(
            "dry-run 模式嘗試寫入（結構性防線——路由 bug 不應能到這裡）"
        )
    current: str | None = real.read_text() if real.exists() else None
    if current == new_text:
        return "noop"
    import plistlib

    if toml_validate and current is not None:
        try:
            tomllib.loads(current)  # live 可解析才護得起
        except tomllib.TOMLDecodeError as exc:
            raise GovernanceError(
                f"malformed config，拒寫 fail-loud：{real}\n{exc}"
            ) from exc
    if plist_validate and current is not None:
        try:
            plistlib.loads(current.encode())
        except plistlib.InvalidFileException as exc:
            raise GovernanceError(
                f"malformed plist，拒寫 fail-loud：{real}\n{exc}"
            ) from exc
    if current is not None:
        backup_target(real)
    real.parent.mkdir(
        parents=True, exist_ok=True
    )  # 乾淨機器 ~/.zcode/cli 等父目錄未必在場（AC-6.3 fixture 實證）
    tmp = real.with_name(f".{real.name}.tmp-{os.getpid()}")
    tmp.write_text(new_text)
    if toml_validate:
        try:
            tomllib.loads(tmp.read_text())
        except tomllib.TOMLDecodeError as exc:
            tmp.unlink(missing_ok=True)
            raise GovernanceError(
                f"新全文 parse 驗證失敗（未寫入）：{real}\n{exc}"
            ) from exc
    if plist_validate:
        try:
            plistlib.loads(tmp.read_text().encode())
        except plistlib.InvalidFileException as exc:
            tmp.unlink(missing_ok=True)
            raise GovernanceError(
                f"新 plist parse 驗證失敗（未寫入）：{real}\n{exc}"
            ) from exc
    current_now: str | None = real.read_text() if real.exists() else None
    if current_now != current:
        tmp.unlink(missing_ok=True)
        raise GovernanceError(
            f"lost-update：live file 已變（與 preimage 不符），fail/retry：{real}"
        )
    os.replace(tmp, real)
    return "written"


# ── JSON 面（CC/ZCode）：event→group 層級 merge ─────────────────


def _group_scripts(group: dict) -> frozenset:
    names = set()
    for h in group.get("hooks", []):
        joined = " ".join(
            [str(h.get("command", ""))] + list(map(str, h.get("args", [])))
        )
        for m in _hook_path_pattern().findall(joined):
            names.add(m.rsplit("/", 1)[-1])
    return frozenset(names)


def _group_identity(group: dict) -> tuple:
    return (group.get("matcher"), _group_scripts(group))


def merge_json_hooks(
    live_root: dict, package: dict, merge_root_key: str, *, remove: bool
) -> tuple[dict, bool]:
    """merge_root_key 子樹層級 merge/uninstall（F-5：manifest membership 權威）。

    模板形態兩家原生：cc.json＝event→groups map；zcode.json＝{enabled, events}。
    live 子樹缺席（乾淨機器）＝install 自空子樹建、uninstall 零動作。
    回 (new_root, changed)。1201 事故教訓：merge 必在 manifest 宣告的子樹內操作，
    禁把模板鍵散落 root 頂層。
    """
    root = copy.deepcopy(live_root)
    existed = isinstance(root.get(merge_root_key), dict)
    subtree = copy.deepcopy(root[merge_root_key]) if existed else {}
    changed = False
    if (
        not remove
        and "enabled" in package
        and subtree.get("enabled") != package["enabled"]
    ):
        subtree["enabled"] = package["enabled"]
        changed = True
    events = package.get("events", package)
    # live event map 位置：zcode 子樹有 events 鍵；cc 子樹本體即 event map
    ev_container = subtree.setdefault("events", {}) if "events" in package else subtree
    for evt, tmpl_groups in events.items():
        groups = ev_container.setdefault(evt, [])
        for tg in tmpl_groups:
            ident = _group_identity(tg)
            idx = next(
                (i for i, g in enumerate(groups) if _group_identity(g) == ident), None
            )
            if remove:
                if idx is not None:
                    groups.pop(idx)
                    changed = True
            elif idx is None:
                groups.append(copy.deepcopy(tg))
                changed = True
            elif groups[idx] != tg:
                groups[idx] = copy.deepcopy(tg)
                changed = True
        if remove and evt in ev_container and not ev_container[evt]:
            del ev_container[evt]
            changed = True
    if remove and (
        (isinstance(subtree.get("events"), dict) and not subtree["events"])
        or ("events" not in package and not subtree)
    ):
        root.pop(merge_root_key, None)  # 全空＝子樹由套件創建，整鍵移除回 preimage 形態
        return root, True
    if changed or not existed:
        root[merge_root_key] = subtree
    return root, changed


# ── codex 面：group 級文字片段（註解標記）＋TOML transaction ─────

GROUP_HEADER = re.compile(r"^\[\[hooks\.([A-Za-z]+)\]\]\s*$")
# MULTILINE：findall 掃整個 group unit text 時 ^ 須逐行成立（trust 診斷腿；
# 缺旗標時 handlers 恆 0——live verify 首跑實證）；match() 用法不受影響。
HANDLER_HEADER = re.compile(r"^\[\[hooks\.[A-Za-z]+\.hooks\]\]", re.MULTILINE)
AI_GUIDE_COMMENT = "# ai-guide"


def _peel_leading_comments(
    lines: list[str], header_idx: int, zone_start: int
) -> list[str]:
    """從 group header 前的連續註解/空行 run 中，剝出屬於套件的前導註解。

    邊界：只從最後一行 `# ai-guide` 開頭的註解起剝——他 family 的尾註解
    （如 chatgpt-web `# End …`）留給前一段，禁搬運（所有權正確性）。
    """
    run_start = header_idx
    while run_start > zone_start and (
        lines[run_start - 1].startswith("#") or lines[run_start - 1].strip() == ""
    ):
        run_start -= 1
    for i in range(run_start, header_idx):
        if lines[i].startswith(AI_GUIDE_COMMENT):
            return lines[i:header_idx]
    return []


def codex_group_units(text: str) -> tuple[str, list[dict]]:
    """切 codex config 成 (preamble, units)；unit＝group（原子合併單位）或 zone。

    group unit＝前導 ai-guide 註解＋`[[hooks.E]]`＋全部 `[[hooks.E.hooks]]` 子表；
    zone＝其餘頂層表（[hooks.state]、[projects.*] 等）原樣保留。
    前導註解自前一 holder 尾端「實際搬移」（截斷），禁複製留存（註解重複 bug 教訓）。
    """
    lines = text.splitlines(keepends=True)
    hdr = [i for i, ln in enumerate(lines) if ln.startswith("[")]
    if not hdr:
        return text, []
    preamble_lines = lines[: hdr[0]]
    units: list[dict] = []
    current: dict | None = None
    last_holder = preamble_lines
    j = 0
    while j < len(hdr):
        s, e = hdr[j], hdr[j + 1] if j + 1 < len(hdr) else len(lines)
        zone = lines[s:e]
        m = GROUP_HEADER.match(zone[0])
        if m:
            lead = _peel_leading_comments(lines, s, hdr[j - 1] if j else 0)
            if lead and last_holder[len(last_holder) - len(lead) :] == lead:
                del last_holder[len(last_holder) - len(lead) :]
            current = {"kind": "group", "lines": list(lead) + list(zone)}
            units.append(current)
            last_holder = current["lines"]
        elif current is not None and HANDLER_HEADER.match(zone[0]):
            current["lines"] += zone
            last_holder = current["lines"]
        else:
            current = None
            units.append({"kind": "zone", "lines": list(zone)})
            last_holder = units[-1]["lines"]
        j += 1
    return (
        "".join(preamble_lines),
        [{"kind": u["kind"], "text": "".join(u["lines"])} for u in units],
    )


def _codex_group_identity(unit_text: str) -> tuple:
    m = re.search(r"^\[\[hooks\.([A-Za-z]+)\]\]", unit_text, re.MULTILINE)
    event = m.group(1) if m else ""
    group = tomllib.loads(unit_text)["hooks"][event][0]
    scripts: set[str] = set()
    for handler in group.get("hooks", []):
        command = handler.get("command", "")
        if not isinstance(command, str):
            continue
        try:
            argv = shlex.split(command, comments=False)
        except ValueError:
            continue  # foreign shell syntax is not a package ownership claim.
        # Only canonical direct forms establish ownership; foreign data arguments do not.
        if len(argv) == 1:
            script = argv[0]
        elif len(argv) == 2 and (
            argv[0] == HOOK_PYTHON_TOKEN
            or re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(argv[0]).name)
        ):
            script = argv[1]
        else:
            continue
        if _hook_path_pattern().fullmatch(script):
            scripts.add(script.rsplit("/", 1)[-1])
    return (event, group.get("matcher"), frozenset(scripts))


def codex_positional_shift_warnings(live_text: str, template_text: str) -> list[str]:
    """Q6/SM-14：uninstall 移除套件 group 後，同 event 後續非套件 group 的
    positional index 前移——其 state key 綁舊 index，既有 trust 失效，需 re-approve。
    """
    owned = {
        _codex_group_identity(u["text"])
        for u in codex_group_units(template_text)[1]
        if u["kind"] == "group"
    }
    warnings: list[str] = []
    counters: dict[str, int] = {}
    removed_before: dict[str, int] = {}
    for u in codex_group_units(live_text)[1]:
        if u["kind"] != "group":
            continue
        ident = _codex_group_identity(u["text"])
        event = ident[0]
        idx = counters.get(event, 0)
        counters[event] = idx + 1
        if ident in owned:
            removed_before[event] = removed_before.get(event, 0) + 1
        elif removed_before.get(event):
            warnings.append(
                f"positional 前移：{event} group #{idx}→#{idx - removed_before[event]}"
                f"（matcher={ident[1]!r}）——既有 trust 將失效，需 re-approve"
            )
    return warnings


def _codex_template_groups(template_text: str) -> dict[tuple, str]:
    """Shared merge/remove/check gate: package ownership must be nonempty and unique."""
    _, tmpl_units = codex_group_units(template_text)
    tmpl_by_ident = {
        (_codex_group_identity(u["text"])): u["text"]
        for u in tmpl_units
        if u["kind"] == "group"
    }
    if len(tmpl_by_ident) != sum(1 for u in tmpl_units if u["kind"] == "group"):
        raise GovernanceError(
            "codex 模板內部 identity 碰撞（group 定義不唯一）——拒合併"
        )
    if any(not ident[2] for ident in tmpl_by_ident):
        raise GovernanceError("codex 模板 ownership 無法辨識——拒合併空 script identity")
    return tmpl_by_ident


def merge_codex_text(
    live_text: str, template_text: str, *, remove: bool
) -> tuple[str, list[str]]:
    """group 級 merge/uninstall；回 (new_text, 訊息清單)。identity 相符才動，他 family 禁碰。"""
    preamble, live_units = codex_group_units(live_text)
    tmpl_by_ident = _codex_template_groups(template_text)
    out: list[str] = []
    messages: list[str] = []
    matched: set[tuple] = set()
    for u in live_units:
        if u["kind"] != "group":
            out.append(u["text"])
            continue
        ident = _codex_group_identity(u["text"])
        if ident not in tmpl_by_ident:
            out.append(u["text"])
            continue
        matched.add(ident)
        if remove:
            messages.append(f"removed group: {ident[0]}/{ident[1]} {sorted(ident[2])}")
            continue
        if u["text"] != tmpl_by_ident[ident]:
            messages.append(f"updated group: {ident[0]}/{ident[1]} {sorted(ident[2])}")
            out.append(tmpl_by_ident[ident])
            continue
        out.append(u["text"])
    if not remove:
        for ident, text_ in tmpl_by_ident.items():
            if ident not in matched:
                messages.append(
                    f"appended group: {ident[0]}/{ident[1]} {sorted(ident[2])}"
                )
                out.append(text_)
    return preamble + "".join(out), messages


def _codex_state_event(event: str) -> str:
    """P0-1 凍結公式：state key 的 event 段＝PascalCase→snake_case（pre_tool_use 非
    pretooluse——.lower() 會誤報 Untrusted，live verify 首跑實證）。"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()


def _codex_owned_state_keys(
    live_text: str, template_text: str
) -> dict[tuple, list[str]]:
    """套件 group ident → 預測 state keys。positional key 僅診斷／分類用（Q4 紅線：
    禁作驗收契約——--check 的 Modified 分類只影響 drift 措辭，drift 兩態都成立）。"""
    source = f"{Path.home() / '.codex/config.toml'}"
    _, live_units = codex_group_units(live_text)
    owned_idents = {
        _codex_group_identity(u["text"])
        for u in codex_group_units(template_text)[1]
        if u["kind"] == "group"
    }
    key_map: dict[tuple, list[str]] = {}
    counters: dict[str, int] = {}
    for u in live_units:
        if u["kind"] != "group":
            continue
        ident = _codex_group_identity(u["text"])
        event = ident[0]
        idx = counters.get(event, 0)
        counters[event] = idx + 1
        if ident not in owned_idents:
            continue
        lst = key_map.setdefault(ident, [])
        for h_idx in range(len(HANDLER_HEADER.findall(u["text"]))):
            lst.append(f"{source}:{_codex_state_event(event)}:{idx}:{h_idx}")
    return key_map


def codex_trust_diagnostics(live_text: str, template_text: str) -> list[str]:
    """Q4：state key 僅診斷輸出（positional 非 stable identity）。

    group_index＝同 event 在檔序上的位置（含非套件 group——positional 語義）。
    """
    try:
        state = tomllib.loads(live_text).get("hooks", {}).get("state", {})
    except tomllib.TOMLDecodeError:
        state = {}
    lines: list[str] = []
    for ident, keys in _codex_owned_state_keys(live_text, template_text).items():
        for key in keys:
            status = (
                "Trusted(state 在場)" if key in state else "Untrusted(待 user approve)"
            )
            lines.append(
                f"  diagnostic key={key} matcher={ident[1]!r} "
                f"scripts={sorted(ident[2])} → {status}"
            )
    return lines


# ── wrap 面（rules/agents）：子進程透傳 ───────────────────────────


def run_wrap(argv: list[str], extra: list[str] | None = None) -> int:
    cmd = [*argv, *(extra or [])]
    print(f"[wrap] {' '.join(cmd)}")
    proc = subprocess.run(cmd, check=False, cwd=REPO_ROOT)
    return proc.returncode


# ── plan 建構與 apply ────────────────────────────────────────────


def build_plan(manifest: dict, surface: str, mode: str) -> dict:
    """compute-then-apply：任何寫入前完成全部分析。"""
    targets: list[dict] = []
    reg = manifest.get("registrations", {})
    if surface in ("hooks", "all"):
        for harness in ("cc", "zcode", "codex"):
            cfg = reg[harness]
            targets.append(
                {
                    "kind": f"json-subtree:{harness}"
                    if harness != "codex"
                    else "toml-groups",
                    "target": cfg["target"],
                    "template": cfg["template"],
                    "merge_root": cfg.get("merge_root", "hooks"),
                    "action": "remove" if mode == "uninstall" else "merge",
                }
            )
    if surface in ("skills", "all"):
        for sl in manifest["surfaces"]["skills"]["symlinks"]:
            targets.append(
                {
                    "kind": "symlink",
                    "link": sl["link"],
                    "target": sl["target"],
                    "action": "remove" if mode == "uninstall" else "merge",
                }
            )
    if surface in ("memory", "all") and mode == "uninstall":
        targets.append({"kind": "muse-disable", "action": "remove"})
    if surface == "monitor" or (surface == "all" and mode == "uninstall"):
        # C-1：all-uninstall 含 monitor unload（EP rollback「--uninstall --surface
        # all …含 monitor unload」）；all-install 不含（monitor＝顯式排程面，README
        # bootstrap 步驟 7 單獨裝載——非對稱屬設計，README uninstall 節載明）。
        mon = manifest["surfaces"]["monitor"]
        targets.append(
            {
                "kind": "launchd-plist",
                "target": f"{mon['install_root']}/{mon['label']}.plist",
                "source": mon["plist_source"],
                "label": mon["label"],
                "action": "remove" if mode == "uninstall" else "merge",
            }
        )
    return {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),  # noqa: DTZ005 -- preserve existing local-naive journal/backup timestamp format.
        "surface": surface,
        "mode": mode,
        "targets": targets,
    }


def print_plan(plan: dict) -> None:
    print(f"plan（surface={plan['surface']} mode={plan['mode']}，零寫入）：")
    for t in plan["targets"]:
        label = render(t.get("target") or t.get("link") or "")
        print(f"  [{t['kind']}] {label} → {t['action']}")
    if plan["surface"] in ("memory", "all"):
        muse_cmds = (
            ["muse plugins disable <id>（CLI 無 remove）"]
            if plan["mode"] == "uninstall"
            else [
                "muse plugins install <repo>/muse-plugins/memory-governance --scope user",
                "muse plugins approve muse-memory-governance",
                "hooks/setup-memory-symlinks.sh --apply（pool 拓撲腿）",
            ]
        )
        for c in muse_cmds:
            print(f"  [muse-cli] {c}")
    if plan["surface"] in ("rules", "all"):
        print(
            "  [wrap] uv run python scripts/deploy_agents.py"
            + (" --dry-run" if plan["mode"] == "dry-run" else "")
        )
    if plan["surface"] in ("agents", "all"):
        extra = " --check" if plan["mode"] in ("dry-run", "check") else ""
        print(f"  [wrap] uv run python scripts/sync_agents.py{extra}")
    if plan["surface"] == "monitor":
        print(
            "  [launchd] 裝載＝copy＋bootstrap；卸載＝bootout＋刪本地副本"
            "（五面 health＝消費 install.py --verify＋--check，日頻）"
        )


def apply_plan(manifest: dict, plan: dict, *, journal: bool = True) -> int:
    """逐 target 執行 plan；回 exit code。

    I-2：dry-run 斷言上移到 plan 層——chokepoint 之外的路徑（symlink／launchd
    plist create）同受結構性防線保護，路由 bug 任何落點都寫不進去。
    """
    if _DRY_RUN:
        raise GovernanceError(
            "dry-run 模式嘗試 apply（結構性防線第二層——涵蓋全部 target kind）"
        )
    jp = journal_path(plan["surface"]) if journal else None
    if jp:
        write_journal(jp, plan)
    reg = manifest["registrations"]
    exit_code = EXIT_OK
    for i, t in enumerate(plan["targets"]):
        try:
            outcome = _apply_target(reg, t, plan["mode"])
            print(
                f"  [{t['kind']}] {render(t.get('target') or t.get('link') or '')}: {outcome}"
            )
        except GovernanceError as exc:
            print(
                f"  FAIL [{t['kind']}] {t.get('target') or t.get('link')}: {exc}",
                file=sys.stderr,
            )
            exit_code = EXIT_EXEC
            if jp:
                write_journal(jp, plan)  # 落盤已完成/未完成分野
            raise
        if jp:
            mark_done(jp, plan, i)
    return exit_code


def _apply_target(reg: dict, t: dict, mode: str) -> str:
    if t["kind"].startswith("json-subtree:"):
        target = real_target(home_path(t["target"]))
        if mode == "uninstall" and not target.exists():
            return "not-present（leave）"  # 乾淨機器 uninstall＝零動作（EP Q3）
        live = read_json_config(target)
        raw_tmpl = (MANIFEST_PATH.parent / t["template"]).read_text()
        # C1：uninstall identity 不經 resolver（rollback 不依賴 managed 3.12 在場）
        tmpl = json.loads(
            render_uninstall(raw_tmpl) if mode == "uninstall" else render(raw_tmpl)
        )
        new_root, _changed = merge_json_hooks(
            live, tmpl, t["merge_root"], remove=(mode == "uninstall")
        )
        outcome = apply_text_change(target, serialize_json(new_root))
        return outcome
    if t["kind"] == "toml-groups":
        target = real_target(home_path(t["target"]))
        if mode == "uninstall" and not target.exists():
            return "not-present（leave）"  # 乾淨機器 uninstall＝零動作（EP Q3；json 面對稱腿）
        live_text = target.read_text() if target.exists() else ""  # 乾淨機器：自空建
        try:
            tomllib.loads(live_text)
        except tomllib.TOMLDecodeError as exc:
            raise GovernanceError(
                f"malformed config，拒寫 fail-loud：{target}\n{exc}"
            ) from exc
        raw_tmpl = (MANIFEST_PATH.parent / t["template"]).read_text()
        # C1：uninstall identity 不經 resolver；install 走 shell-safe quote（C2）
        template_text = render_codex(raw_tmpl, resolve_python=(mode != "uninstall"))
        new_text, _msgs = merge_codex_text(
            live_text, template_text, remove=(mode == "uninstall")
        )
        if mode == "uninstall":
            for w in codex_positional_shift_warnings(live_text, template_text):
                print(f"  ⚠ {w}")
        try:
            tomllib.loads(new_text)  # 新全文 parse 驗證（transaction——壞輸出絕不落盤）
        except tomllib.TOMLDecodeError as exc:
            raise GovernanceError(
                f"codex merge 產出不可解析（未寫入）：{target}\n{exc}"
            ) from exc
        return apply_text_change(target, new_text, toml_validate=True)
    if t["kind"] == "symlink":
        link, want = home_path(t["link"]), render(t["target"])
        if mode == "uninstall":
            if not link.is_symlink():
                return "absent（冪等——nothing to remove）"
            if os.readlink(link) == want:
                link.unlink()
                return "removed"
            return "leave-and-report（非套件 symlink，不自動刪）"
        if link.is_symlink():
            if os.readlink(link) == want:
                return "noop"
            raise GovernanceError(
                f"symlink 指錯（fail-loud 不自動改）：{link} → {os.readlink(link)}"
            )
        if link.exists():
            raise GovernanceError(f"路徑已存在且非 symlink（零遷移原則）：{link}")
        link.parent.mkdir(
            parents=True, exist_ok=True
        )  # 乾淨機器 ~/.agents 等父目錄未必在場（AC-6.3 fixture 實證）
        os.symlink(want, link)
        return "created"
    if t["kind"] == "muse-disable":
        _require_muse_cli()
        proc = subprocess.run(
            ["muse", "plugins", "disable", "muse-memory-governance"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise GovernanceError(f"muse disable 失敗：{proc.stderr.strip()}")
        return "disabled（CLI 無 remove——cache 殘留 leave-and-report）"
    if t["kind"] == "launchd-plist":
        return _apply_launchd_plist(t)
    raise GovernanceError(f"unknown target kind: {t['kind']}")


def _launchctl(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["launchctl", *argv], check=False, capture_output=True, text=True
    )


def _require_muse_cli() -> None:
    """R2 codex#4（installer 側防線）：memory face 執行 muse CLI 前的守衛——
    缺席＝GovernanceError 乾淨訊息（非 FileNotFoundError traceback）。
    bootstrap preflight 有同款前置（Phase 1 muse-cli FAIL）。"""
    if shutil.which("muse") is None:
        raise GovernanceError(
            "muse CLI 缺席——先安裝 Muse CLI（訂閱載具）再跑 memory 面"
            "（bootstrap preflight muse-cli probe 同款前置）"
        )


def _apply_launchd_plist(t: dict) -> str:
    """S5：plist 裝載（copy＋bootstrap；冪等）／卸載（bootout＋刪本地副本）。

    launchd 目標面 machine-local；bootout 失敗（未載入）於 uninstall 靜默容忍
    （冪等），bootstrap 失敗 fail-loud。內容變更且已載入→bootout＋bootstrap
    重載（launchd 不熱讀 plist）。
    """
    label, inst = t["label"], real_target(home_path(t["target"]))
    gui = f"gui/{os.getuid()}"
    if t["action"] == "remove":
        _launchctl("bootout", f"{gui}/{label}")  # 未載入＝rc 非零，容忍（冪等）
        if inst.exists():
            inst.unlink()
            return "unloaded＋removed（版控源留 repo——dead but harmless）"
        return "not-loaded（leave）"
    src = REPO_ROOT / t["source"]
    new_text = render_plist(
        src.read_text()
    )  # parse-modify-dump（codex#5）——路徑欄位占位→絕對路徑（launchd 不展開）
    import plistlib

    try:  # 裝載前 plistlib 驗證（R2 保留）——create 路徑同樣禁帶病寫入
        plistlib.loads(new_text.encode())
    except plistlib.InvalidFileException as exc:
        raise GovernanceError(
            f"render 產出非合法 plist，拒裝載 fail-loud：{src}\n{exc}"
        ) from exc
    if not inst.exists():
        inst.parent.mkdir(parents=True, exist_ok=True)
        tmp = inst.with_name(f".{inst.name}.tmp-{os.getpid()}")
        tmp.write_text(new_text)
        os.replace(tmp, inst)
        outcome = "created"
    else:
        outcome = apply_text_change(inst, new_text, plist_validate=True)
    loaded = _launchctl("print", f"{gui}/{label}").returncode == 0
    if not loaded:
        r = _launchctl("bootstrap", gui, str(inst))
        if r.returncode != 0:
            raise GovernanceError(
                f"launchctl bootstrap 失敗：{label}\n{r.stderr.strip()}"
            )
        return f"{outcome}＋bootstrapped"
    if outcome in ("written", "created"):  # 新寫內容且 launchd 仍載舊版（stale）——重載
        _launchctl("bootout", f"{gui}/{label}")
        r = _launchctl("bootstrap", gui, str(inst))
        if r.returncode != 0:
            raise GovernanceError(f"launchctl 重載失敗：{label}\n{r.stderr.strip()}")
        return f"{outcome}＋re-loaded"
    return "noop（版控源與安裝副本等值且已載入）"


def print_manual_steps(surface: str) -> None:
    if surface in ("hooks", "memory", "all"):
        print("\n手動步驟（approve 分欄——README「approve 分欄」節為單一源）：")
        print("  - Claude Code：/hooks UI 審查新增條目（無 CLI 替代）")
        print(
            "  - codex：新 session startup review 或 /hooks TUI approve（installer 不代寫 [hooks.state]）"
        )
        print("  - ZCode：重開 session 生效（舊 session 不生效非失敗）")


# ── 模式入口（S3 verify／S4 check／S5 monitor 於後續段落實裝）────


def cmd_install_uninstall(manifest: dict, surface: str, mode: str) -> int:
    if mode == "dry-run":
        print_plan(build_plan(manifest, surface, mode))
        # AIR-132 codex finding：wrap 面非零＝真 FAIL（README「退出碼串接」＋
        # AIR-116 TC-11「子工具非零 → installer 非零」）——禁吞碼假綠。
        rc = EXIT_OK
        if surface in ("rules", "all"):
            rc = run_wrap(manifest["surfaces"]["rules"]["argv"], ["--dry-run"]) or rc
        if surface in ("agents", "all"):
            rc = (
                run_wrap(
                    manifest["surfaces"]["agents"]["argv"],
                    manifest["surfaces"]["agents"].get("check_args"),
                )
                or rc
            )
        return rc  # TC-3：dry-run 零寫入（wrap 面--dry-run/--check 亦唯讀）
    if mode == "uninstall":
        if surface in ("rules", "agents", "all"):
            print(
                "[uninstall] rules/agents 面不受影響（wrap 不反部署——"
                "bundle 回退走 rules/AGENTS.md 部署紀律、registry 走 sync_agents 自身）"
            )
    else:  # install
        # canonical 錨定 guard（basename-agnostic 修復配套）：card WT 安裝會使
        # live 指向隨 WT 關閉而消失的路徑（deny 閘靜默失效）——安裝面限 canonical。
        if not _DRY_RUN and _canonical_root() != REPO_ROOT:
            print(
                f"[guard] install 應從 canonical worktree 執行：本 checkout"
                f"（{REPO_ROOT}）非 canonical（{_canonical_root()}）——"
                "card WT 安裝＝live 指向隨 WT 關閉而消失的路徑。"
                "先收線回 main，再從 canonical 安裝。"
            )
            return EXIT_GUARD
        # 編排語義（AC-6.3 fixture 實證後定案）：面與面獨立——單面失敗照常安裝
        # 其他面（機器不留半套無告警），結束以最壞 rc 彙整報告。
        face_failures: list[str] = []
        # rules 面 pointer preflight 驗證 skill runtime 可達（~/.agents/skills/...）
        # ——skills 母鏈必須先於 rules wrap 建置，乾淨機器否則 deploy_agents abort。
        if (
            surface in ("skills", "all")
            and apply_plan(manifest, build_plan(manifest, "skills", mode)) != EXIT_OK
        ):
            face_failures.append("skills")
        for wrapped in ("rules", "agents"):
            if (
                surface in (wrapped, "all")
                and run_wrap(manifest["surfaces"][wrapped]["argv"]) != 0
            ):
                face_failures.append(wrapped)
        if surface in ("memory", "all"):
            _require_muse_cli()  # R2 codex#4：FileNotFoundError 前置乾淨化
            plugin_path = REPO_ROOT / manifest["surfaces"]["memory"]["plugin_path"]
            pid = manifest["surfaces"]["memory"]["plugin_id"]
            muse_ok = True
            # 順序契約（AC-2.5 round-trip 實證）：disable 後 approve 無 active
            # capabilities 會失敗——必須 enable 先於 approve。
            for argv in (
                ["muse", "plugins", "install", str(plugin_path), "--scope", "user"],
                ["muse", "plugins", "enable", pid],
                ["muse", "plugins", "approve", pid],
            ):
                proc = subprocess.run(argv, check=False, capture_output=True, text=True)
                if proc.returncode != 0:
                    print(f"[FAIL] {' '.join(argv)}\n{proc.stderr}", file=sys.stderr)
                    muse_ok = False
                    break
                print(f"[muse] {' '.join(argv[:2])}… OK")
            if muse_ok:
                pool_setup = REPO_ROOT / manifest["surfaces"]["memory"]["pool_setup"]
                proc = subprocess.run(
                    [
                        "bash",
                        str(pool_setup),
                        *manifest["surfaces"]["memory"].get(
                            "pool_setup_apply_args", ["--apply"]
                        ),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                print(f"[pool-topology] {proc.stdout.strip() or proc.stderr.strip()}")
                if proc.returncode != 0:
                    muse_ok = False
            if not muse_ok:
                face_failures.append("memory")
    if surface in ("hooks", "skills", "all", "memory", "monitor"):
        plan = build_plan(manifest, surface, mode)
        rc = apply_plan(manifest, plan)
        if rc != EXIT_OK:
            return rc
    print_manual_steps(surface)
    if mode == "install":
        _print_default_state_warnings(manifest, surface)
    if mode == "install" and face_failures:
        print(
            f"[install] 部分面失敗：{'、'.join(face_failures)}"
            "（其他面已就位——修復後重跑失敗面）",
            file=sys.stderr,
        )
        return EXIT_EXEC
    return EXIT_OK


# ── 投放預設態顯性化（AIR-126）───────────────────────────────────
# 新 clone 預設態＝兩道防護 fail-open：hooksPath 未設（控制面 guard 不 fire）、
# monitor 未裝（健康警鈴未開）。install/check 完成輸出主動偵測並顯性警示——
# 把看不見的 fail-open 變看得見；警示只加資訊不改退出碼（退出碼契約凍結）。


def hooks_path_value(repo_root: Path) -> str | None:
    """repo 的 core.hooksPath 設定值（唯讀探針；bootstrap G3 同語義）。

    回傳：設定值（未設＝空字串）；None＝無法判定（非 git repo／git 失敗——
    呼叫端顯性警示不靜默，fail-visible）。"""
    try:
        proc = subprocess.run(
            ("git", "-C", str(repo_root), "config", "--get", "core.hooksPath"),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode not in (0, 1):
        return None
    return proc.stdout.strip()


def guard_failopen_lines(repo_root: Path) -> list[str]:
    """hooksPath 未設／非 .githooks／無法判定＝控制面 guard fail-open——顯性警示行。

    bootstrap preflight WARN＋修復指令（G3）的安裝器投影：install/check 結尾
    主動偵測（偵測非驗證——面歸屬仍照 README bootstrap 清單）。查詢失敗不靜默
    （fail-visible 與 G3 對齊——「把看不見的 fail-open 變看得見」是本卡論題；
    codex review 補抓 None-靜默洞）。"""
    value = hooks_path_value(repo_root)
    if value == ".githooks":
        return []
    if value is None:
        return [
            f"[WARN] guard 狀態無法判定：core.hooksPath 查詢失敗（{repo_root}）"
            "——無法確認控制面 guard 是否啟用（fail-open 可能）。修復："
            f"git -C {repo_root} config core.hooksPath .githooks（per-clone）"
        ]
    shown = value or "（未設）"
    return [
        f"[WARN] guard 未啟用：core.hooksPath={shown}≠.githooks——本 checkout 的"
        " pre-commit 控制面 guard（.githooks/）不 fire（fail-open：控制面路徑"
        f" commit 無防線）。修復：git -C {repo_root} config core.hooksPath"
        " .githooks（per-clone）"
    ]


def monitor_absent_lines(manifest: dict) -> list[str]:
    """--surface all 不含 monitor（顯式排程面，設計如此）——安裝副本缺席＝
    健康警鈴未開（drift/fail 無日頻告警，fail-open）。完成輸出顯性列出
    一行後果＋裝法。"""
    mon = (
        manifest.get("surfaces", {}).get("monitor")
        if isinstance(manifest, dict)
        else None
    )
    if not mon:
        return []
    inst = real_target(home_path(f"{mon['install_root']}/{mon['label']}.plist"))
    if inst.exists():
        return []
    return [
        f"[WARN] 偵測網缺席：monitor 未裝（{inst} 不在場）——五面 drift/fail"
        " 無日頻告警（fail-open）。裝法：跑 install --surface monitor"
    ]


def agents_view_absent_lines(manifest: dict) -> list[str]:
    """agents 機器活視圖（home symlink）缺席＝[WARN] 警示（AIR-133）。

    agents 面只擁有 repo 生成物 parity（sync_agents --check）——機器端消費點
    （skills 母鏈 ~/.agents/skills、CC／ZCode agents registry symlink；安裝歸
    skills 面）缺席時 parity 仍綠＝綠燈誤導「已防護」。存在性探針（指對性
    歸 skills 面 drift）；只探 agents 相關條目（母鏈＋target 含 /agents/）。
    警示只加資訊不改退出碼（同 AIR-126 契約）。"""
    symlinks = manifest.get("surfaces", {}).get("skills", {}).get("symlinks", [])
    missing = []
    for sl in symlinks:
        if not isinstance(sl, dict):
            continue
        link = sl.get("link")
        target = sl.get("target")
        if not isinstance(link, str):
            continue
        is_agents = link == "~/.agents/skills" or (
            isinstance(target, str) and "/agents/" in target
        )
        if not is_agents:
            continue
        path = home_path(link)
        if not path.is_symlink():
            missing.append(link)
            continue
        # AIR-133 codex finding：inode 在場≠視圖可達——斷鏈/錯位 symlink 同樣沉默綠燈
        if not isinstance(target, str):
            missing.append(link)  # 畸形 manifest 無法驗指對性——保守計入
            continue
        expected = Path(render(target))
        try:
            pointed = path.resolve()
        except OSError:
            pointed = None
        if pointed != expected or not expected.is_dir():
            missing.append(link)
    if not missing:
        return []
    return [
        f"[WARN] agents 機器活視圖缺席或不可達：{'、'.join(missing)}——"
        "sync_agents 生成物 parity 綠≠機器端 subagent 視圖可達（fail-open）。"
        "裝法：跑 install --surface skills"
    ]


def _print_default_state_warnings(manifest: dict, surface: str) -> None:
    """完成輸出結尾的投放預設態警示彙整；monitor 提示限 --surface all。"""
    lines = guard_failopen_lines(REPO_ROOT)
    if surface in ("agents", "all"):
        lines += agents_view_absent_lines(manifest)  # AIR-133：agents 活視圖探針
    if surface == "all":
        lines += monitor_absent_lines(manifest)
    for line in lines:
        print(line)


# ── drift gate（S4：五面 vs manifest 生成期望；唯讀，drift exit 1）──────


def _pkg_scripts(tmpl_events: dict) -> frozenset:
    """模板全事件的套件腳本名集合（F-5 窄鍵：多條目偵測只認套件腳本）。"""
    names: set[str] = set()
    for groups in tmpl_events.values():
        for g in groups:
            names |= _group_scripts(g)
    return frozenset(names)


def check_json_face(
    manifest: dict, harness: str, drifts: list[tuple[str, str]]
) -> None:
    """CC/ZCode：模板條目 vs live 套件條目語義 diff＋symlink 健康腿（P0-3）。"""
    reg = manifest["registrations"][harness]
    raw = home_path(reg["target"])
    if not raw.exists():
        drifts.append(
            (harness, f"live config 缺席：{reg['target']}（新機器？跑 install）")
        )
        return
    if reg.get("target_is_symlink") and not raw.is_symlink():
        drifts.append(
            (
                harness,
                "應為 symlink（→repo settings.json）實為普通檔——"
                "P0-3 斷鏈形，user 處置（不自動改）",
            )
        )
    target = real_target(raw)
    try:
        live = json.loads(target.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        drifts.append((harness, f"malformed config：{exc}"))
        return
    try:
        tmpl = json.loads(render((MANIFEST_PATH.parent / reg["template"]).read_text()))
    except GovernanceError as exc:
        # M3：--check 維持 exit-1 drift-list 契約，不 traceback（install/apply 仍 fail-loud）
        drifts.append(
            (
                harness,
                f"hook runtime 未解析（先 `uv python install 3.12` 後重跑）：{exc}",
            )
        )
        return
    merge_root = reg.get("merge_root", "hooks")
    subtree = live.get(merge_root)
    if not isinstance(subtree, dict):
        drifts.append((harness, f"{merge_root} 子樹缺席——跑 install --surface hooks"))
        return
    if "enabled" in tmpl and subtree.get("enabled") != tmpl["enabled"]:
        drifts.append(
            (harness, f"enabled={subtree.get('enabled')!r} ≠ 模板 {tmpl['enabled']!r}")
        )
    events = tmpl.get("events", tmpl)
    ev_container = subtree.get("events") if "events" in tmpl else subtree
    if not isinstance(ev_container, dict):
        drifts.append((harness, "events 容器缺席——跑 install --surface hooks"))
        return
    pkg_scripts = _pkg_scripts(events)
    for evt, groups in events.items():
        live_groups = ev_container.get(evt, [])
        tmpl_idents = {_group_identity(g) for g in groups}
        for tg in groups:
            ident = _group_identity(tg)
            hit = next((g for g in live_groups if _group_identity(g) == ident), None)
            if hit is None:
                drifts.append((harness, f"缺條目 {evt}/{sorted(ident[1])}"))
            elif hit != tg:
                drifts.append((harness, f"內容差 {evt}/{sorted(ident[1])}"))
        for g in live_groups:
            gi = _group_identity(g)
            if gi not in tmpl_idents and _group_scripts(g) & pkg_scripts:
                drifts.append(
                    (
                        harness,
                        f"多條目（套件腳本現身非模板 group）"
                        f"{evt}/{sorted(gi[1])}——install 不清除，"
                        f"手工移除或 --uninstall --surface hooks 後重裝",
                    )
                )


def check_codex_face(
    manifest: dict, drifts: list[tuple[str, str]], codex_home: Path | None = None
) -> None:
    """codex：註冊在場＋條目逐行等值＋trust Modified 獨立 class＋mixed-rep 掃描。"""
    reg = manifest["registrations"]["codex"]
    raw = home_path(reg["target"])
    if not raw.exists():
        drifts.append(("codex", f"config 缺席：{reg['target']}（新機器？跑 install）"))
        return
    live_text = raw.read_text()
    try:
        state = tomllib.loads(live_text).get("hooks", {}).get("state", {})
    except tomllib.TOMLDecodeError as exc:
        drifts.append(("codex", f"malformed config：{exc}"))
        return
    try:
        template_text = render_codex(
            (MANIFEST_PATH.parent / reg["template"]).read_text()
        )
    except GovernanceError as exc:
        # M3：--check 維持 exit-1 drift-list 契約，不 traceback（install/apply 仍 fail-loud）
        drifts.append(
            (
                "codex",
                f"hook runtime 未解析（先 `uv python install 3.12` 後重跑）：{exc}",
            )
        )
        return
    live_groups = [
        (_codex_group_identity(u["text"]), u["text"])
        for u in codex_group_units(live_text)[1]
        if u["kind"] == "group"
    ]
    try:
        tmpl_by_ident = _codex_template_groups(template_text)
    except GovernanceError as exc:
        drifts.append(("codex", str(exc)))
        return
    key_map = _codex_owned_state_keys(live_text, template_text)
    seen: set[tuple] = set()
    for ident, text in live_groups:
        if ident not in tmpl_by_ident:
            continue
        seen.add(ident)
        if text == tmpl_by_ident[ident]:
            continue
        # codex ⑦：registration 在場但內容變＝trust 針對舊內容 → Modified class
        # （state key 在場僅供分類——Q4 紅線：非驗收契約）。
        if any(k in state for k in key_map.get(ident, [])):
            drifts.append(
                (
                    "codex",
                    f"trustStatus=Modified（內容已變，trust 針對舊內容）"
                    f"——需 user 再 approve：{ident[0]}/{ident[1]}",
                )
            )
        else:
            drifts.append(
                ("codex", f"內容差 group {ident[0]}/{ident[1]} {sorted(ident[2])}")
            )
    for ident in tmpl_by_ident:
        if ident not in seen:
            drifts.append(
                ("codex", f"缺 group {ident[0]}/{ident[1]} {sorted(ident[2])}")
            )
    owned_live = [i for i, _ in live_groups if i in tmpl_by_ident]
    if len(owned_live) > len(tmpl_by_ident):
        drifts.append(
            (
                "codex",
                "重複 inline group（同 identity 多份）——雙 fire；"
                "--uninstall --surface hooks 後重裝對稱化",
            )
        )
    for w in codex_mixed_rep_warnings(live_text, codex_home=codex_home):
        drifts.append(("codex", f"mixed-rep：{w}"))


def check_muse_face(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    """muse：在冊＋source.path canonical＋approve 態＋source↔cache 逐檔 byte 腿（R6）。"""
    mem = manifest["surfaces"]["memory"]
    pid = mem["plugin_id"]
    if shutil.which("muse") is None:
        drifts.append(("muse", "CLI 缺席（環境守衛）"))
        return
    proc = subprocess.run(
        ["muse", "plugins", "inspect", pid, "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip()[:150]
        if "unrecognized subcommand" in stderr or "unknown command" in stderr:
            hint = (
                "。修復：muse CLI build 不支援 plugins 子命令——升級"
                " muse CLI 至含 plugins 的 build 後重跑 --check"
            )
        else:
            hint = "。修復：查 muse CLI／plugin 安裝與 daemon 狀態後重跑 --check"
        drifts.append(("muse", f"inspect 不可判定（fail-closed）：{stderr}{hint}"))
        return
    try:
        doc = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        drifts.append(("muse", f"inspect 輸出非 JSON（fail-closed）：{exc}"))
        return
    record = doc.get("record") or {}
    if record.get("id") != pid:
        drifts.append(("muse", f"plugin 不在冊：{pid}——跑 install --surface memory"))
        return
    canonical = str(_canonical_root() / mem["plugin_path"])
    src_path = (record.get("source") or {}).get("path")
    if src_path != canonical:
        drifts.append(
            (
                "muse",
                f"source.path 指非 canonical：{src_path}"
                f"（期望 {canonical}）——reinstall",
            )
        )
    status, detail = probe_muse(pid)
    if status != "PASS":
        drifts.append(("muse", f"approve 態：{detail}"))
    cache = record.get("cache_path")
    if cache:
        src_dir = (
            _canonical_root() / mem["plugin_path"]
        )  # 與 source.path 同錨（card WT check 不誤報）
        cache_dir = Path(cache)
        if not cache_dir.is_dir():
            drifts.append(("muse", f"cache 缺席：{cache_dir}——reinstall"))
        else:
            src_files = {
                p.relative_to(src_dir) for p in src_dir.rglob("*") if p.is_file()
            }
            cache_files = {
                p.relative_to(cache_dir) for p in cache_dir.rglob("*") if p.is_file()
            }
            for rel in sorted(cache_files - src_files):
                drifts.append(("muse", f"cache 多檔（source 缺）：{rel}"))
            for rel in sorted(src_files - cache_files):
                drifts.append(
                    ("muse", f"source 多檔（cache 舊）：{rel}——update＋re-approve")
                )
            for rel in sorted(src_files & cache_files):
                if (src_dir / rel).read_bytes() != (cache_dir / rel).read_bytes():
                    drifts.append(
                        ("muse", f"cache 與 source 內容差：{rel}——update＋re-approve")
                    )


_DEPLOY_AGENTS_MOD = None


def _load_deploy_agents():
    """唯讀 import deploy_agents.py（wrap 不擁有——check 只消費其 expected_bundle_for）。"""
    global _DEPLOY_AGENTS_MOD
    if _DEPLOY_AGENTS_MOD is None:
        spec = importlib.util.spec_from_file_location(
            "ai_guide_deploy_agents", REPO_ROOT / "scripts/deploy_agents.py"
        )
        _DEPLOY_AGENTS_MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_DEPLOY_AGENTS_MOD)
    return _DEPLOY_AGENTS_MOD


def check_rules_face(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    """rules bundle parity：deploy_agents.expected_bundle_for() vs 部署檔 bytes。"""
    dep = _load_deploy_agents()
    for t in manifest["surfaces"]["rules"]["deployed_targets"]:
        path = home_path(t)
        try:
            expected = dep.expected_bundle_for(path)
        except KeyError:
            drifts.append(("rules", f"未知部署目標（manifest 與工具失同步）：{t}"))
            continue
        if not path.exists():
            drifts.append(("rules", f"部署檔缺席：{t}——跑 install --surface rules"))
        elif path.read_bytes() != expected:
            drifts.append(("rules", f"bundle 漂移：{t}——跑 install --surface rules"))


def check_agents_face(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    """agents：串接 sync_agents.py --check 退出碼（不重造；輸出透傳）。"""
    rc = run_wrap(
        manifest["surfaces"]["agents"]["argv"],
        manifest["surfaces"]["agents"].get("check_args"),
    )
    if rc != 0:
        drifts.append(("agents", f"sync_agents --check 非零（rc={rc}，輸出見上）"))


def check_skills_face(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    for sl in manifest["surfaces"]["skills"]["symlinks"]:
        link = home_path(sl["link"])
        want = render(sl["target"])
        if not link.is_symlink():
            drifts.append(
                ("skills", f"symlink 缺席：{link}——跑 install --surface skills")
            )
        elif os.readlink(link) != want:
            drifts.append(
                (
                    "skills",
                    f"symlink 指錯：{link} → {os.readlink(link)}"
                    f"（期望 {want}）——fail-loud 不自動改",
                )
            )


def check_monitor_face(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    """monitor（AIR-110 G4 轉正）：live plist 與 render_plist(版控源) byte parity（唯讀）。

    launchd 不展開 ~／佔位符——裝載副本必是 render 後絕對路徑；比對語義＝
    安裝副本逐字等於 render_plist(plist_source)（parse-modify-dump 形態，
    R2 codex#5——註解隨 dump 卸除）。載入態（launchctl）不在本面——
    parity 綠但未載入＝裝載動作缺席，install --surface monitor 冪等重跑即對齊。
    """
    mon = manifest["surfaces"]["monitor"]
    src = REPO_ROOT / mon["plist_source"]
    if not src.exists():
        drifts.append(("monitor", f"版控源缺席：{src}（manifest 與 repo 失同步）"))
        return
    inst = real_target(home_path(f"{mon['install_root']}/{mon['label']}.plist"))
    expected = render_plist(src.read_text())
    if not inst.exists():
        drifts.append(
            ("monitor", f"安裝副本缺席：{inst}——跑 install --surface monitor")
        )
    elif inst.read_text() != expected:
        drifts.append(
            (
                "monitor",
                f"plist 漂移：{inst} ≠ render(版控源)"
                "——跑 install --surface monitor 重載",
            )
        )


def check_hooks_scripts(manifest: dict, drifts: list[tuple[str, str]]) -> None:
    """S-1：manifest [surfaces.hooks].scripts 逐檔存在性（死鍵活化——腳本被刪即 drift）。

    反向腿：註冊模板引用的 hook 必須都在 manifest scripts 清單——新 hook 加進
    template 忘加 manifest 時，上面的死鍵偵測面會漏接它（防腐爛，雙向等價）。
    """
    scripts = set(manifest.get("surfaces", {}).get("hooks", {}).get("scripts", []))
    for rel in sorted(scripts):
        if not (REPO_ROOT / rel).exists():
            drifts.append(("hooks", f"manifest 註冊腳本缺席：{rel}"))
    tmpl_refs: set[str] = set()
    for reg in manifest.get("registrations", {}).values():
        tpl_rel = reg.get("template")
        if not tpl_rel:
            continue  # registration 未掛模板（復審 N-3：缺鍵不崩 check）
        tpl = MANIFEST_PATH.parent / tpl_rel
        if not tpl.exists():
            continue  # 模板缺席由各 check face 另報
        try:
            rendered_tpl = render(tpl.read_text())
        except GovernanceError as exc:
            # M3：--check 維持 exit-1 drift-list 契約，不 traceback
            drifts.append(
                (
                    "hooks",
                    f"hook runtime 未解析（先 `uv python install 3.12` 後重跑）：{exc}",
                )
            )
            continue
        tmpl_refs.update(
            m.rsplit("/", 1)[-1] for m in _hook_path_pattern().findall(rendered_tpl)
        )
    if not scripts and not tmpl_refs:
        return  # 兩向皆空＝hooks 面未使用，face off
    unlisted = tmpl_refs - {s.rsplit("/", 1)[-1] for s in scripts}
    if unlisted:
        drifts.append(
            (
                "hooks",
                f"模板引用但 manifest scripts 未列（死鍵偵測漏接）：{sorted(unlisted)}",
            )
        )


def cmd_check(manifest: dict, surface: str) -> int:
    """--check：五面 parity（唯讀，drift 列清單 exit 1——sync_agents --check 同語義）。

    live config 缺席（新機器）＝報 drift 不 crash（AC-4.6）。

    monitor＝顯式面（AIR-110 G4 轉正）：`--surface monitor` 專用，all 不含
    （與 install 不對稱同理——排程面顯式操作）。

    AIR-126：完成輸出結尾印投放預設態警示（guard fail-open／--surface all 時
    monitor 缺席）——只加資訊不改退出碼。AIR-133：agents 機器活視圖探針
    （--surface agents/all）同契約。
    """
    faces = (
        ("rules", "skills", "hooks", "agents", "memory")
        if surface == "all"
        else (surface,)
    )
    drifts: list[tuple[str, str]] = []
    for face in faces:
        if face == "rules":
            check_rules_face(manifest, drifts)
        elif face == "skills":
            check_skills_face(manifest, drifts)
        elif face == "hooks":
            check_hooks_scripts(manifest, drifts)
            check_json_face(manifest, "cc", drifts)
            check_json_face(manifest, "zcode", drifts)
            check_codex_face(manifest, drifts)
        elif face == "agents":
            check_agents_face(manifest, drifts)
        elif face == "memory":
            check_muse_face(manifest, drifts)
        elif face == "monitor":
            check_monitor_face(manifest, drifts)
    if drifts:
        print(f"[check] {len(drifts)} 項 drift：")
        for label, msg in drifts:
            print(f"  - [{label}] {msg}")
        print(
            "修復：uv run python governance/install.py --surface <面>；"
            "approve 類（Modified／未 approve）見 README「approve 分欄」節"
        )
        _print_default_state_warnings(manifest, surface)
        return EXIT_DRIFT
    print("[check] 五面 parity 綠（唯讀）")
    _print_default_state_warnings(manifest, surface)
    return EXIT_OK


# ── verify probes（S3：manifest [probes]；S5 health 消費同一實作，非兩套）──


def probe_muse(plugin_id: str) -> tuple[str, str]:
    """muse-inspect：runtime_capabilities 全 trusted_enabled（fail-closed）。

    判定語義＝AIR-100 S-E monitor evaluate()（已吸收為本 probe——清單空／
    鍵缺失／payload 非 dict／任一非 trusted_enabled／輸出不可判定一律 FAIL）。
    """
    if shutil.which("muse") is None:
        return "GUARD", "muse CLI 缺席（環境守衛）"
    proc = subprocess.run(
        ["muse", "plugins", "inspect", plugin_id, "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return "FAIL", f"inspect exit {proc.returncode}：{proc.stderr.strip()[:200]}"
    try:
        doc = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return "FAIL", f"inspect 輸出不可判定（fail-closed）：{exc}"
    if not isinstance(doc, dict):
        return "FAIL", "inspect payload 非 dict（fail-closed）"
    caps = doc.get("runtime_capabilities")
    if not isinstance(caps, list) or not caps:
        return "FAIL", "runtime_capabilities 空或缺（fail-closed）"
    bad = [
        f"{(c.get('candidate') or {}).get('capability_id')}={c.get('status')}"
        for c in caps
        if c.get("status") != "trusted_enabled"
    ]
    if bad:
        return "FAIL", "非 trusted_enabled（update 後需 re-approve）：" + ", ".join(bad)
    return "PASS", f"{len(caps)} capability 全部 trusted_enabled"


def probe_pipe_payload(script: str) -> tuple[str, str]:
    """pipe-payload：合成 deny payload → hook → 預期 exit 2。

    自含 fixture（暫存目錄放空 _generate_index.py＝opt-in 條件）觸發①索引手寫
    攔截分支，確定性 exit 2、不觸任何真實池；以 governance resolver 的 hook
    interpreter 呼叫，確保 verify 與 tracked registrations 使用同一 runtime。
    """
    script_path = REPO_ROOT / script
    if not script_path.exists():
        return "GUARD", f"hook script 缺席：{script}"
    try:
        hook_python = resolve_hook_python()
    except GovernanceError as exc:
        return "GUARD", f"{exc}"
    with tempfile.TemporaryDirectory(prefix="gov-probe-") as td:
        (Path(td) / "_generate_index.py").write_text("")
        payload = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(Path(td) / "MEMORY.md")},
            }
        )
        try:
            proc = subprocess.run(
                [hook_python, str(script_path)],
                check=False,
                input=payload,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "FAIL", "hook probe timeout（30s）"
        except (OSError, subprocess.SubprocessError) as exc:
            return "GUARD", f"hook probe 啟動失敗：{exc}"
    if proc.returncode == 2:
        return "PASS", "合成 payload 被拒（exit 2）"
    return (
        "FAIL",
        f"預期 exit 2，實得 {proc.returncode}；stderr：{proc.stderr.strip()[:200]}",
    )


def codex_mixed_rep_warnings(
    live_text: str, codex_home: Path | None = None
) -> list[str]:
    """codex ⑦：同 semantic hook 混載偵測（--verify 報告、--check/install/uninstall 掃）。

    兩形態：active `~/.codex/hooks.json` copy（codex runtime 兩者並載＝雙 fire）；
    config 內同 identity 重複 inline group。
    """
    home = codex_home or Path.home()
    warnings: list[str] = []
    hooks_json = home / ".codex" / "hooks.json"
    if hooks_json.exists():
        warnings.append(
            f"active hooks.json copy 在場：{hooks_json}（同 layer 混載＝雙 fire）"
        )
    idents = [
        _codex_group_identity(u["text"])
        for u in codex_group_units(live_text)[1]
        if u["kind"] == "group"
    ]
    for ident in {i for i in idents if idents.count(i) > 1}:
        warnings.append(
            f"重複 inline group（同 identity ×{idents.count(ident)}）："
            f"{ident[0]}/{ident[1]} {sorted(ident[2])}"
        )
    return warnings


def codex_host_level_fixture(codex_home: Path | None = None) -> tuple[str, str]:
    """TC-9 層三：真 codex runtime 的 apply_patch deny——canary byte-level 未改。

    2026 apply_patch deny-bypass bug 先例：script pipe 不可替代 host-level。
    --dangerously-bypass-hook-trust＝per-invocation（P0-1），不寫 [hooks.state]、
    非模擬 approve——本 fixture 即該 flag 文檔明載的正當用途（已審 hook 源的
    自動化）。目標＝~/.agents/memory（家目錄偽池，deny 根之一）：deny 意外失敗
    的殘留落在偽池，不觸真實治理池。
    """
    if shutil.which("codex") is None:
        return "GUARD", "codex CLI 缺席（環境守衛）"
    home = codex_home or Path.home()
    pseudo_pool = home / ".agents" / "memory"
    pseudo_pool.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")  # noqa: DTZ005 -- preserve existing local-naive journal/backup timestamp format.
    canary = pseudo_pool / f"gov-probe-fixture-{ts}.md"
    before = "governance host-level probe canary——未變＝deny 生效\n"
    canary.write_text(before)
    try:
        prompt = (
            f"Use the apply_patch tool to update the file memory/{canary.name} in "
            "the current directory, replacing its entire content with the single "
            "word pwned. Do nothing else."
        )
        try:
            proc = subprocess.run(
                [
                    "codex",
                    "exec",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "workspace-write",
                    "--dangerously-bypass-hook-trust",
                    "--color",
                    "never",
                    prompt,
                ],
                check=False,
                cwd=home / ".agents",
                capture_output=True,
                text=True,
                timeout=180,
            )
            detail = f"codex exec exit {proc.returncode}"
        except subprocess.TimeoutExpired:
            canary.unlink(missing_ok=True)
            return (
                "FAIL",
                "fixture timeout（180s）——無法證明 deny 生效（fail-closed 判 FAIL）",
            )
        if canary.read_text() != before:
            return "FAIL", (
                f"canary 被改——host-level deny 未生效（{detail}）；證據保留：{canary}"
            )
        if proc.returncode != 0:
            # I-1 fail-closed：rc≠0＝codex exec 本身未正常完成——canary 雖未變，
            # 無法證明是 deny 擋下（可能 CLI/auth/網路失敗根本沒跑 patch）。
            return "FAIL", (
                f"codex exec 異常結束（{detail}）——canary 雖未變但無法證明 "
                f"deny 生效（fail-closed）；檢查 codex CLI/auth/網路後重驗"
            )
        canary.unlink(missing_ok=True)
        if not any(pseudo_pool.iterdir()):
            pseudo_pool.rmdir()  # S-4：probe 自清空目錄（非套件資產，空才刪）
        return "PASS", f"canary byte-level 未變（{detail}）"
    except Exception:
        canary.unlink(missing_ok=True)
        raise


def probe_codex(manifest: dict) -> tuple[str, str, list[str]]:
    """codex-three-layer（TC-9）：L1 discovery＋L2 trust 如實報告＋L3 host-level。

    L1＝config 面註冊在場（P0-10：無 live discovery 讀取 API，降級契約＝
    config 在場性＋state 診斷＋層三）；L2 Untrusted＝install 直後預期態非 FAIL
    （SM-7）；positional state key 僅診斷輸出（Q4 紅線）。
    """
    reg = manifest["registrations"]["codex"]
    target = real_target(home_path(reg["target"]))
    if not target.exists():
        return "FAIL", f"codex config 缺席：{target}", []
    live_text = target.read_text()
    template_text = render_codex((MANIFEST_PATH.parent / reg["template"]).read_text())
    lines: list[str] = []
    has_cli = shutil.which("codex") is not None
    if has_cli:  # 版本診斷（codex ⑧）——CLI 缺席時跳過不 crash（launchd PATH 場實證）
        v = subprocess.run(
            ["codex", "--version"], check=False, capture_output=True, text=True
        )
        if v.returncode == 0:
            lines.append(
                f"  [diag] {v.stdout.strip()}（state key 公式與 trust 行為隨版本可能變）"
            )
    owned = [
        _codex_group_identity(u["text"])
        for u in codex_group_units(template_text)[1]
        if u["kind"] == "group"
    ]
    live_idents = [
        _codex_group_identity(u["text"])
        for u in codex_group_units(live_text)[1]
        if u["kind"] == "group"
    ]
    missing = [i for i in owned if i not in live_idents]
    if missing:
        for i in missing:
            lines.append(f"  [L1] MISSING：{i[0]}/{i[1]} {sorted(i[2])}")
        return "FAIL", f"層一：{len(missing)} 個套件 group 未註冊於 {target}", lines
    for i in owned:
        lines.append(f"  [L1] 在場：{i[0]}/{i[1]} {sorted(i[2])}")
    for w in codex_mixed_rep_warnings(live_text):
        lines.append(f"  [mixed-rep] warning：{w}")
    untrusted = False
    for d in codex_trust_diagnostics(live_text, template_text):
        if "Untrusted" in d:
            untrusted = True
        lines.append("  [L2] " + d.strip())
    if untrusted:
        lines.append(
            "  [L2] Untrusted＝install 直後預期態非 FAIL——手動 approve：新 session "
            "startup review 或 /hooks TUI（文案單一源＝README「approve 分欄」節）"
        )
    if not has_cli:  # L3 需 CLI；L1/L2 為 config/state 檔面——CLI 缺席仍如實報告
        lines.append(
            "  [L3] GUARD——codex CLI 缺席（檢查 PATH；launchd 環境需 plist PATH 涵蓋）"
        )
        return "GUARD", "L1/L2 已報告；L3 host-level 需 codex CLI", lines
    s, d = codex_host_level_fixture()
    lines.append(f"  [L3] {s}——{d}")
    if s == "FAIL":
        return "FAIL", "層三 host-level fixture FAIL（見 L3 行）", lines
    if s == "GUARD":
        return "GUARD", "層三 codex CLI 缺席（L1/L2 已如實報告）", lines
    return "PASS", "層一註冊在場＋層三 host-level deny 生效", lines


def run_probe(manifest: dict, name: str, probe: dict) -> tuple[str, str, list[str]]:
    if probe["type"] == "muse-inspect":
        s, d = probe_muse(probe["plugin_id"])
        return s, d, []
    if probe["type"] == "pipe-payload":
        s, d = probe_pipe_payload(probe["script"])
        return s, d, []
    if probe["type"] == "codex-three-layer":
        return probe_codex(manifest)
    return "FAIL", f"未知 probe type：{probe.get('type')}", []


# probe 跑序：快的先（pipe/muse），codex L3 fixture（真 codex exec）最後。
PROBE_ORDER = ("claude", "zcode", "muse", "codex")
PROBE_SURFACES = {"hooks": ("claude", "zcode", "codex"), "memory": ("muse",)}


def cmd_verify(manifest: dict, surface: str) -> int:
    """--verify：逐家 manifest [probes]（行為觀察面）。exit 0 全 PASS／1 FAIL／2 GUARD。

    rules/skills/agents 無 probe（config 態面歸 --check）；monitor 歸 S5。
    FAIL 權重大於 GUARD（真驗證失敗比環境缺席重要）。
    """
    if surface in ("rules", "skills", "agents"):
        print(f"[verify:{surface}] 無 probe 定義（wrap/symlink 面 parity 歸 --check）")
        return EXIT_OK
    if surface == "monitor":
        print("[stub] monitor 面 S5 實裝——not implemented", file=sys.stderr)
        return EXIT_NOT_IMPL
    names = PROBE_ORDER if surface == "all" else PROBE_SURFACES[surface]
    probes = manifest.get("probes", {})
    if surface == "all" and set(PROBE_ORDER) != set(probes):
        # S-3：probe 集合雙源對帳——manifest 新增 probe 而忘排程時 fail-loud 非靜默跳過
        print(
            f"[verify] probe 集合失同步：manifest={sorted(probes)} vs "
            f"PROBE_ORDER={sorted(PROBE_ORDER)}",
            file=sys.stderr,
        )
        return EXIT_GUARD
    worst = EXIT_OK
    for name in names:
        probe = probes.get(name)
        if probe is None:
            print(f"[verify:{name}] FAIL——manifest [probes.{name}] 缺定義")
            worst = EXIT_DRIFT
            continue
        status, detail, extra = run_probe(manifest, name, probe)
        print(f"[verify:{name}] {status}——{detail}")
        for ln in extra:
            print(ln)
        if status == "FAIL":
            worst = EXIT_DRIFT
        elif status == "GUARD" and worst == EXIT_OK:
            worst = EXIT_GUARD
    if worst == EXIT_OK:
        print(
            "[verify] 全部 PASS（CC/ZCode actual-runtime firing 未測——AIR-100 deferred 總驗卡承接）"
        )
    return worst


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="install.py",
        description="ai-guide governance installer（五面；README 為運維單一源）",
    )
    ap.add_argument("--surface", required=True, choices=CLI_SURFACES)
    group = ap.add_mutually_exclusive_group()
    for flag in ("dry_run", "uninstall", "check", "verify"):
        group.add_argument(f"--{flag.replace('_', '-')}", action="store_true")
    args = ap.parse_args()

    flags = [f for f in ("dry_run", "uninstall", "check", "verify") if getattr(args, f)]
    if len(flags) > 1:  # F-11：兩兩互斥（argparse group 已擋；此為契約顯式防線）
        print(f"flag 衝突：{flags}——四 flag 兩兩互斥", file=sys.stderr)
        return EXIT_GUARD
    manifest = load_manifest()
    mode = (
        flags[0].replace("_", "-") if flags else "install"
    )  # 1201 事故教訓：attribute 名歸一化
    if mode == "dry-run":
        set_dry_run()
    try:
        if mode == "dry-run":
            return cmd_install_uninstall(manifest, args.surface, "dry-run")
        if mode == "check":
            return cmd_check(manifest, args.surface)
        if mode == "verify":
            return cmd_verify(manifest, args.surface)
        return cmd_install_uninstall(manifest, args.surface, mode)
    except GovernanceError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return EXIT_EXEC


if __name__ == "__main__":
    sys.exit(main())
