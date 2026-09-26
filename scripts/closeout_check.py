#!/usr/bin/env python3
# closeout 複查腿 CLI（AIR-193 切片二·survey top3）——結案 predicate 群手動消費態。
# 掛點決策（AC#3）：hook（.githooks/card-diagram-guard.py pre-commit）為正典、本 CLI
# 為複查腿——判定邏輯單一源＝guard 的純函式（import 呼叫），禁二刻。
# 用途：guard 不在場 clone（core.hooksPath 未設）、Done 後補勾／補件複查（AIR-181
# 代勾形態）、--all-done 全板 Done 卡巡檢。
# 用法：
#   uv run python scripts/closeout_check.py "backlog/tasks/air-181 ....md" ...
#   uv run python scripts/closeout_check.py --all-done [--no-history]
# 輸出：stdout 逐卡缺項清單（人話）；refs 未落地走警告（stderr，不計違規）。
# exit code＝違規計數（0＝全過；非 Done 卡跳過不計）——逐卡違規＋歷史軌跡
# violation pair／ERROR 各計 1，可超過卡數。歷史稽核在 --no-ff merge 下同一 flip
# 可於分支 commit 與 merge commit 各報一次（first-parent diff 重計）——本 repo 卡
# branch ff-only 收線慣例下不發生，dedup 不做、於此聲明。
# 歷史軌跡稽核（--all-done 附帶，AIR-208 F2；round-2 gate 解耦）：baseline
# （guard.STATUS_TRAJECTORY_AUDIT_BASELINE，immutable OID）..HEAD 有卡檔事件
# （backlog/tasks＋backlog/completed path universe）即跑；「WT=Done 且 HEAD=Done」
# 盲點集合卡的 authoritative id 只決定 violation scope——僅這些 id 的 lineage 報
# verdict，他卡（含 completed 側）事件照走（rename 鏈）不產 verdict；相鄰 blob
# status pair 餵 guard.status_trajectory_violation（判定單一源，禁二刻）。
# 證據完整性 ERROR（baseline 不可用／非 HEAD 祖先／git 指令失敗／D-A 無法唯一
# 配對／M-R lineage id 不一致或缺失）不受 scope 限制＝非零 exit（fail-closed，
# 不冒充已驗證）。--no-history 逃生。只跑本稽核慢路徑，禁進 pre-commit。
# runtime：系統 python3（3.9）相容——與 guard 同款約束。
import argparse
import glob
import importlib.util
import os
import subprocess
import sys


