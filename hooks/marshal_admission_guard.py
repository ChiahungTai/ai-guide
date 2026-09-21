#!/usr/bin/env python3
r"""PreToolUse hook（ZCode/CC matcher `Edit|Write`；codex matcher `apply_patch`）：
marshal admission guard——控制面路徑 × canonical 主樹 → deny（AIR-135.10）。

把 AIR-106 控制面隔離閘從 commit 時點前移到「編輯當下」：控制面檔案的編輯
須走非 canonical worktree（scripts/wt-open.sh 卡 WT／--ephemeral 快速分身），
canonical 主樹（PRIMARY，live symlink 即時生效面）留 main。

canonical 判定＝git-common-dir→PRIMARY（scripts/wt-open.sh:58-59 同款拓撲錨；
兩腿審查共識——棄 wt-identity.json 存在性判據：.agent-tmp gitignored lifecycle
receipt 可缺席可刪、wt-open 失敗也留痕，不是 authorization token）。

faces（policy 共用、payload adapter 分開）：
- ZCode/CC：`tool_input.file_path`（Edit|Write lane）
- codex：apply_patch 標頭抽取（`*** Add/Update/Delete File:`／`*** Move to:`；
  adapter 形態照 codex_memory_path_deny.py）；多檔 patch 任一命中即整 call deny

流程：resolve（symlink／`../`／相對路徑——新檔以 nearest existing parent 定
worktree 錨）→ `git rev-parse --show-toplevel` → `--git-common-dir`→PRIMARY →
toplevel≠PRIMARY（卡 WT／ephemeral WT）放行 → 相等（canonical）→ repo
self-gate（common dir 與本 hook 所屬 ai-guide repo 不同＝N/A 放行——user-level
hook 不殺其他 repo 的同名 rules/）→ `.githooks/control-plane-guard.sh
--match-path <repo-relative>`（patterns 單一源共用——exit 0 非控制面放行、
1 命中 deny）。

deny 輸出：exit 2＋stderr 指路（跨 harness 慣例——ZCode exit 2 deny 已證、
codex exit 2 deny 官方文檔、CC exit 2 阻斷），stdout 併附 hookSpecificOutput
JSON 說明（ZCode dialect，照 zcode_agent_background_gate.py 形態）。
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
GIT_BIN = shutil.which("git") or "/usr/bin/git"  # ZCode GUI 行程 PATH 窄——退 /usr/bin 絕對路徑
BASH_BIN = "/bin/bash"

# apply_patch 寫入座標抽取（形態照 codex_memory_path_deny.py——大小寫敏感、
# 無行首寬鬆匹配：hunk context 誤判 header 的 false positive 教訓）
PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$",
    re.MULTILINE,
)

DENY_HEADER = "[Hook Blocked] 控制面路徑禁 canonical 主樹直寫（marshal admission guard——AIR-135.10）"
DENY_GUIDANCE = (
    "控制面檔案的編輯走非 canonical worktree：scripts/wt-open.sh <卡id> --base <owning 線> "
    "開卡 WT，或 scripts/wt-open.sh --ephemeral <name> --base <owning 線> 快速分身；"
    "canonical 主樹（PRIMARY）留 main，編輯在卡 WT 完成後經 merge 收線。"
)


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


def _matches_control_plane(hook_root, rel):
    """guard --match-path 子入口（patterns 單一源）。1＝命中控制面；0／異常＝非命中。"""
    proc = subprocess.run(
        [BASH_BIN, str(hook_root / GUARD_REL), "--match-path", rel],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 1


def evaluate(raw_paths, cwd):
    """任一 target 命中 canonical 控制面 → (raw, resolved, toplevel)；全數通過 → None。

    例外由 main 的 fail-open 接住（exit 0 放行）。
    """
    hook_root = Path(__file__).resolve().parent.parent
    hook_common = None  # lazy——非 repo／非 canonical 目標不必付 self-gate 那顆 git call
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
        if os.path.realpath(toplevel) != os.path.realpath(primary):
            continue  # 非 canonical——卡 WT／ephemeral WT 放行
        if hook_common is None:
            hook_common = _git_common_dir(str(hook_root))
        if os.path.realpath(common) != os.path.realpath(hook_common):
            continue  # repo self-gate——他 repo 的同名控制面路徑 N/A
        rel = os.path.relpath(resolved, toplevel)
        if _matches_control_plane(hook_root, rel):
            return raw, resolved, toplevel
    return None


def _deny(hit):
    _raw, resolved, toplevel = hit
    reason = (
        DENY_HEADER
        + "。\n命中座標：" + str(resolved) + "\n"
        + "（worktree：" + toplevel + "）\n"
        + DENY_GUIDANCE
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
