#!/usr/bin/env python3
# MEMORY.md 索引 generator——條目檔 frontmatter 是單一 source，索引是其機械投影。
# 用法: python3 _generate_index.py [--check]（--check 只驗證不寫入、零檔案系統副作用）
# 部署形態：本檔是資產源 ai-guide repo skills/memory-audit/scripts/generate_index.py
#   的副本（複製進各專案 memory dir、更名 _generate_index.py）。副本與資產源 bytes
#   不符時 Stop hook（hooks/memory-index-regen.py 信任邊界）跳過重生成並留
#   _regen-skipped-stale 標記——刷新：cp <資產源> ./_generate_index.py.new
#   && mv ./_generate_index.py.new ./_generate_index.py（原子）；詳情 memory-audit skill 層 1。
# Gate 分級（2026-09-03 裁決「zcode 優先」——ZCode 為主力 harness）：
#   硬 gate（fail-loud exit 1＋行動訊息；超限時**索引照寫出**〔--check 除外〕——
#     2026-09-05 S1/AIR-25 改 CC 式，官方 memory.md:401-403「write still succeeds +
#     error telling Claude to rewrite」；size gate 拒寫會停滯索引＝新條目不可見＝
#     召回斷裂。**errs 路徑（frontmatter 違規）同 CC 式（AIR-27）**：壞條目跳過、
#     合法條目照常寫出＋exit 1 列名壞檔——一個壞檔不擋全部條目投影：
#     A 形態 >22,500 字元 或 >190 行——守兩端共同截斷線（200 行／25,000 字元）
#     B 形態 >6,000 字元（常駐面；AIR-48 P3——12 條定額實測 ~3,600 留成長餘裕；
#       超限同 CC 式照寫：成員都在只是胖，停滯＝新常駐成員不可見）
#   bytes info（照常寫入、exit 0）：>24,000 bytes 印 [INFO] 一行——縱深預警
#     （非任何 harness 的實際截斷線：兩端皆量 chars；CJK 一字 3B，bytes 提前折射）
# B 形態（AIR-48 P3——顯式清單檔 opt-in，per-pool）：
#   池內存在 _resident-set.md → B 形態：MEMORY.md＝常駐段（清單條目行；rank 只排
#   集合內順序，不決定常駐資格——北極星既定）＋routing 行；_inventory.md＝全量投影
#   （底線前綴不進 harness 開場載入；尺寸無上界，rg 可達即成立——SM-4）。
#   缺清單檔的池維持現行 A 形態（他池刷新安全，不會誤切）。
#   常駐清單失效 fail-loud（R2）：清單 id 必須唯一解析到合法條目（命中數≠1：
#   列名不存在／frontmatter 損壞／池內重名）→ inventory 照寫（全量投影新鮮）、
#   **MEMORY.md 保留上一份常駐面**（不得發布缺必要成員的子集）＋exit 1。
#   雙檔發布順序（R3）：先原子發布 _inventory.md，成功後才發布 B 形態 MEMORY.md
#   ——inventory 寫入失敗＝不切換常駐面＋_inventory-write-failed marker＋exit 1
#   （不新增交易框架——單檔原子替換機制分兩步；成功路徑清 marker）。
#   流入率口徑（R4）：A 形態＝MEMORY.md chars；B 形態＝inventory chars（B 常駐面
#   ≈常數不得作為流入訊號）——輸出行自帶兩欄數字，消費端（lite 流入率/夜收斂）
#   依形態取數，禁不同口徑相減（首次切換重建基線）。
# 載入上限實證（2026-09-03 雙端源碼反組譯、CLI 三版同構；共用池＝ZCode symlink→Claude 實體）：
#   兩端同語義＝200 行 或 25,000 字元（UTF-16 code units，CJK 一字計 1）：
#     ZCode zcode.cjs：Vut=200／mre=25e3（Wut()：o=t.length 比較）
#     Claude versions/<v>：YD=200／GF=25000（mLe() 回傳 byteCount:t.length——
#       欄位名叫 byteCount、計量是 .length＝chars；TextEncoder 在另一 scope 屬
#       crypto——欄位名≠計量方式，minified 跨 scope 撞名勿再誤讀）
#   兩端超限皆截斷＋附 WARNING（非靜默）；「25KB」假象＝警告以 25000/1024 顯示 "24.4KB"
#   重跑驗證（drift 防護——量詞須彈性：常數前綴不足 100 字元，.{100} 會 0 hits）：
#     rg -a -o '.{30}mre=[0-9*]+.{30}' /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs
#     rg -a -o '.{0,100}YD=200,GF=25000.{0,60}' ~/.local/share/claude/versions/<最新版>
#     計量實作：perl -0777 -ne 'if (/(function mLe\(e\)\{.{0,300})/s){my $x=$1;$x=~s/\n/\\n/g;print "$x\n"}' <該版檔>
# 2026-09-06 輸出行附 gate 值（OK 兩路徑＋size FAIL 附超限比值）：nightly-watch 假警——
#   輸出不含 gate 值時，消費 session 轉引 _audit-state.md prose 舊值（18,500 vs 真值
#   22,500）＝輸出真空由 prose 填補（09-02 同型第二次）。輸出自足＝就地校驗。
# 寫入用 unique tmp（os.getpid()）＋只清 aged（>60s）殘檔——並行 process 的 in-flight
# tmp 不被誤殺。
# 2026-09-01 chars gate 17,000→18,500（harness 線內 ~25% 餘裕）：寫入治理
#   hook 上線（block-memory-index-write.py 擋 desc>120/膨脹>12,000）後流入率
#   下降，原 17,000 餘裕（~700）只撐一天（08-31 晚 16,308 → 隔晨 17,269 撞線）。
#   （hook 僅攔主 session——subagent 寫入不觸發；「流入率下降」以主 session 寫入為主）
# 2026-09-03 晚 chars gate 18,500→22,500（真線 90%）：寫入原則配套＋每日夜間收斂
#   cron 承接流出（user 裁定「有進有出」）——gate 即時閥語義下餘裕＝收斂反應時間，
#   夜間收斂前置清理使 jam 罕見，放寬安全。
# description 截斷線隨 hook DESC_LIMIT：140→120（09-01）→100（09-03 P1：硬限對齊
#   紀律值）——寫入端已擋，此為存量縱深。
# 條目 frontmatter 必含 name / description / type（頂層 `type:` 或 `metadata.type:` 皆可）。
# 語言層約束：跑在 hook runtime 系統 python3 3.9——禁 PEP 604（X | None）等 3.10+ 語法。
import os
import pathlib
import re
import sys
import time
from typing import NamedTuple