def _load_guard():
    """載 .githooks/card-diagram-guard.py 為模組——判定函式單一源。"""
    path = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.pardir,
            ".githooks",
            "card-diagram-guard.py",
        )
    )
    spec = importlib.util.spec_from_file_location("card_diagram_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _repo_root():
    r = sh("git", "rev-parse", "--show-toplevel")
    return r.stdout.strip() if r.returncode == 0 else None


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _head_status(g, root, relpath):
    r = sh("git", "-C", root, "show", "HEAD:" + relpath)
    return g.frontmatter_status(r.stdout) if r.returncode == 0 else None


def _is_tracked_factory(root):
    def is_tracked(path):
        return bool(sh("git", "-C", root, "ls-files", "--", path).stdout.strip())

    return is_tracked


def check_card(g, path, root):
    """對單卡跑結案 predicate 群——回 (violations, warnings, status)。"""
    text = _read(path)
    status = g.frontmatter_status(text)
    violations = []
    warnings = []
    if status != "Done":
        return violations, warnings, status
    violations.extend(g.section_marker_violations(text))
    warnings.extend(g.section_marker_warnings(text))
    violations.extend(g.ac_residue_violations(text))
    relpath = os.path.relpath(os.path.abspath(path), root)
    v = g.status_trajectory_violation(_head_status(g, root, relpath), status)
    if v:
        violations.append(v)
    for p in g.missing_ref_paths(text, _is_tracked_factory(root)):
        warnings.append("refs 路徑 git 查無（未落地？MOS-28 型）：" + p)
    return violations, warnings, status


# ── F2：--all-done 歷史軌跡稽核（AIR-208）────────────────────────────
# collector 只取歷史證據（相鄰 commit 的 blob frontmatter status pair）；合法性判定
# 單一源＝guard.status_trajectory_violation。掃描宇宙含 backlog/completed 是為了追
# tasks→completed rename（--all-done 枚舉範圍不變，仍只 backlog/tasks/*.md）。

_AUDIT_PATHS = ("backlog/tasks", "backlog/completed")


def _frontmatter_id(blob_text):
    """frontmatter id 值（D/A identity 配對證據抽取——非判定）。"""
    lines = blob_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for l in lines[1:]:
        s = l.strip()
        if s == "---":
            break
        if s.startswith("id:"):
            return s[len("id:") :].strip().strip("'\"") or None
    return None


def _parse_name_status_z(out):
    """git diff-tree --name-status -z 串流 → [(code, old_path, new_path)]。

    R/C 有兩個路徑；A/M/D 新舊同位——new_path 照抄 old_path（A＝同路徑新 blob、
    M＝parent:old → commit:new 的相鄰對、D＝同路徑舊 blob）。
    """
    toks = out.split("\0")
    events = []
    i = 0
    while i < len(toks):
        code = toks[i]
        if not code:
            i += 1
            continue
        if code[0] in ("R", "C"):
            events.append((code, toks[i + 1], toks[i + 2]))
            i += 3
        else:
            events.append((code, toks[i + 1], toks[i + 1]))
            i += 2
    return events


def _gap_msg(commit, path):
    return (
        f"history-gap：commit {commit[:12]} {path}——frontmatter 解析失敗，相鄰軌跡對"
        "打斷（不跨缺口拼對避免誤報；post-baseline 破損本就可疑，hook 在場不應發生）"
    )


def _show_fail_msg(commit, ref_path, err):
    return (
        f"commit {commit[:12]} git show {ref_path} 失敗——歷史證據取不到，"
        f"fail-closed（{err}）"
    )


def _audit_commit_events(g, root, commit, parent, cache, audit_ids):
    """單 commit 卡檔事件 → (pairs, gaps, errors)。

    pairs＝(commit, old_path, new_path, old_status, new_status, guard_msg)——
    old_path None＝birth（A 事件；old_status None）。git show／diff-tree 指令失敗
    ＝error（證據取不到，fail-closed 非零）；blob 取得成功但 frontmatter 解析失敗
    ＝gap（打斷相鄰鏈＋警告，不跨缺口拼對）。rename 未被 -M 偵測（大改內容拆
    D+A）時以 frontmatter id 復原 lineage；同 commit 重複卡 id、split-rename 兩側
    缺 id、M/R lineage id 不一致或缺失＝identity-ambiguous error（fail-closed，
    不產生 pair）。純刪除（D 無配對 A）非 Done-entry 事件，不餵 predicate。
    violation scope：只對 audit_ids 內 lineage id 的 pair 回報（id 無法判定＝
    birth 形，照報 fail-closed）。
    """
    r = sh(
        "git",
        "-C",
        root,
        "diff-tree",
        "--no-commit-id",
        "-r",
        "-M",
        "--name-status",
        "-z",
        parent,
        commit,
        "--",
        *_AUDIT_PATHS,
    )
    if r.returncode != 0:
        return (
            [],
            [],
            [
                f"commit {commit[:12]} diff-tree 失敗：{r.stderr.strip()}"
                "——歷史證據取不到，fail-closed"
            ],
        )

    def blob(ref_path):
        """git show 結果快取（CompletedProcess）——指令失敗由 returncode 分流。"""
        if ref_path not in cache:
            cache[ref_path] = sh("git", "-C", root, "show", ref_path)
        return cache[ref_path]

    def parse(ref_path):
        """回 (status, id, show_err)；show_err 非 None＝git show 失敗；
        status None（且 show_err None）＝frontmatter 解析失敗。"""
        rr = blob(ref_path)
        if rr.returncode != 0:
            return None, None, rr.stderr.strip()
        return g.frontmatter_status(rr.stdout), _frontmatter_id(rr.stdout), None

    a_events, d_events, m_events = [], [], []
    for code, old_path, new_path in _parse_name_status_z(r.stdout):
        if not (new_path or old_path or "").endswith(".md"):
            continue
        if code[0] == "A":
            a_events.append(new_path)
        elif code[0] == "D":
            d_events.append(old_path)
        else:  # M／R／C——old→new 相鄰對
            m_events.append((old_path, new_path))

    pairs, gaps, errors = [], [], []
    a_st, a_id, d_st, d_id = {}, {}, {}, {}
    for p in d_events:
        s, fid, show_err = parse(f"{parent}:{p}")
        if show_err is not None:
            errors.append(_show_fail_msg(commit, f"{parent}:{p}", show_err))
            continue
        if s is None:
            gaps.append(_gap_msg(commit, p))
            continue
        d_st[p], d_id[p] = s, fid
    for p in a_events:
        s, fid, show_err = parse(f"{commit}:{p}")
        if show_err is not None:
            errors.append(_show_fail_msg(commit, f"{commit}:{p}", show_err))
            continue
        if s is None:
            gaps.append(_gap_msg(commit, p))
            continue
        a_st[p], a_id[p] = s, fid

    def _dup_ids(idmap):
        seen = {}
        for p, fid in idmap.items():
            if fid is not None:
                seen.setdefault(fid, []).append(p)
        return {fid: ps for fid, ps in seen.items() if len(ps) > 1}

    for label, idmap in (("新增", a_id), ("刪除", d_id)):
        for fid, ps in _dup_ids(idmap).items():
            errors.append(
                f"identity-ambiguous：commit {commit[:12]} {label}側出現重複卡 id"
                f"「{fid}」（{len(ps)} 檔）——無法唯一配對，fail-closed"
            )
    # 缺 id 的 split-rename 兩側無法以 id 配對——與重複 id 同屬 identity-ambiguous
    idless_a = [p for p in a_events if p in a_st and a_id[p] is None]
    idless_d = [p for p in d_events if p in d_st and d_id[p] is None]
    if (idless_a and d_st) or (idless_d and a_st):
        errors.append(
            f"identity-ambiguous：commit {commit[:12]} 卡檔缺 frontmatter id"
            f"（A 側 {idless_a}／D 側 {idless_d}）——split-rename 無法以 id 配對，"
            "fail-closed"
        )
    if errors:
        return pairs, gaps, errors  # ambiguous commit 短路——不產生 pair
    for p in a_events:
        if p not in a_st:
            continue  # 解析失敗已記 gap
        cands = (
            [dp for dp, fid in d_id.items() if fid == a_id[p]]
            if a_id[p] is not None
            else []
        )
        old_s, old_path = None, None
        if cands:  # dup／缺 id 檢查後 candidates ≤1——同 id lineage 視為 rename
            dp = cands[0]
            old_s, old_path = d_st[dp], dp
        v = g.status_trajectory_violation(old_s, a_st[p])
        if v and (a_id[p] is None or a_id[p] in audit_ids):
            # scope：非盲點集合 id 的 lineage 不產 verdict；birth 形 id 無法判定
            # 照報（fail-closed）
            pairs.append((commit, old_path, p, old_s, a_st[p], v))
    for old_path, new_path in m_events:
        old_s, old_fid, show_err = parse(f"{parent}:{old_path}")
        if show_err is not None:
            errors.append(_show_fail_msg(commit, f"{parent}:{old_path}", show_err))
            continue
        if old_s is None:
            gaps.append(_gap_msg(commit, old_path))
            continue
        new_s, new_fid, show_err = parse(f"{commit}:{new_path}")
        if show_err is not None:
            errors.append(_show_fail_msg(commit, f"{commit}:{new_path}", show_err))
            continue
        if new_s is None:
            gaps.append(_gap_msg(commit, new_path))
            continue
        # M/R 兩側 id 皆須存在且相等——身份自證（丟棄 id 會讓新 Done identity
        # 繼承舊 identity 的合法前驅，繞過 birth-Done 檢查）
        if old_fid is None or new_fid is None or old_fid != new_fid:
            errors.append(
                f"identity-ambiguous：commit {commit[:12]} lineage id 不一致或缺失"
                f"（{old_path} → {new_path}：{old_fid!r} → {new_fid!r}）——"
                "M/R 身份無法自證，fail-closed"
            )
            continue
        v = g.status_trajectory_violation(old_s, new_s)
        if v and new_fid in audit_ids:
            pairs.append((commit, old_path, new_path, old_s, new_s, v))
    return pairs, gaps, errors


def _audit_should_run(g, root):
    """gate：baseline..HEAD 有卡檔事件即跑（與 WT 狀態解耦）。count==0 且 baseline
    為 HEAD 祖先＝無可審歷史（vacuous pass 已驗證）→ False；其餘無法判定一律
    True——稽核自身 baseline 雙檢 fail-closed 收（shallow clone 自然落入）。"""
    baseline = g.STATUS_TRAJECTORY_AUDIT_BASELINE
    r = sh(
        "git",
        "-C",
        root,
        "rev-list",
        "--count",
        f"{baseline}..HEAD",
        "--",
        *_AUDIT_PATHS,
    )
    if r.returncode != 0:
        return True
    try:
        n = int(r.stdout.strip())
    except ValueError:
        return True
    if n > 0:
        return True
    mb = sh("git", "-C", root, "merge-base", "--is-ancestor", baseline, "HEAD")
    return mb.returncode != 0


def history_trajectory_audit(g, root, audit_ids):
    """F2 歷史軌跡稽核（--all-done 專用慢路徑）——回 (violations, errors, warnings)。

    baseline 前置雙檢查（cat-file -e ^{commit}＋merge-base --is-ancestor）任一失敗
    ＝errors 非空（呼叫端計入非零 exit——fail-closed，不冒充已驗證；shallow clone
    自然落入）。單趟 rev-list --parents --reverse baseline..HEAD，逐 commit
    first-parent diff 取事件（merge 經 first-parent diff 自然涵蓋；衝突手寫 status
    為已知邊界，文件聲明）。baseline 前祖父化（不重新審判 legacy 卡）。
    scope（round-2）：audit_ids＝盲點集合卡（WT=Done 且 HEAD=Done）的 authoritative
    frontmatter id 集合——violation 只對這些 id 的 lineage 報告（--all-done 候選
    宇宙不因 backlog/completed 擴大：completed 側僅供 rename 鏈 path universe，
    他卡 lineage 事件照走但不產 verdict）；id 無法判定（None，僅 birth 形可達）
    照報 fail-closed。errors／gaps 是證據完整性問題，不受 scope 限制。
    已知邊界（偵測控制定位，文件聲明）：committer date 偽造、merge 衝突手寫
    status、flip commit 的 status 行被 mangle（如 `state: Done`）且下一 commit
    restore——兩 commit 皆 parse-fail 成 history-gap 警告、相鄰鏈打斷，flip 隱形
    於違規計數。
    """
    baseline = g.STATUS_TRAJECTORY_AUDIT_BASELINE
    r = sh("git", "-C", root, "cat-file", "-e", f"{baseline}^{{commit}}")
    if r.returncode != 0:
        return (
            [],
            [
                f"baseline {baseline[:12]} 不可用（git cat-file 失敗）——歷史無法驗證，"
                "fail-closed 非 PASS；shallow clone 請先 git fetch --unshallow"
            ],
            [],
        )
    r = sh("git", "-C", root, "merge-base", "--is-ancestor", baseline, "HEAD")
    if r.returncode != 0:
        return (
            [],
            [
                f"baseline {baseline[:12]} 非 HEAD 祖先——歷史無法驗證，fail-closed 非 PASS"
            ],
            [],
        )
    r = sh("git", "-C", root, "rev-list", "--parents", "--reverse", f"{baseline}..HEAD")
    if r.returncode != 0:
        return [], [f"rev-list {baseline[:12]}..HEAD 失敗：{r.stderr.strip()}"], []
    violations, errors, warnings = [], [], []
    cache = {}
    for line in r.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        commit, parent = parts[0], (parts[1] if len(parts) > 1 else None)
        if parent is None:
            warnings.append(
                f"history-gap：commit {commit[:12]} 無 parent（orphan root）"
                "——diff 無法取，相鄰鏈打斷"
            )
            continue
        p, gp, e = _audit_commit_events(g, root, commit, parent, cache, audit_ids)
        violations.extend(p)
        warnings.extend(gp)
        errors.extend(e)
    return violations, errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "closeout 複查腿——結案 predicate 群手動消費態"
            "（判定源＝.githooks/card-diagram-guard.py）"
        )
    )
    parser.add_argument("cards", nargs="*", help="卡檔路徑（backlog/tasks/*.md）")
    parser.add_argument(
        "--all-done", action="store_true", help="掃 backlog/tasks/ 全部 status: Done 卡"
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="跳過 --all-done 附帶的歷史軌跡稽核（AIR-208 逃生口；預設全審）",
    )
    args = parser.parse_args(argv)
    g = _load_guard()
    if args.all_done:
        root = _repo_root()
        if not root:
            print(
                "ERROR: 不在 git repo 內——--all-done 需 repo root 定位 backlog/tasks/",
                file=sys.stderr,
            )
            return 2
        cards = [
            p
            for p in sorted(glob.glob(os.path.join(root, "backlog", "tasks", "*.md")))
            if g.frontmatter_status(_read(p)) == "Done"
        ]
    else:
        if not args.cards:
            parser.error("至少給一張卡檔路徑，或 --all-done")
        root = _repo_root() or os.getcwd()
        cards = args.cards
    # F2 歷史軌跡稽核（AIR-208 round-2）：gate 與 WT 狀態解耦——baseline..HEAD 有
    # 卡檔事件即跑（backlog/completed 側歷史不因 tasks 無盲點卡而漏審）；count==0
    # 且 baseline 為 HEAD 祖先＝無可審歷史才跳過（顯性註記）。盲點集合（WT=Done
    # 且 HEAD=Done）卡的 authoritative id 只決定 violation scope——他卡 lineage
    # 事件照走（rename 鏈）不產 verdict；證據完整性 error 不受 scope 限制
    history = None
    if args.all_done and args.no_history:
        print(
            "--no-history：跳過歷史軌跡稽核（AIR-208 逃生口）——本輪僅驗 WT/HEAD "
            "一致性，不保證歷史軌跡合法",
            file=sys.stderr,
        )
    elif args.all_done:
        if _audit_should_run(g, root):
            audit_ids = set()
            for p in cards:
                if (
                    _head_status(g, root, os.path.relpath(os.path.abspath(p), root))
                    == "Done"
                ):
                    fid = _frontmatter_id(_read(p))
                    if fid:
                        audit_ids.add(fid)
            history = history_trajectory_audit(g, root, audit_ids)
        else:
            print(
                "歷史軌跡稽核：baseline..HEAD 無卡檔事件——跳過",
                file=sys.stderr,
            )
    bad = 0
    for path in cards:
        if not os.path.exists(path):
            print(f"ERROR: 卡檔不存在：{path}", file=sys.stderr)
            bad += 1
            continue
        violations, warnings, status = check_card(g, path, root)
        if status != "Done":
            print(f"SKIP {path}——status={status}，非結案對象")
            continue
        if violations:
            bad += 1
            print(f"FAIL {path}——{len(violations)} 項違規：")
            for i, v in enumerate(violations, 1):
                print(f"  {i}. {v}")
        else:
            print(f"PASS {path}")
        for w in warnings:
            print("  警告（不擋）：" + w, file=sys.stderr)
    if history is not None:
        h_violations, h_errors, h_warnings = history
        for w in h_warnings:
            print("  " + w, file=sys.stderr)
        for commit, old_path, new_path, old_s, new_s, msg in h_violations:
            bad += 1
            print("FAIL（歷史軌跡稽核）" + new_path)
            info = "  commit {}：{} → {}".format(
                commit[:12],
                old_s if old_s is not None else "（新建——無先前觀測）",
                new_s,
            )
            if old_path and old_path != new_path:
                info += f"（{old_path} → {new_path}）"
            print(info)
            print("  " + msg)
        for e in h_errors:
            bad += 1
            print("ERROR（歷史軌跡稽核）" + e)
    return min(bad, 255)  # shell exit 收斂（>255 會 wrap）


if __name__ == "__main__":
    sys.exit(main())
