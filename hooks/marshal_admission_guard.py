#!/usr/bin/env python3
r"""PreToolUse hook（ZCode/CC matcher `Edit|Write`；codex matcher `apply_patch`）：
marshal admission guard——per-repo marker profile 寫入准入閘（AIR-152 marker
泛化；前身 AIR-135.10＝ai-guide 控制面 canonical 隔離，行為等價保留）。

三態（opt-in marker，repo 根 `.agents/marshal-governance.json`）：
- absent——本 repo 不啟用，全放行（向下相容；未收編 repo 由
  scripts/agent_liveness_sweep.py --enrollment-root 增列可見面）
- valid——生效；invariant 兩級：
    wt     = canonical 主樹（任何 branch）寫入命中 profile 即 deny
             （ai-guide 現行控制面行為等價保留：self repo 的 patterns 單一源
             仍走 .githooks/control-plane-guard.sh --match-path，marker
             sourceRoots 為附加面）
    branch = canonical ∧ 當前 branch == marker trunk ∧ 命中才 deny
             （trunk 以外的 branch 於 canonical checkout 的寫入放行——
             正當出路仍是非 canonical 卡 WT）
  命中判定順序：marker 檔本身恆豁免（壞 profile 的修復出口）→ allowlist
  （regex search）命中放行 → sourceRoots（regex search，repo 相對 POSIX
  路徑；前綴語請錨定寫 `"^src/"`——未錨定 `"src/"` 以 search 語義會命中
  `docs/src/…` 任意含子串路徑）或（self repo）控制面 guard 命中即 deny。
- malformed——deny（fail-closed，禁 fail-open）：JSON 不可解析／schema 不符
  （protocol≠1、invariantLevel 非 branch|wt、trunk 缺、sourceRoots/allowlist
  非字串陣列、任一 pattern regex 語法錯——靜默失效即假保護）→ 本 repo 寫入
  一律 deny 指路修復（marker 檔本身除外）。

canonical 判定＝git-common-dir→PRIMARY（scripts/wt-open.sh:58-59 同款拓撲錨；
兩腿審查共識——棄 wt-identity.json 存在性判據：.agent-tmp gitignored lifecycle
receipt 可缺席可刪、wt-open 失敗也留痕，不是 authorization token）。marker 一律
以 canonical checkout（PRIMARY 根）為準讀取——repo 治理配置不隨 worktree 漂。
self repo 判定＝target repo common dir 與本 hook 所屬 repo common dir 相同
（同 repo 的跨 checkout／worktree 皆成立）；self 才有權共用控制面 guard
patterns（他 repo 的同名 rules/ 由 marker opt-in 決定是否受管，不再靠
self-gate 放行——AIR-152 以 marker 三態取代）。

faces（policy 共用、payload adapter 分開）：
- ZCode/CC：`tool_input.file_path`（Edit|Write lane）
- codex：apply_patch 標頭抽取（`*** Add/Update/Delete File:`／`*** Move to:`；
  adapter 形態照 codex_memory_path_deny.py）；多檔 patch 任一命中即整 call deny

流程：resolve（symlink／`../`／相對路徑——新檔以 nearest existing parent 定
worktree 錨）→ `git rev-parse --show-toplevel` → `--git-common-dir`→PRIMARY →
marker 三態（malformed deny／absent 放行）→ 非 canonical（卡 WT／ephemeral
WT）放行 → allowlist → invariant 級（branch 級加 branch==trunk 判定）→
sourceRoots／控制面 patterns 命中 deny。

deny 輸出：exit 2＋stderr 指路（跨 harness 慣例——ZCode exit 2 deny 已證、
codex exit 2 deny 官方文檔、CC exit 2 阻斷），stdout 併附 hookSpecificOutput
JSON 說明（ZCode dialect，照 zcode_agent_background_gate.py 形態）。deny
三段式：擋了什麼（座標＋worktree）／為什麼（canonical×invariant 判定）／
可 copy-paste 恢復命令（wt-open <卡id> --base <trunk>／--ephemeral）。
fail-open：任何例外 exit 0 放行＋stderr 診斷（既有慣例——本閘是 Marshal
admission guard 非防惡意 sandbox，crash 不得鎖死所有編輯；Bash redirect／
MCP write 不在本 hook 面，定位＝提高違規成本＋留審計跡，禁宣稱完整 write
security boundary）。**無 bypass env**（break-glass＝human 停 registration；
決策勿重辯）。
覆蓋：Edit/Write hook 家族不觸發於 subagent 寫入（ZCode 實證）——spawned
worker 在卡 WT 的寫入（理想形態）本就不經此閘。
hook runtime python 3.9——禁 3.10+ 語法。
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GUARD_REL = os.path.join(".githooks", "control-plane-guard.sh")
MARKER_REL = os.path.join(".agents", "marshal-governance.json")
MARKER_PROTOCOL = 1
VALID_LEVELS = ("branch", "wt")
GIT_BIN = shutil.which("git") or "/usr/bin/git"  # ZCode GUI 行程 PATH 窄——退 /usr/bin 絕對路徑
BASH_BIN = "/bin/bash"

# apply_patch 寫入座標抽取（形態照 codex_memory_path_deny.py——大小寫敏感、
# 無行首寬鬆匹配：hunk context 誤判 header 的 false positive 教訓）
PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
    re.MULTILINE,
)

DENY_HEADER_WT = "[Hook Blocked] 控制面路徑禁 canonical 主樹直寫（marshal admission guard）"
DENY_HEADER_BRANCH = "[Hook Blocked] trunk 直寫被拒——branch 級 invariant（marshal admission guard）"
DENY_HEADER_MALFORMED = "[Hook Blocked] marshal-governance marker 損毀——fail-closed（marshal admission guard）"


def extract_patch_paths(command):
    """從 patch 文本抽寫入座標（Add/Update/Delete File＋Move to；出現順序）。"""
    paths = []
    for m in PATCH_PATH_RE.finditer(command or ""):
        paths.append((m.group(1) or m.group(2)).strip())
    return paths


def _target_paths(data):
    """本 hook 轄面的寫入座標清單；非轄面工具回 None（哨兵——不檢查直接放行）。"""
    tool = data.get("tool_name")
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    if tool in ("Edit", "Write"):
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return []
        return [file_path]
    if tool == "apply_patch":
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            return []
        return extract_patch_paths(command)
    return None


def _resolve_target(raw, cwd):
    """相對路徑套 cwd 後 resolve（symlink／`../` 全正規化；不存在路徑保留字面）。"""
    p = Path(raw)
    if not p.is_absolute():
        p = Path(cwd) / p
    return p.resolve()


def _nearest_existing_dir(resolved):
    """新檔（不存在）以 nearest existing parent 定 worktree 錨；檔案目標退其父目錄。"""
    cur = resolved
    if cur.exists() and not cur.is_dir():
        cur = cur.parent
    while not cur.is_dir():
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent
    return cur


def _git(workdir, *args):
    return subprocess.run(
        [GIT_BIN, "-C", workdir, *args], capture_output=True, text=True, check=False
    )


def _git_toplevel(workdir):
    """worktree toplevel；不在 repo 內回 None。"""
    proc = _git(workdir, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out or None


def _git_common_dir(workdir):
    """絕對化 git common dir（舊 git 無 --path-format 時退手動 join——wt-open.sh:58 同款錨）。"""
    proc = _git(workdir, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if proc.returncode == 0:
        out = proc.stdout.strip()
        if out:
            return out
    proc = _git(workdir, "rev-parse", "--git-common-dir")
    if proc.returncode == 0:
        out = proc.stdout.strip()
        if out:
            p = Path(out)
            return str(p if p.is_absolute() else Path(workdir) / p)
    raise RuntimeError(f"git-common-dir 不可判定（{workdir}）")


def _git_branch(workdir):
    """當前 branch；detached HEAD 回 "HEAD"、判讀失敗回 None——兩者皆 ≠ trunk
    （branch 級豁免面；封閉 predicate 不確定即不擋）。"""
    proc = _git(workdir, "rev-parse", "--abbrev-ref", "HEAD")
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out or None


def load_profile(repo_root):
    """讀 canonical 根的 marker——回 (status, profile)；status ∈ absent/ok/malformed。

    schema：{"protocol":1,"trunk":"main","invariantLevel":"branch|wt",
             "sourceRoots":["…"],"allowlist":["…"]}；sourceRoots/allowlist
    省略視為空陣列，其餘鍵缺失或型不符＝malformed。
    """
    path = os.path.join(repo_root, MARKER_REL)
    if not os.path.isfile(path):
        return "absent", None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, ValueError):
        return "malformed", None
    if not isinstance(data, dict) or data.get("protocol") != MARKER_PROTOCOL:
        return "malformed", None
    if data.get("invariantLevel") not in VALID_LEVELS:
        return "malformed", None
    trunk = data.get("trunk")
    if not isinstance(trunk, str) or not trunk:
        return "malformed", None
    for key in ("sourceRoots", "allowlist"):
        val = data.get(key, [])
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            return "malformed", None
        for item in val:
            try:
                re.compile(item)
            except re.error:
                return "malformed", None  # 壞 regex＝該規則永不命中＝靜默失效——fail-closed
    return "ok", data


def _compile_patterns(items):
    """marker 條目 → compiled regex（load_profile 已驗 regex 語法——壞 pattern 在
    schema 層即 malformed；此處 try/except 僅 belt，正常路徑不觸）。"""
    pats = []
    for item in items:
        try:
            pats.append(re.compile(item))
        except re.error:
            pass
    return pats


def _matches_any(patterns, rel_posix):
    return any(p.search(rel_posix) for p in patterns)


def _matches_control_plane(hook_root, rel):
    """guard --match-path 子入口（self repo patterns 單一源）。1＝命中控制面；
    0／異常＝非命中。"""
    proc = subprocess.run(
        [BASH_BIN, str(hook_root / GUARD_REL), "--match-path", rel],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 1


def evaluate(raw_paths, cwd):
    """任一 target 命中 → hit dict；全數通過 → None。

    hit["kind"] ∈ "control-plane"（wt／branch invariant 命中）｜
    "marker-malformed"（profile 不可判讀，fail-closed）。
    例外由 main 的 fail-open 接住（exit 0 放行）。
    """
    hook_root = Path(__file__).resolve().parent.parent
    hook_common = None  # lazy——非 self repo 或 sourceRoots 已命中時不付那顆 git call
    for raw in raw_paths:
        resolved = _resolve_target(raw, cwd)
        base = _nearest_existing_dir(resolved)
        if base is None:
            continue
        toplevel = _git_toplevel(str(base))
        if not toplevel:
            continue
        common = _git_common_dir(toplevel)
        primary = os.path.dirname(common)
        rel = os.path.relpath(resolved, toplevel)
        rel_posix = rel.replace(os.sep, "/")
        if rel_posix == MARKER_REL.replace(os.sep, "/"):
            continue  # marker 檔本身恆豁免——壞 profile 的修復出口
        status, profile = load_profile(primary)
        if status == "malformed":
            return {
                "kind": "marker-malformed",
                "raw": raw,
                "resolved": resolved,
                "toplevel": toplevel,
                "primary": primary,
            }
        if status == "absent":
            continue  # opt-in 三態——無 marker＝本 repo 不啟用
        if os.path.realpath(toplevel) != os.path.realpath(primary):
            continue  # 非 canonical——卡 WT／ephemeral WT 放行
        if _matches_any(_compile_patterns(profile.get("allowlist", [])), rel_posix):
            continue
        if profile.get("invariantLevel") == "branch":
            if _git_branch(toplevel) != profile.get("trunk"):
                continue  # branch 級豁免：非 trunk branch 的 canonical checkout
        hit = _matches_any(_compile_patterns(profile.get("sourceRoots", [])), rel_posix)
        if not hit:
            if hook_common is None:
                hook_common = _git_common_dir(str(hook_root))
            if os.path.realpath(common) == os.path.realpath(hook_common):
                # self repo——控制面 patterns 單一源共用 guard script（ai-guide 現行面）
                hit = _matches_control_plane(hook_root, rel)
        if hit:
            return {
                "kind": "control-plane",
                "raw": raw,
                "resolved": resolved,
                "toplevel": toplevel,
                "primary": primary,
                "profile": profile,
            }
    return None


def _guidance(trunk):
    """deny 三段式第三段——可 copy-paste 恢復命令（trunk 由 marker profile 帶）。"""
    return (
        "寫入走非 canonical worktree：scripts/wt-open.sh <卡id> --base " + trunk
        + " 開卡 WT，或 scripts/wt-open.sh --ephemeral <name> --base " + trunk
        + " 快速分身（hotfix 亦走 --ephemeral，不白名單）；"
        "canonical 主樹（PRIMARY）留 " + trunk + "，編輯在卡 WT 完成後經 merge 收線。"
    )


def _deny(hit):
    resolved = hit["resolved"]
    toplevel = hit["toplevel"]
    if hit["kind"] == "marker-malformed":
        marker = os.path.join(hit["primary"], MARKER_REL)
        reason = (
            DENY_HEADER_MALFORMED + "。\n"
            "marker：" + marker + "\n"
            "（profile 不可判讀＝invariant 狀態未知，本 repo 寫入一律擋——"
            "marker 檔本身除外，修復出口保留）\n"
            "修復：直接編輯該 marker 修正 JSON/schema（protocol=" + str(MARKER_PROTOCOL)
            + "、invariantLevel=branch|wt、trunk 非空字串、sourceRoots/allowlist＝"
            "字串陣列），或刪除該檔即停用本閘。"
        )
    else:
        profile = hit["profile"]
        trunk = profile.get("trunk") if isinstance(profile, dict) else "main"
        if profile.get("invariantLevel") == "branch":
            header = DENY_HEADER_BRANCH
            why = "canonical ∧ branch==" + trunk + " ∧ 路徑命中 marker sourceRoots"
        else:
            header = DENY_HEADER_WT
            why = "canonical 主樹 × profile 命中（wt 級 invariant）"
        reason = (
            header + "。\n命中座標：" + str(resolved) + "\n"
            "（worktree：" + toplevel + "；判定：" + why + "）\n"
            + _guidance(trunk)
        )
    # stdout JSON 說明（ZCode hookSpecificOutput dialect，照 background gate 形態）；
    # 載荷機制＝exit 2＋stderr（三 harness 已證／文檔認可的 deny 形）
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    print(reason, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"[marshal_admission_guard] stdin parse error（fail-open 放行）: {exc}",
            file=sys.stderr,
        )
        return
    try:
        if not isinstance(data, dict):
            return
        paths = _target_paths(data)
        if not paths:
            return
        cwd = data.get("cwd")
        cwd = cwd if isinstance(cwd, str) and cwd else os.getcwd()
        hit = evaluate(paths, cwd)
        if hit is not None:
            _deny(hit)
    except Exception as exc:  # fail-open（既有慣例）——crash 不得鎖死所有編輯
        print(f"[marshal_admission_guard] fail-open: {exc!r}", file=sys.stderr)
        return


if __name__ == "__main__":
    main()