GATE_CHARS = 22_500
GATE_CHARS_B = 6_000  # B 形態常駐面 gate（AIR-48 P3；SKILL 層 1 prose 同值單一源）
TRUNCATE_DESC = 100  # desc 截斷線——須 == hooks/block-memory-index-write.py DESC_LIMIT（tests cross-layer 錨）
GATE_BYTES = 24_000
GATE_LINES = 190
RESIDENT_SET_NAME = "_resident-set.md"
INVENTORY_NAME = "_inventory.md"
INVENTORY_FAIL_MARKER = "_inventory-write-failed"
ORDER = [
    ("user", "User"),
    ("feedback", "Feedback"),
    ("project", "Project"),
    ("reference", "Reference"),
]
RANK_ORDER = {"hot": 0, "core": 1, "cold": 2}  # 缺省/invalid -> core（永不進 errs）
TYPE_ORDER = {t: i for i, (t, _) in enumerate(ORDER)}


def sort_key(e):
    """fail-soft 載入序：type 分組 × rank 層 × 組內 mtime 新在前（name 尾鍵可重現）。"""
    return (TYPE_ORDER[e.typ], e.rank, -e.mtime, e.name)


class Entry(NamedTuple):
    """索引條目——具名字段取代位置元組（AIR-39 post-build F1：e[4]/e[5] 位置耦合）。"""

    typ: str
    stem: str
    name: str
    hook: str
    rank: int
    mtime: float


def parse_frontmatter(text: str) -> dict:
    if not text.startswith(("---\n", "---\r\n")):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    out: dict = {}
    parent = None
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            k, _, v = line.strip().partition(":")
            if parent:
                out[f"{parent}.{k.strip()}"] = v.strip()
            continue
        k, _, v = line.partition(":")
        parent = k.strip() if not v.strip() else None
        out[k.strip()] = v.strip().strip("'\"")
    return out


def parse_rank(fm) -> int:
    # 雙落點（沿 type 先例：頂層 rank / metadata.rank）；巢狀值引號剝除
    # （parse_frontmatter 只剝頂層）；缺省/invalid 一律 core、永不進 errs。
    raw = fm.get("rank") or fm.get("metadata.rank")
    return RANK_ORDER.get(str(raw).strip().strip("'\"").lower(), RANK_ORDER["core"])


