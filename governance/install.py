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

if sys.version_info < (3, 11):
    print(
        "ai-guide governance installer 需要 Python 3.11+（tomllib）。\n"
        "請改用：uv run python governance/install.py …",
        file=sys.stderr,
    )
    sys.exit(2)

import argparse
import copy
import datetime
import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.toml"
REPO_TOKEN = "{{REPO}}"
JOURNAL_DIR = Path.home() / ".local/share/ai-guide/governance-plan-journal"
BAK_KEEP = 3
JOURNAL_KEEP = 10

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_GUARD = 2
EXIT_NOT_IMPL = 3
EXIT_EXEC = 4  # 執行錯誤（malformed／lost-update／子進程失敗）——journal 有線索

# P0-2 凍結：CC/ZCode live config 逐字重現參數（＋尾換行）。
SERIALIZE_PARAMS = {"indent": 2, "ensure_ascii": False}

HOOK_MARKER = "/ai-guide/hooks/"

_DRY_RUN = False  # 結構性防線：dry-run 模式下任何寫入 chokepoint 直接 raise（1201 事故教訓）


class GovernanceError(Exception):
    """fail-loud 執行錯誤（malformed config、lost-update、子進程失敗）。"""


def set_dry_run() -> None:
    global _DRY_RUN
    _DRY_RUN = True


# ── 基礎 helpers ─────────────────────────────────────────────────


def render(text: str) -> str:
    return text.replace(REPO_TOKEN, str(REPO_ROOT))


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
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = real.with_name(f"{real.name}.bak-{ts}-gov")
    shutil.copy2(real, bak)
    # 只 prune 自家後綴（他弧手工 bak 不入額度）；按 mtime 排序非檔名（1201 事故教訓——
    # 檔名排序把最新備份當最舊刪）。
    own = sorted((real.parent).glob(f"{real.name}.bak-*-gov"), key=lambda p: p.stat().st_mtime)
    for old in own[:-BAK_KEEP] if len(own) > BAK_KEEP else []:
        old.unlink(missing_ok=True)
    return bak


# ── 原子寫（temp＋parse 驗證＋preimage 對比＋os.replace）──────────


def apply_text_change(real: Path, new_text: str, *, toml_validate: bool = False) -> str:
    """唯一寫入 chokepoint。回 "noop"（byte-equal 零寫入零備份）或 "written"。

    通用 preimage 防線：寫入前 live 若變（codex runtime 寫 [hooks.state]、
    ZCode runtime 併發重寫 config——1201 事故實證）即 fail/retry。
    """
    if _DRY_RUN:
        raise GovernanceError("dry-run 模式嘗試寫入（結構性防線——路由 bug 不應能到這裡）")
    current = real.read_text()
    if current == new_text:
        return "noop"
    if toml_validate:
        try:
            tomllib.loads(current)  # live 可解析才護得起
        except tomllib.TOMLDecodeError as exc:
            raise GovernanceError(
                f"malformed config，拒寫 fail-loud：{real}\n{exc}"
            ) from exc
    backup_target(real)
    tmp = real.with_name(f".{real.name}.tmp-{os.getpid()}")
    tmp.write_text(new_text)
    if toml_validate:
        try:
            tomllib.loads(tmp.read_text())
        except tomllib.TOMLDecodeError as exc:
            tmp.unlink(missing_ok=True)
            raise GovernanceError(f"新全文 parse 驗證失敗（未寫入）：{real}\n{exc}") from exc
    if real.read_text() != current:
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
        joined = " ".join([str(h.get("command", ""))] + list(map(str, h.get("args", []))))
        for m in re.findall(r"/ai-guide/hooks/[\w.\-]+", joined):
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
    if not remove and "enabled" in package and subtree.get("enabled") != package["enabled"]:
        subtree["enabled"] = package["enabled"]
        changed = True
    events = package.get("events", package)
    # live event map 位置：zcode 子樹有 events 鍵；cc 子樹本體即 event map
    ev_container = subtree.setdefault("events", {}) if "events" in package else subtree
    for evt, tmpl_groups in events.items():
        groups = ev_container.setdefault(evt, [])
        for tg in tmpl_groups:
            ident = _group_identity(tg)
            idx = next((i for i, g in enumerate(groups) if _group_identity(g) == ident), None)
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
HANDLER_HEADER = re.compile(r"^\[\[hooks\.[A-Za-z]+\.hooks\]\]")
AI_GUIDE_COMMENT = "# ai-guide"


