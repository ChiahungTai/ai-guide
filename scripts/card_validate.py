#!/usr/bin/env python3
# kanban 卡檔 frontmatter 機械驗證閘（AIR-309 P1）——「寫入後立即驗證、失敗 agent 自修」
# 機械面。起因＝bridge 側 DB-109 malformed frontmatter 事故（plain scalar 內 `a: b` 使
# pyyaml "mapping values are not allowed"，板解析器把卡靜默打進 Unparsed）。
#
# 四層檢查（結構層敗＝停驗後續層——下層對破碎結構無判定意義）：
#   ① delimiter：檔首 opening「---」＋ closing「---」完整
#   ② YAML strict：pyyaml safe_load 系全量解析；日期不自動轉型（timestamp tag 的
#      constructor 覆寫回原字串——文件契約以字串為準，quoted／unquoted 同收 str）
#   ③ top-level mapping：解析結果須為 dict（list／scalar／空皆違約）
#   ④ 必填欄位契約：kanban 必要欄位在場＋型別（全板 251 卡實測分佈）——
#      id/title/status/created_date/updated_date＝非空字串；
#      assignee/labels/dependencies＝清單；ordinal＝整數（bool 除外）；
#      選填 references＝清單、parent_task_id＝非空字串
#
# 邊界（與 card-diagram-guard 分工，兩閘並存不重疊——kanban skill「frontmatter 驗證閘」條）：
# 本閘只驗 frontmatter 機械面（卡檔是機器可解析的卡）；結案結構（AC 殘留／status 軌跡／
# 五段 marker／desc 圖／黑話／終態圖）歸 .githooks/card-diagram-guard.py。
#
# CLI：
#   uv run python scripts/card_validate.py <file...>   # 逐檔驗（working tree 檔）
#   uv run python scripts/card_validate.py --all       # 掃 backlog/tasks/ 全板
#   uv run python scripts/card_validate.py --staged    # pre-commit hook 模式（驗 staged blob）
# exit：0＝全過；1＝違規（列違規檔＋逐條原因——自修迴圈逐條修到 0）；2＝環境／用法錯
# （pyyaml 缺且無法自癒、非 git repo、argparse 用法錯等——非卡檔驗證 verdict）。
#
# 依賴自癒：pyyaml 非本專案依賴（pyproject runtime deps 淨空）——import 失敗時以
# `uv run --no-project --with pyyaml` re-exec 自身（uv 快取後零網路；首次需抓套件）；
# 無 uv／再失敗＝exit 2 帶手動修法。pytest 環境無 pyyaml，測試 subprocess 每次呼叫
# 都實測此自癒路徑。
# runtime：uv 管理的 python（專案 requires-python >=3.12）；語法保守至 3.9
# （與 card-diagram-guard 同款紀律——系統 python3 直跑也解析得了，僅 yaml 層需 uv）。

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # 自癒 re-exec 路徑——見 self_heal_exec()
    yaml = None

BOARD_DIR = "backlog/tasks"

# ── 必填欄位契約（單一源；全板 251 卡 100% 在場的九欄＝必填）──────────
REQUIRED_STR = ("id", "title", "status", "created_date", "updated_date")
REQUIRED_LIST = ("assignee", "labels", "dependencies")
REQUIRED_INT = ("ordinal",)
OPTIONAL_LIST = ("references",)
OPTIONAL_STR = ("parent_task_id",)


def _die2(msg):
    print("[card_validate] " + msg, file=sys.stderr)
    sys.exit(2)


def self_heal_exec():
    """pyyaml 缺席時以 uv ephemeral env re-exec 自身；無 uv＝exit 2 帶手動修法。

    --no-project：驗證器零專案依賴（stdlib＋pyyaml），跳過專案 env 解析與 sync，
    任意 cwd（tmp repo 測試、hook）皆可跑；守衛變數防 re-exec 迴圈。
    """
    remedy = (
        "pyyaml 不可用——手動跑：uv run --with pyyaml python scripts/card_validate.py <args>"
    )
    if os.environ.get("_CARD_VALIDATE_SELF_HEAL") == "1":
        _die2("自癒 re-exec 後仍缺 pyyaml——" + remedy)
    uv = shutil.which("uv")
    if uv is None:
        _die2("PATH 上無 uv，無法自癒——" + remedy)
    env = dict(os.environ)
    env["_CARD_VALIDATE_SELF_HEAL"] = "1"
    argv = [
        uv,
        "run",
        "--no-project",
        "--with",
        "pyyaml",
        "python",
        os.path.abspath(__file__),
        *sys.argv[1:],
    ]
    os.execvpe(uv, argv, env)


if yaml is not None:

    class ContractLoader(yaml.SafeLoader):
        """safe_load 系＋日期不自動轉型（AIR-309：文件契約以字串為準）。

        pyyaml 對 timestamp 形 scalar 隱式掛 tag 後 construct 成 datetime/date，
        使「欄位型別＝字串」契約誤判——constructor 覆寫回 construct_scalar 原字串。
        """

    ContractLoader.add_constructor(
        "tag:yaml.org,2002:timestamp",
        lambda loader, node: loader.construct_scalar(node),
    )