def write_atomic(here: pathlib.Path, name: str, content: str) -> None:
    """aged 殘檔清理＋tmp+replace 原子寫（只清 >60s 殘檔——並行 in-flight tmp 不誤殺）。"""
    now = time.time()
    for stale in here.glob(f"{name}.*.tmp"):
        try:
            if now - stale.stat().st_mtime > 60:
                stale.unlink()
        except OSError:
            pass
    tmp = here / f"{name}.{os.getpid()}.tmp"
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(here / name)


def write_index(here: pathlib.Path, content: str) -> None:
    write_atomic(here, "MEMORY.md", content)


def parse_resident_set(text: str) -> list:
    """清單檔解析：每行一個條目 id。

    相容三種行形態——backtick 包裹（`` `name`——註解 ``，necessity-set 直拷）、
    list/ordered marker（`- name`／`1. name`）、裸 name；# 註解與空行跳過。
    回傳 id 序列（清單內重複行由呼叫端去重渲染——同 id 無投影歧義，不 fail）。"""
    ids = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"`([^`]+)`", line)
        if m:
            ids.append(m.group(1).strip())
            continue
        line = re.sub(r"^([-*+]|\d+[.)])\s+", "", line)
        token = line.split()[0] if line.split() else ""
        if token:
            ids.append(token.strip("`"))
    return ids


def render_index_body(entries: list, header_title: str, header_note: str) -> str:
    """type 分組投影 body（A 形態 MEMORY.md 與 _inventory.md 共用渲染）。"""
    lines = [f"# {header_title}", "", header_note, ""]
    for typ, title in ORDER:
        group = [e for e in entries if e.typ == typ]
        if not group:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(f"- [{e.stem}]({e.name}) - {e.hook}" for e in group)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_b_form(resident_entries: list) -> str:
    """B 形態 MEMORY.md：常駐段（清單條目，沿 sort_key——rank 只排集合內順序）＋routing 行。"""
    lines = [
        "# Memory Index（B 形態——常駐定額）",
        "",
        "本檔為 _generate_index.py 機械投影，禁手寫（PreToolUse gate）——改條目檔後重跑 generator。",
        "常駐集合＝_resident-set.md 顯式清單；全量條目在 _inventory.md（rg 可達，不進開場）。",
        "",
    ]
    for typ, title in ORDER:
        group = [e for e in resident_entries if e.typ == typ]
        if not group:
            continue
        lines.append(f"## {title}（resident）")
        lines.append("")
        lines.extend(f"- [{e.stem}]({e.name}) - {e.hook}" for e in group)
        lines.append("")
    lines.append("## Routing")
    lines.append("")
    lines.append(
        "全量條目住 _inventory.md——`rg -i <關鍵詞> _inventory.md` 定位後 Read 條目檔 body；"
        "非常駐條目不進開場載入，任務需要時按需檢索。"
    )
    lines.append(
        "Pending 候選（inbox 待治理，provisional）住 _pending.md——canonical > pending："
        "有候選聲稱 X 時 canonical 仍為 Y，不得據此覆蓋 canonical（AIR-63）。"
    )
    return "\n".join(lines).rstrip() + "\n"


def rank_counts_line(entries: list) -> str:
    rank_hits = [sum(1 for e in entries if e.rank == i) for i in range(3)]
    line = f"rank 分層：hot={rank_hits[0]} core={rank_hits[1]} cold={rank_hits[2]}"
    if sum(rank_hits) and rank_hits[0] / sum(rank_hits) > 1 / 3:
        line += " —— [WARN] hot 佔比超 1/3（rank 通膨可疑）"
    return line


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    check_only = "--check" in sys.argv
    errs, entries = [], []
    for f in sorted(here.glob("*.md")):
        if f.name == "MEMORY.md" or f.name.startswith("_"):
            continue
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        typ = fm.get("type") or fm.get("metadata.type")
        desc = " ".join((fm.get("description") or "").split())
        if not (fm.get("name") and desc and typ in dict(ORDER)):
            errs.append(f"  {f.name}: type={typ!r}")
            continue
        hook = desc if len(desc) <= TRUNCATE_DESC else desc[: TRUNCATE_DESC - 1] + "…"
        entries.append(
            Entry(typ, f.stem, f.name, hook, parse_rank(fm), f.stat().st_mtime)
        )
    # fail-soft 載入序：type 分組 × rank 層 × 組內 mtime 新在前（name 尾鍵可重現）。
    entries.sort(key=sort_key)
    resident_set = here / RESIDENT_SET_NAME
    b_form = resident_set.exists()

    if b_form:
        return main_b_form(here, check_only, errs, entries, resident_set)
    return main_a_form(here, check_only, errs, entries)


