#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""post-build gate（AIR-119）——主鏈跳步機械閘，A/B 共用判定單一源。

B 腿（Stop hook，CC＋ZCode 雙端註冊）：turn 結束判定，命中→輸出 block JSON
（reason＝指令；harness 連續上限 ZCode 3／CC 8——本閘預算 2 次先於上限自限）。
A 腿（/commit 階段 2.95）：`--verdict` 印 tri-state JSON（state＝ok／stale／
missing／exempt＋ahead 數），skill 消費子進程輸出，禁 import（檔名含連字號）。

判定（純機械，全過才攔）：
  1. 卡在場——backlog CLI `task view <branch>` 權威（無卡／CLI 缺席／非 backlog
     repo＝豁免；user 裁決 0917）
  2. branch 非 main／master 且非 detached HEAD（--abbrev-ref 回 "HEAD" 豁免）
  3. vs merge-base(main|master, HEAD) 有領先 commit
  4. 改動含非 .md 檔（純文檔／卡務／排程 session commit 豁免）
  5. receipt 三態（.agent-tmp/post-build-receipts/<branch 編碼>.json）：
     ok（head_sha==HEAD）→放行並清 block 預算；missing（缺席或缺 head_sha 鍵）→攔；
     stale（head 為歷史值）→攔。stale 常態來源＝/commit 推進 HEAD——
     /commit 階段 6 成功後刷新 receipt head_sha（審查 F1），刷新前窗期的 stale
     視同已覆蓋，reason 自帶逃生口。

