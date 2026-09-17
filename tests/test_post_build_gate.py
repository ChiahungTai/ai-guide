"""post-build-gate.py 場景整合測試（AIR-119）。

以 subprocess 走真實 hook 契約（stdin JSON／--verdict CLI）跑完整生命週期場景：
卡存在判定（backlog CLI 權威——無卡豁免）、預算制（F2 編碼回歸為函式級直測）、
receipt 三態（ok/stale/missing）、stale 逃生口語（F1）、main 豁免。步驟間共用
同一 fixture repo 的順序狀態，故收進單一 test 逐項收集、末尾斷言。

fixture 卡由真 `backlog init`＋`task create` 建立——卡存在判定與生產端同源
（CLI 是 id 正規化與 store 格式的權威）。
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "post-build-gate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pbg", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(fix, *args, **kw):
    out = subprocess.run(
        ["git", "-C", str(fix)] + list(args), capture_output=True, text=True
    )
    if out.returncode != 0 and not kw.get("may_fail"):
        raise RuntimeError("git %s: %s" % (args, out.stderr))
    return out.stdout.strip()


def commit(fix, fname, content):
    (fix / fname).write_text(content)
    git(fix, "add", fname)
    git(fix, "commit", "-m", "add " + fname)


def run_hook(fix):
    p = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"cwd": str(fix), "hook_event_name": "Stop"}),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return p.returncode, p.stdout.strip()


def run_verdict(fix):
    p = subprocess.run(
        [sys.executable, str(HOOK), "--verdict"],
        cwd=str(fix),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(p.stdout)


def write_receipt(fix, branch, head_sha):
    d = fix / ".agent-tmp" / "post-build-receipts"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / (branch.replace("/", "__") + ".json"), "w") as fh:
        json.dump({"branch": branch, "head_sha": head_sha, "completed_at": "t"}, fh)


def clear_budget(fix, branch):
    marker = fix / ".agent-tmp" / "post-build-gate" / (branch.replace("/", "__") + ".blocks")
    marker.unlink(missing_ok=True)


def test_gate_scenario(tmp_path):
    fix = tmp_path
    git(fix, "init")
    git(fix, "symbolic-ref", "HEAD", "refs/heads/main")
    init = subprocess.run(
        ["backlog", "init", "fixture", "--agent-instructions", "none"],
        cwd=str(fix), capture_output=True, text=True, timeout=60, input="",
    )
    assert init.returncode == 0, "backlog init: %s%s" % (init.stdout, init.stderr)
    created = subprocess.run(
        ["backlog", "task", "create", "fixture card"],
        cwd=str(fix), capture_output=True, text=True, timeout=60,
    )
    assert created.returncode == 0, "task create: %s%s" % (created.stdout, created.stderr)
    card_id = os.listdir(fix / "backlog" / "tasks")[0].split(" - ")[0]
    CARD = card_id.lower()  # branch 慣例形態（小寫）
    commit(fix, "backlog/tasks/%s - fixture.md" % card_id, "")
    git(fix, "add", "backlog") if False else None  # card 檔已由 CLI add/commit 或隨後 commit
    git(fix, "add", "-A")
    git(fix, "commit", "-m", "backlog store") if git(
        fix, "status", "--porcelain"
    ) else None
    git(fix, "checkout", "-b", CARD)

    fails = []

    def check(name, cond, detail=""):
        if not cond:
            fails.append("%s | %s" % (name, detail[:120]))

    # docs-only → 豁免 pass
    commit(fix, "notes.md", "notes\n")
    rc, out = run_hook(fix)
    check("t1 docs-only pass", rc == 0 and out == "", out)

    # .py commit、無 receipt → block（預算 1）
    commit(fix, "mod.py", "x = 1\n")
    rc, out = run_hook(fix)
    check("t2 no-receipt block", rc == 0 and '"decision": "block"' in out.replace("'", '"'), out)

    # 第二次 turn end → block（預算 2）
    rc, out = run_hook(fix)
    check("t3 budget-2 block", '"block"' in out, out)

    # stale → block 附逃生口語（清預算模擬新弧：stale 首發預算必新）
    prev = git(fix, "rev-parse", "HEAD~1")
    clear_budget(fix, CARD)
    write_receipt(fix, CARD, prev)
    rc, out = run_hook(fix)
    try:
        reason4 = json.loads(out).get("reason", "")
    except Exception:
        reason4 = ""
    check("t4 stale block + escape wording", "過期" in reason4 and "忽略" in reason4, reason4)

    # 有效 receipt → pass（清預算）
    head = git(fix, "rev-parse", "HEAD")
    write_receipt(fix, CARD, head)
    rc, out = run_hook(fix)
    check("t5 valid-receipt pass", rc == 0 and out == "", out)

    # receipt 移除 → 新預算 → block
    (fix / ".agent-tmp" / "post-build-receipts" / (CARD + ".json")).unlink()
    rc, out = run_hook(fix)
    check("t6 fresh-budget block after ok", '"block"' in out, out)

    # 預算耗盡 → 靜默放行
    run_hook(fix)
    rc, out = run_hook(fix)
    check("t7 budget-exhausted silent", rc == 0 and out == "", out)

    # main branch → 恆 pass
    git(fix, "checkout", "main")
    rc, out = run_hook(fix)
    check("t8 main pass", rc == 0 and out == "", out)

    # 無卡 branch → 豁免（user 裁決 0917：鏈是卡驅動，無卡不欠 post-build）
    git(fix, "checkout", "-b", "feature/x")
    commit(fix, "feat.py", "f = 1\n")
    rc, out = run_hook(fix)
    check("t9 no-card exempt", rc == 0 and out == "", out)

    # F2 回歸（函式級）：slash branch 的預算讀寫同路徑（_branch_key 編碼）
    mod = _load_module()
    assert mod._branch_key("feature/x") == "feature__x"
    mod._budget_consume(str(fix), "feature/x")
    assert mod._budget_count(str(fix), "feature/x") == 1, "F2: slash branch 預算計數"

    # --verdict CLI 三態（A 腿——不受 B 腿預算影響；card branch 上判定）
    git(fix, "checkout", CARD)
    v = run_verdict(fix)
    check(
        "t10a verdict missing (budget 無關)",
        v["state"] == "missing" and v["branch"] == CARD,
        json.dumps(v, ensure_ascii=False),
    )
    write_receipt(fix, CARD, git(fix, "rev-parse", "HEAD"))
    v = run_verdict(fix)
    check("t10b verdict ok", v["state"] == "ok", json.dumps(v, ensure_ascii=False))
    write_receipt(fix, CARD, "0" * 40)
    v = run_verdict(fix)
    check("t10c verdict stale", v["state"] == "stale", json.dumps(v, ensure_ascii=False))
    receipt_path = fix / ".agent-tmp" / "post-build-receipts" / (CARD + ".json")
    with open(receipt_path) as fh:
        bad = json.load(fh)
    del bad["head_sha"]
    with open(receipt_path, "w") as fh:
        json.dump(bad, fh)
    v = run_verdict(fix)
    check("t10d verdict missing (缺 head_sha 鍵, F6)", v["state"] == "missing", json.dumps(v, ensure_ascii=False))

    # main 上 verdict 豁免
    git(fix, "checkout", "main")
    v = run_verdict(fix)
    check("t11 verdict main exempt", v["state"] == "exempt", json.dumps(v, ensure_ascii=False))

    assert not fails, "gate scenario failures:\n" + "\n".join(fails)