def main_a_form(here, check_only, errs, entries) -> int:
    """A 形態（無清單檔）——現行投影路徑，行為不變。"""
    content = render_index_body(
        entries,
        "Memory Index",
        "本檔為 _generate_index.py 機械投影，禁手寫（PreToolUse gate）——改條目檔後重跑 generator。",
    )
    n_chars, n_lines = len(content), content.count("\n")
    n_bytes = len(content.encode("utf-8"))
    info = (
        f"[INFO] bytes {n_bytes} > {GATE_BYTES} — 縱深預警（兩端截斷線皆 25,000 chars；CJK 一字 3B，bytes 提前折射）\n"
        if n_bytes > GATE_BYTES
        else ""
    )
    if errs:
        print(
            info
            + "[FAIL] frontmatter 違規（需 name/description/type∈user|feedback|project|reference）"
            f"——{len(errs)} 檔跳過、未進索引：\n"
            + "\n".join(errs)
            + "\n[提示] 索引已以合法條目照常寫出（CC 式——壞條目不擋投影，AIR-27）；修好後重跑"
        )
        if not check_only:  # --check 零副作用（與 size gate 同 guard）
            write_index(here, content)
        return 1
    if n_chars > GATE_CHARS or n_lines > GATE_LINES:
        wrote = ""
        if not check_only:  # --check 零副作用語義不變（SM-2 guard）
            write_index(here, content)
            wrote = "——索引已寫出（不停滯）"
        print(
            info
            + f"[FAIL] gate 超限: {n_chars} chars (>{GATE_CHARS}, {n_chars / GATE_CHARS:.1%})"
            f" / {n_lines} lines (>{GATE_LINES}, {n_lines / GATE_LINES:.1%}){wrote}。當下 session 需縮：merge or drop stale 條目"
            "（可推導內容歸 repo/git——skip-derivable），縮後重跑"
        )
        return 1
    if check_only:
        print(
            info
            + f"[OK] {len(entries)} entries, {n_chars} chars, {n_bytes} bytes, {n_lines} lines"
            f"（gate: {GATE_CHARS} chars／{GATE_BYTES} bytes／{GATE_LINES} 行；--check 未寫入）\n"
            + rank_counts_line(entries)
        )
        return 0
    write_index(here, content)
    print(
        info
        + f"[OK] MEMORY.md 已重生成: {len(entries)} entries, {n_chars} chars, {n_bytes} bytes, {n_lines} lines"
        f"（gate: {GATE_CHARS} chars／{GATE_BYTES} bytes／{GATE_LINES} 行）\n"
        + rank_counts_line(entries)
    )
    return 0


