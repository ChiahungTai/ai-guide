#!/usr/bin/env python3
"""PROJECTION 段生成器——每卡機械生成投影（135.2 AC#3 投影面契約，0919 三腿裁決）。

鐵律：只寫 <!-- PROJECTION:BEGIN/END --> 隔離區（整段 replace）；白話＝Notes 最新
「白話：」行機械 lift（投影只搬運不創作）；hash 錨＝卡面減投影段；regen 冪等
（兩次執行 bit-identical）。寫卡面屬 single-writer 權——僅 owning/board-control session 跑。
"""
import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "backlog" / "tasks"
IDS = ["AIR-135", "AIR-135.1", "AIR-135.2", "AIR-135.3", "AIR-135.4",
       "AIR-135.5", "AIR-135.6", "AIR-135.7", "AIR-135.8"]
BEGIN, END = "<!-- PROJECTION:BEGIN -->", "<!-- PROJECTION:END -->"


def find(pid: str) -> Path:
    return next(TASKS.glob(f"{pid.lower()} -*.md"))


def load_all() -> dict:
    cards = {}
    for pid in IDS:
        p = find(pid)
        text = p.read_text(encoding="utf-8")
        status = re.search(r"^status:\s*(.+)$", text, re.MULTILINE).group(1).strip()
        deps = re.findall(r"^\s*-\s*(AIR-[\w.]+)\s*$", text, re.MULTILINE)
        ac_done = len(re.findall(r"^- \[x\] #", text, re.MULTILINE))
        ac_open = len(re.findall(r"^- \[ \] #", text, re.MULTILINE))
        baihua_m = re.findall(r"^白話：(.+)$", text, re.MULTILINE)
        # F1 修正：白話只從 SECTION:NOTES 區 lift——禁讀投影段自身輸出（防 self-feedback）
        notes_m = re.search(r"<!-- SECTION:NOTES:BEGIN -->(.*?)<!-- SECTION:NOTES:END -->", text, re.DOTALL)
        baihua_notes = re.findall(r"^白話：(.+)$", notes_m.group(1), re.MULTILINE) if notes_m else []
        cards[pid] = {"path": p, "text": text, "status": status, "deps": deps,
                      "ac": f"{ac_done}/{ac_done + ac_open}", "baihua": baihua_notes[-1] if baihua_notes else "（未寫）"}
    for pid, c in cards.items():
        c["rdeps"] = [o for o, oc in cards.items() if pid in oc["deps"]]
    return cards


def projection_body(c: dict) -> str:
    deps = "、".join(c["deps"]) or "無——起點"
    rdeps = "、".join(c["rdeps"]) or "無"
    return (f"白話：{c['baihua']}\n"
            f"要等：{deps}\n擋誰：{rdeps}\n"
            f"現況：{c['status']}；AC {c['ac']}")


def source_hash(text_wo: str) -> str:
    # 135.2 契約：hash 排除投影段自身＋排除 updated_date（防 regen→日期變→hash 變 自激）
    text_wo = re.sub(r"(?m)^updated_date:.*$\n?", "", text_wo)
    return hashlib.sha256(text_wo.encode()).hexdigest()[:12]


def render(text: str, c: dict) -> str:
    text_wo = text.split(BEGIN)[0].rstrip()
    src_hash = source_hash(text_wo)
    block = (f"{BEGIN}\n{projection_body(c)}\n"
             f"源 hash：{src_hash}（卡面減投影段；不符即 stale）\n{END}")
    return text_wo + "\n\n" + block + "\n"


def main() -> None:
    cards = load_all()
    for pid, c in cards.items():
        new_text = render(c["path"].read_text(encoding="utf-8"), c)
        c["path"].write_text(new_text, encoding="utf-8")
        print(f"[projection] {pid} hash={source_hash(new_text.split(BEGIN)[0].rstrip())}")
    # 冪等驗證：以當前檔重算應 bit-identical
    for pid, c in cards.items():
        before = c["path"].read_text(encoding="utf-8")
        if render(before, c) != before:
            print(f"[projection] ⚠️ {pid} 非冪等——hash 錨計算有誤")
            raise SystemExit(1)
    print("[projection] 冪等 PASS（二次執行 bit-identical）")


if __name__ == "__main__":
    main()