def _peel_leading_comments(lines: list[str], header_idx: int, zone_start: int) -> list[str]:
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
            if lead and last_holder[len(last_holder) - len(lead):] == lead:
                del last_holder[len(last_holder) - len(lead):]
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
    mm = re.search(r'^matcher = "(.*?)"$', unit_text, re.MULTILINE)
    scripts = frozenset(
        s.rsplit("/", 1)[-1] for s in re.findall(r"/ai-guide/hooks/[\w.\-]+", unit_text)
    )
    return (event, mm.group(1) if mm else None, scripts)


def merge_codex_text(live_text: str, template_text: str, *, remove: bool) -> tuple[str, list[str]]:
    """group 級 merge/uninstall；回 (new_text, 訊息清單)。identity 相符才動，他 family 禁碰。"""
    preamble, live_units = codex_group_units(live_text)
    _, tmpl_units = codex_group_units(template_text)
    tmpl_by_ident = {(_codex_group_identity(u["text"])): u["text"]
                     for u in tmpl_units if u["kind"] == "group"}
    if len(tmpl_by_ident) != sum(1 for u in tmpl_units if u["kind"] == "group"):
        raise GovernanceError("codex 模板內部 identity 碰撞（group 定義不唯一）——拒合併")
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
                messages.append(f"appended group: {ident[0]}/{ident[1]} {sorted(ident[2])}")
                out.append(text_)
    return preamble + "".join(out), messages


def codex_trust_diagnostics(live_text: str, template_text: str) -> list[str]:
    """Q4：state key 僅診斷輸出（positional 非 stable identity）。

    group_index＝同 event 在檔序上的位置（含非套件 group——positional 語義）。
    """
    source = f"{Path.home() / '.codex/config.toml'}"
    try:
        state = tomllib.loads(live_text).get("hooks", {}).get("state", {})
    except tomllib.TOMLDecodeError:
        state = {}
    _, tmpl_units = codex_group_units(template_text)
    owned_idents = {_codex_group_identity(u["text"]) for u in tmpl_units if u["kind"] == "group"}
    _, live_units = codex_group_units(live_text)
    lines: list[str] = []
    counters: dict[str, int] = {}
    for u in live_units:
        if u["kind"] != "group":
            continue
        event = _codex_group_identity(u["text"])[0]
        idx = counters.get(event, 0)
        counters[event] = idx + 1
        ident = _codex_group_identity(u["text"])
        if ident not in owned_idents:
            continue
        handlers = len(HANDLER_HEADER.findall(u["text"]))
        matcher = ident[1]
        scripts = sorted(ident[2])
        for h_idx in range(handlers):
            key = f"{source}:{event.lower()}:{idx}:{h_idx}"
            status = "Trusted(state 在場)" if key in state else "Untrusted(待 user approve)"
            lines.append(f"  diagnostic key={key} matcher={matcher!r} scripts={scripts} → {status}")
    return lines


# ── wrap 面（rules/agents）：子進程透傳 ───────────────────────────


def run_wrap(argv: list[str], extra: list[str] | None = None) -> int:
    cmd = [*argv, *(extra or [])]
    print(f"[wrap] {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT)
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
                    "kind": f"json-subtree:{harness}" if harness != "codex" else "toml-groups",
                    "target": cfg["target"],
                    "template": cfg["template"],
                    "merge_root": cfg.get("merge_root", "hooks"),
                    "action": "remove" if mode == "uninstall" else "merge",
                }
            )
    if surface in ("skills", "all"):
        for sl in manifest["surfaces"]["skills"]["symlinks"]:
            targets.append({"kind": "symlink", "link": sl["link"], "target": sl["target"],
                            "action": "remove" if mode == "uninstall" else "merge"})
    if surface == "memory" and mode == "uninstall":
        targets.append({"kind": "muse-disable", "action": "remove"})
    return {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "surface": surface, "mode": mode, "targets": targets}