def main_b_form(here, check_only, errs, entries, resident_set) -> int:
    """B 形態（清單檔在場）——常駐面＋inventory 雙檔，先 inventory 後常駐面（R3）。"""
    resident_ids = parse_resident_set(resident_set.read_text(encoding="utf-8"))
    # 唯一解析（R2）：清單 id 對條目 stem（檔名去 .md——天然唯一、與索引顯示名同源；
    # 存量有 frontmatter name≠stem 分離案例，fm_name 不受檔名唯一性保護）的命中數
    # 必須 ==1（0＝列名不存在/frontmatter 損壞——壞檔已進 errs 不在 entries）。
    counts = {}
    for e in entries:
        counts[e.stem] = counts.get(e.stem, 0) + 1
    unresolvable = [rid for rid in resident_ids if counts.get(rid, 0) != 1]
    if unresolvable:
        # inventory 照寫（全量投影新鮮、不依賴清單）；MEMORY.md 保留上一份常駐面
        # （不得發布缺必要成員的子集）；--check 零副作用。
        if not check_only:
            write_atomic(
                here,
                INVENTORY_NAME,
                render_index_body(
                    entries,
                    "Memory Inventory（全量投影）",
                    "本檔為 _generate_index.py 機械投影，禁手寫——全量條目住此（底線前綴不進開場）；rg 可達。",
                ),
            )
        uniq = sorted(set(unresolvable))
        print(
            "[FAIL] 常駐清單無法唯一解析（缺檔／壞 frontmatter／重名——清單 id 命中合法條目 ≠1）：\n"
            + "\n".join(f"  {rid}" for rid in uniq)
            + "\nMEMORY.md 保留上一份常駐面未切換；_inventory.md 已照寫。"
            "修正：修 frontmatter／同步清單（rename 走集合確認流程——user 凍結）後重跑"
        )
        return 1
    resident_entries = sorted(
        [e for e in entries if e.stem in set(resident_ids)], key=sort_key
    )
    b_content = render_b_form(resident_entries)
    inv_content = render_index_body(
        entries,
        "Memory Inventory（全量投影）",
        "本檔為 _generate_index.py 機械投影，禁手寫——全量條目住此（底線前綴不進開場）；rg 可達。",
    )
    n_chars, n_lines = len(b_content), b_content.count("\n")
    inv_chars = len(inv_content)
    inv_lines = inv_content.count("\n")

    if check_only:
        if errs:
            print(
                "[FAIL] frontmatter 違規（需 name/description/type∈user|feedback|project|reference）"
                f"——{len(errs)} 檔跳過、未進 inventory：\n"
                + "\n".join(errs)
                + "\n[提示] --check 未寫入；修好後重跑"
            )
            return 1
        if n_chars > GATE_CHARS_B:
            print(
                f"[FAIL] B gate 超限: 常駐面 {n_chars} chars (>{GATE_CHARS_B}, {n_chars / GATE_CHARS_B:.1%})"
                f"／_inventory.md: {len(entries)} entries, {inv_chars} chars。需縮常駐清單或壓 desc，縮後重跑\n"
                + rank_counts_line(entries)
            )
            return 1
        print(
            f"[OK] {len(resident_entries)} resident, {n_chars} chars, {n_lines} lines"
            f"（B gate: {GATE_CHARS_B} chars）／_inventory.md: {len(entries)} entries, {inv_chars} chars, {inv_lines} lines"
            "（--check 未寫入）\n" + rank_counts_line(entries)
        )
        return 0

    # R3 發布順序：先原子發布 inventory；失敗＝不切常駐面＋marker＋exit 1。
    try:
        write_atomic(here, INVENTORY_NAME, inv_content)
    except OSError as exc:
        try:
            (here / INVENTORY_FAIL_MARKER).write_text(
                f"inventory 寫入失敗：{exc}——常駐面未切換；修復後重跑自動移除本標記\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        print(
            f"[FAIL] _inventory.md 寫入失敗（{exc}）——不切換常駐面（MEMORY.md 保留原狀）"
            f"＋已留 {INVENTORY_FAIL_MARKER} marker。修復（磁碟/權限）後重跑"
        )
        return 1
    try:
        if (here / INVENTORY_FAIL_MARKER).exists():
            (here / INVENTORY_FAIL_MARKER).unlink()
    except OSError:
        pass

    # 常駐面照寫（CC 式——errs／gate 超限皆不停滯：成員都在，寫出面＝新鮮投影）。
    write_index(here, b_content)
    if errs:
        print(
            "[FAIL] frontmatter 違規（需 name/description/type∈user|feedback|project|reference）"
            f"——{len(errs)} 檔跳過、未進 inventory：\n"
            + "\n".join(errs)
            + "\n[提示] inventory 已以合法條目照常寫出（CC 式，AIR-27）；修好後重跑"
        )
        return 1
    if n_chars > GATE_CHARS_B:
        print(
            f"[FAIL] B gate 超限: 常駐面 {n_chars} chars (>{GATE_CHARS_B}, {n_chars / GATE_CHARS_B:.1%})"
            "——常駐面已寫出（不停滯）。需縮常駐清單或壓 desc，縮後重跑\n"
            + rank_counts_line(entries)
        )
        return 1
    print(
        f"[OK] MEMORY.md（B 形態）已重生成: {len(resident_entries)} resident, {n_chars} chars, {n_lines} lines"
        f"（B gate: {GATE_CHARS_B} chars）／_inventory.md: {len(entries)} entries, {inv_chars} chars, {inv_lines} lines\n"
        + rank_counts_line(entries)
        + f"\n流入率口徑（B）＝inventory chars: {inv_chars}（A 形態口徑＝MEMORY.md chars——禁跨口徑相減）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