安全約束：runtime python 3.9（機器 python3）——禁 3.10+ 語法；<1s（實測
65-80ms）；內部任何錯誤 exit 0 fail-open（催告閘非安全閘，禁讓 turn 崩）；
block 預算 per-branch 終身 2 次（branch 經 `/`→`__` 檔名編碼——slash branch
預算防線才不會靜默失效，審查 F2）；block JSON 輸出 ensure_ascii 預設（locale
編碼防禦，審查 F9）。已知限制：trunk 候選硬編碼 main/master，自訂 trunk 的
repo 閘不存在（覆蓋缺口非誤攔，審查 F7）。
"""
import json
import os
import subprocess
import sys

BLOCK_BUDGET = 2
MAIN_CANDIDATES = ("main", "master")


def _git(repo, *args):
    out = subprocess.run(
        ["git", "-C", repo] + list(args),
        capture_output=True, text=True, timeout=10,
    )
    return out.stdout.strip() if out.returncode == 0 else ""


def _card_exists(repo, branch):
    """卡存在判定單一源＝backlog CLI（id 正規化與 store 格式的權威——
    branch↔卡 id 的 prose 慣例若漂移，CLI 跟著更新，glob 二次硬編碼退役，
    user 裁決 0917）。CLI 缺席／非 backlog repo／查無卡 → False（fail-open：
    gate exempt，誤放行而非誤攔）。"""
    try:
        out = subprocess.run(
            ["backlog", "task", "view", branch],
            cwd=repo, capture_output=True, text=True, timeout=15,
        )
        return out.returncode == 0
    except Exception:
        return False


def _branch_key(branch):
    return branch.replace("/", "__")  # slash branch 檔名編碼（審查 F2）


def _receipt(repo, branch, head):
    """回 (state, stale_at)：state ∈ ok／stale／missing。缺 head_sha 鍵＝missing（審查 F6）。"""
    path = os.path.join(repo, ".agent-tmp", "post-build-receipts",
                        _branch_key(branch) + ".json")
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return "missing", ""
    if not isinstance(data, dict) or not data.get("head_sha"):
        return "missing", ""
    if data.get("head_sha") == head:
        return "ok", ""
    return "stale", str(data.get("completed_at", ""))


def _budget_count(repo, branch):
    try:
        with open(os.path.join(repo, ".agent-tmp", "post-build-gate",
                               _branch_key(branch) + ".blocks")) as fh:
            return int(fh.read().strip() or "0")
    except Exception:
        return 0


def _budget_consume(repo, branch):
    try:
        d = os.path.join(repo, ".agent-tmp", "post-build-gate")
        os.makedirs(d, exist_ok=True)
        count = _budget_count(repo, branch)  # 先讀後寫——"w" 會截斷同檔（自截斷 bug）
        with open(os.path.join(d, _branch_key(branch) + ".blocks"), "w") as fh:
            fh.write(str(count + 1))
    except Exception:
        pass


def verdict(repo):
    """回 dict：branch／state（ok｜stale｜missing｜exempt）／ahead／reason。

    純狀態判定（無 block 預算——預算是 B 腿催告語義，A 腿收口閘不受預算限，
    審查 F4）。A 腿經 --verdict 消費本函式。
    """
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    exempt = {"branch": branch, "state": "exempt", "ahead": 0, "reason": ""}
    if branch in ("", "HEAD"):  # detached HEAD（審查 F8）
        return exempt
    if branch in MAIN_CANDIDATES:
        return exempt
    if not _card_exists(repo, branch):  # 無卡＝非鏈上弧（user 裁決 0917）
        return exempt
    merge_base = ""
    for cand in MAIN_CANDIDATES:
        merge_base = _git(repo, "merge-base", cand, "HEAD")
        if merge_base:
            break
    if not merge_base:
        return exempt
    ahead = _git(repo, "rev-list", "--count", merge_base + "..HEAD")
    if ahead in ("", "0"):
        return exempt
    files = _git(repo, "diff", "--name-only", merge_base, "HEAD")
    if not files or all(f.endswith(".md") for f in files.splitlines()):
        return exempt
    head = _git(repo, "rev-parse", "HEAD")
    state, stale_at = _receipt(repo, branch, head)
    if state == "ok":
        try:  # receipt 覆蓋現狀——清 block 預算（新工作＝新預算）
            os.remove(os.path.join(repo, ".agent-tmp", "post-build-gate",
                                   _branch_key(branch) + ".blocks"))
        except OSError:
            pass
        return {"branch": branch, "state": "ok", "ahead": ahead, "reason": ""}
    if state == "stale":
        return {"branch": branch, "state": "stale", "ahead": ahead, "reason": (
            "post-build receipt 已過期（head != 當前 HEAD，完成於 %s）——其後又有新 "
            "commit。若本弧已完成：重跑 /post-build 刷新 receipt；若僅 /commit 推進 "
            "了 HEAD（receipt 內容已含本弧工作）：此提醒可忽略，/commit 階段 6 會刷新。"
            % (stale_at or "未知時點")
        )}
    return {"branch": branch, "state": "missing", "ahead": ahead, "reason": (
        "本弧尚無有效 post-build receipt（branch=%s，領先 main %s 個 commit）。"
        "若本弧已完成：先跑 /post-build（收尾鏈），完成後再結束；"
        "若僅段落結算、弧未完成：直接繼續工作即可（此提醒有預算上限，不會連環出現）。"
        % (branch, ahead)
    )}


def main():
    argv = sys.argv[1:]
    if "--verdict" in argv:  # A 腿 CLI：tri-state JSON（cwd＝repo）
        try:
            result = verdict(os.getcwd())
        except Exception:
            result = {"branch": "", "state": "exempt", "ahead": 0, "reason": ""}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    # B 腿：Stop hook
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    repo = payload.get("cwd") or os.getcwd()
    try:
        result = verdict(repo)
        should_block = result["state"] in ("stale", "missing")
    except Exception:
        should_block, result = False, {"reason": ""}  # fail-open：禁讓 turn 崩
    if should_block:
        branch = result.get("branch") or ""
        if _budget_count(repo, branch) >= BLOCK_BUDGET:
            should_block = False  # 催告預算耗盡——靜默讓 turn 結束（A 腿仍把關）
        else:
            _budget_consume(repo, branch)
    if should_block:
        print(json.dumps({"decision": "block", "reason": result["reason"]}))
    sys.exit(0)


if __name__ == "__main__":
    main()