def validate_text(text):
    """四層檢查——回 [(layer, message), ...]；空清單＝過。"""
    lines = text.splitlines()
    # ① delimiter
    if not lines or lines[0].strip() != "---":
        return [("delimiter", "檔首缺 opening「---」——frontmatter delimiter 不完整")]
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return [("delimiter", "缺 closing「---」——frontmatter 未閉合")]
    # ② YAML strict（日期不自動轉型）
    try:
        data = yaml.load("\n".join(lines[1:close]), Loader=ContractLoader)
    except yaml.YAMLError as e:
        detail = "；".join(s.strip() for s in str(e).splitlines() if s.strip())
        return [("yaml", "YAML strict 解析失敗：" + detail)]
    # ③ top-level mapping
    if not isinstance(data, dict):
        got = "空（frontmatter 無內容）" if data is None else type(data).__name__
        return [("mapping", "top-level 須為 mapping（key: value 形），實得" + got)]
    # ④ 必填欄位契約
    return field_issues(data)


def field_issues(data):
    """層④——必填欄位在場＋型別；選填欄位在場時同驗型別。"""
    out = []
    for f in REQUIRED_STR:
        if f not in data:
            out.append(("fields", "缺必填欄位 " + f))
        elif not isinstance(data[f], str) or not data[f].strip():
            out.append(
                ("fields", f"{f} 須為非空字串，實得 {data[f]!r}（{type(data[f]).__name__}）")
            )
    for f in REQUIRED_LIST:
        if f not in data:
            out.append(("fields", "缺必填欄位 " + f))
        elif not isinstance(data[f], list):
            out.append(("fields", f"{f} 須為清單，實得 {data[f]!r}（{type(data[f]).__name__}）"))
    for f in REQUIRED_INT:
        if f not in data:
            out.append(("fields", "缺必填欄位 " + f))
        elif isinstance(data[f], bool) or not isinstance(data[f], int):
            out.append(
                ("fields", f"{f} 須為整數，實得 {data[f]!r}（{type(data[f]).__name__}）")
            )
    for f in OPTIONAL_LIST:
        if f in data and not isinstance(data[f], list):
            out.append(("fields", f"{f} 須為清單，實得 {data[f]!r}（{type(data[f]).__name__}）"))
    for f in OPTIONAL_STR:
        if f in data and (not isinstance(data[f], str) or not data[f].strip()):
            out.append(
                ("fields", f"{f} 須為非空字串，實得 {data[f]!r}（{type(data[f]).__name__}）")
            )
    return out


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def staged_card_blobs():
    """hook 母體——staged 的 backlog/tasks/*.md（name-status -M -C；rename 取 dest，
    與 card-diagram-guard 同款解析）。回 [(路徑, 文字或 None, 讀取錯誤或 None)]。"""
    r = sh(
        "git",
        "-c",
        "core.quotePath=false",
        "diff",
        "--cached",
        "--name-status",
        "-M",
        "-C",
        "--",
        BOARD_DIR + "/*.md",
    )
    if r.returncode != 0:
        _die2("git diff --cached 失敗（非 git repo 或 index 異常）：" + r.stderr.strip())
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        code, dest = parts[0], parts[-1]
        if code.startswith("D"):
            continue  # 刪卡無 frontmatter 可驗；rename 未達相似度拆 D＋A，A 側照驗
        blob = sh("git", "show", ":" + dest)
        if blob.returncode != 0:
            out.append((dest, None, "staged blob 讀取失敗（index 不一致）"))
            continue
        out.append((dest, blob.stdout, None))
    return out


def collect_entries(ns):
    """三模式共用母體——回 [(顯示路徑, 文字或 None, 讀取錯誤或 None)]。"""
    if ns.staged:
        return staged_card_blobs()
    if ns.all:
        board = Path(__file__).resolve().parents[1] / BOARD_DIR
        if not board.is_dir():
            _die2(BOARD_DIR + "/ 不存在（--all 以本腳本所在 repo 為根）")
        return [(str(p.relative_to(board.parents[1])), p.read_text(), None)
                for p in sorted(board.glob("*.md"))]
    entries = []
    for raw in ns.files:
        p = Path(raw)
        if not p.is_file():
            entries.append((raw, None, "檔案不存在"))
            continue
        try:
            entries.append((raw, p.read_text(), None))
        except UnicodeDecodeError:
            entries.append((raw, None, "檔案非 UTF-8，無法解析"))
    return entries


def main(argv=None):
    if yaml is None:
        self_heal_exec()
    parser = argparse.ArgumentParser(
        prog="card_validate.py",
        description="kanban 卡檔 frontmatter 機械驗證閘"
        "（四層：delimiter／YAML strict／top-level mapping／必填欄位）",
    )
    parser.add_argument("files", nargs="*", metavar="file", help="待驗卡檔路徑（可多個）")
    parser.add_argument("--all", action="store_true", help="掃 backlog/tasks/ 全板")
    parser.add_argument(
        "--staged", action="store_true", help="pre-commit hook 模式：驗 staged 卡檔 blob（通過時靜默）"
    )
    ns = parser.parse_args(argv)
    if bool(ns.files) + int(ns.all) + int(ns.staged) != 1:
        parser.error("須恰好一種模式：<file...>、--all 或 --staged")
    violations = 0
    entries = collect_entries(ns)
    for path, text, read_err in entries:
        issues = [("read", read_err)] if read_err else validate_text(text)
        if issues:
            violations += 1
            print("FAIL " + path)
            for layer, msg in issues:
                print("  [" + layer + "] " + msg)
        elif not ns.staged:
            print("PASS " + path)
    if violations:
        print(
            f"[card_validate] {violations}/{len(entries)} 檔違規——"
            "自修迴圈：逐條修後重跑，exit 0 才進下一步"
        )
        return 1
    if not ns.staged:
        print(f"[card_validate] {len(entries)} 檔全過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