def print_plan(plan: dict) -> None:
    print(f"plan（surface={plan['surface']} mode={plan['mode']}，零寫入）：")
    for t in plan["targets"]:
        label = render(t.get("target") or t.get("link") or "")
        print(f"  [{t['kind']}] {label} → {t['action']}")
    if plan["surface"] in ("memory", "all"):
        muse_cmds = (
            ["muse plugins disable <id>（CLI 無 remove）"]
            if plan["mode"] == "uninstall"
            else ["muse plugins install <repo>/muse-plugins/memory-governance --scope user",
                  "muse plugins approve muse-memory-governance",
                  "hooks/setup-memory-symlinks.sh --apply（pool 拓撲腿）"]
        )
        for c in muse_cmds:
            print(f"  [muse-cli] {c}")
    if plan["surface"] in ("rules", "all"):
        print("  [wrap] uv run python scripts/deploy_agents.py" + (" --dry-run" if plan["mode"] == "dry-run" else ""))
    if plan["surface"] in ("agents", "all"):
        extra = " --check" if plan["mode"] in ("dry-run", "check") else ""
        print(f"  [wrap] uv run python scripts/sync_agents.py{extra}")


def apply_plan(manifest: dict, plan: dict, *, journal: bool = True) -> int:
    """逐 target 執行 plan；回 exit code。"""
    jp = journal_path(plan["surface"]) if journal else None
    if jp:
        write_journal(jp, plan)
    reg = manifest["registrations"]
    exit_code = EXIT_OK
    for i, t in enumerate(plan["targets"]):
        try:
            outcome = _apply_target(reg, t, plan["mode"])
            print(f"  [{t['kind']}] {render(t.get('target') or t.get('link') or '')}: {outcome}")
        except GovernanceError as exc:
            print(f"  FAIL [{t['kind']}] {t.get('target') or t.get('link')}: {exc}", file=sys.stderr)
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
        live = read_json_config(target)
        tmpl = json.loads(render((MANIFEST_PATH.parent / t["template"]).read_text()))
        new_root, _changed = merge_json_hooks(
            live, tmpl, t["merge_root"], remove=(mode == "uninstall")
        )
        outcome = apply_text_change(target, serialize_json(new_root))
        return outcome
    if t["kind"] == "toml-groups":
        target = real_target(home_path(t["target"]))
        live_text = target.read_text()
        try:
            tomllib.loads(live_text)
        except tomllib.TOMLDecodeError as exc:
            raise GovernanceError(f"malformed config，拒寫 fail-loud：{target}\n{exc}") from exc
        template_text = render((MANIFEST_PATH.parent / t["template"]).read_text())
        new_text, _msgs = merge_codex_text(live_text, template_text, remove=(mode == "uninstall"))
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
            if link.is_symlink() and os.readlink(link) == want:
                link.unlink()
                return "removed"
            return "leave-and-report（非套件 symlink，不自動刪）"
        if link.is_symlink():
            if os.readlink(link) == want:
                return "noop"
            raise GovernanceError(f"symlink 指錯（fail-loud 不自動改）：{link} → {os.readlink(link)}")
        if link.exists():
            raise GovernanceError(f"路徑已存在且非 symlink（零遷移原則）：{link}")
        os.symlink(want, link)
        return "created"
    if t["kind"] == "muse-disable":
        proc = subprocess.run(["muse", "plugins", "disable", "muse-memory-governance"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise GovernanceError(f"muse disable 失敗：{proc.stderr.strip()}")
        return "disabled（CLI 無 remove——cache 殘留 leave-and-report）"
    raise GovernanceError(f"unknown target kind: {t['kind']}")


def print_manual_steps(surface: str) -> None:
    if surface in ("hooks", "memory", "all"):
        print("\n手動步驟（approve 分欄——README「approve 分欄」節為單一源）：")
        print("  - Claude Code：/hooks UI 審查新增條目（無 CLI 替代）")
        print("  - codex：新 session startup review 或 /hooks TUI approve（installer 不代寫 [hooks.state]）")
        print("  - ZCode：重開 session 生效（舊 session 不生效非失敗）")


# ── 模式入口（S3 verify／S4 check／S5 monitor 於後續段落實裝）────


def cmd_install_uninstall(manifest: dict, surface: str, mode: str) -> int:
    if mode == "dry-run":
        print_plan(build_plan(manifest, surface, mode))
        if surface in ("rules", "all"):
            run_wrap(manifest["surfaces"]["rules"]["argv"], ["--dry-run"])
        if surface in ("agents", "all"):
            run_wrap(manifest["surfaces"]["agents"]["argv"],
                     manifest["surfaces"]["agents"].get("check_args"))
        return EXIT_OK  # TC-3：dry-run 零寫入（wrap 面--dry-run/--check 亦唯讀）
    if mode == "uninstall":
        if surface in ("rules", "agents", "all"):
            print("[uninstall] rules/agents 面不受影響（wrap 不反部署——"
                  "bundle 回退走 rules/AGENTS.md 部署紀律、registry 走 sync_agents 自身）")
    else:  # install
        for wrapped in ("rules", "agents"):
            if surface in (wrapped, "all"):
                rc = run_wrap(manifest["surfaces"][wrapped]["argv"])
                if rc != 0:
                    return EXIT_EXEC
        if surface in ("memory", "all"):
            plugin_path = REPO_ROOT / manifest["surfaces"]["memory"]["plugin_path"]
            pid = manifest["surfaces"]["memory"]["plugin_id"]
            for argv in (["muse", "plugins", "install", str(plugin_path), "--scope", "user"],
                         ["muse", "plugins", "approve", pid]):
                proc = subprocess.run(argv, capture_output=True, text=True)
                if proc.returncode != 0:
                    print(f"[FAIL] {' '.join(argv)}\n{proc.stderr}", file=sys.stderr)
                    return EXIT_EXEC
                print(f"[muse] {' '.join(argv[:2])}… OK")
            pool_setup = REPO_ROOT / manifest["surfaces"]["memory"]["pool_setup"]
            proc = subprocess.run(["bash", str(pool_setup), "--apply"],
                                  capture_output=True, text=True)
            print(f"[pool-topology] {proc.stdout.strip() or proc.stderr.strip()}")
            if proc.returncode != 0:
                return EXIT_EXEC
    if surface == "monitor":
        print("[stub] monitor 面 S5 實裝——not implemented", file=sys.stderr)
        return EXIT_NOT_IMPL
    if surface in ("hooks", "skills", "all", "memory"):
        plan = build_plan(manifest, surface, mode)
        rc = apply_plan(manifest, plan)
        if rc != EXIT_OK:
            return rc
    print_manual_steps(surface)
    return EXIT_OK


def cmd_check(manifest: dict, surface: str) -> int:
    print("[stub] --check S4 實裝——not implemented", file=sys.stderr)
    return EXIT_NOT_IMPL


def cmd_verify(manifest: dict, surface: str) -> int:
    print("[stub] --verify S3 實裝——not implemented", file=sys.stderr)
    return EXIT_NOT_IMPL


def main() -> int:
    ap = argparse.ArgumentParser(prog="install.py", description="ai-guide governance installer（五面；README 為運維單一源）")
    ap.add_argument("--surface", required=True,
                    choices=["rules", "skills", "hooks", "agents", "memory", "monitor", "all"])
    group = ap.add_mutually_exclusive_group()
    for flag in ("dry_run", "uninstall", "check", "verify"):
        group.add_argument(f"--{flag.replace('_', '-')}", action="store_true")
    args = ap.parse_args()

    flags = [f for f in ("dry_run", "uninstall", "check", "verify") if getattr(args, f)]
    if len(flags) > 1:  # F-11：兩兩互斥（argparse group 已擋；此為契約顯式防線）
        print(f"flag 衝突：{flags}——四 flag 兩兩互斥", file=sys.stderr)
        return EXIT_GUARD
    manifest = load_manifest()
    mode = flags[0].replace("_", "-") if flags else "install"  # 1201 事故教訓：attribute 名歸一化
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
