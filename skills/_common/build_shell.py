# build_shell.py——shell-ready md → 報告殼確定性 codegen（AIR-73）
"""shell-ready md → 報告殼（report shell）確定性 codegen＋三級 gate。

落點契約（卡面 desc 為設計權威；.agent-tmp/illupatch-synthesis.md 已不存在於兩 repo）：
- lossless 分流：本 builder 只做 lossless 全量投影（md 每個語義葉進殼、順序全等）；
  mode: curated 的殼由手維護，builder 拒絕（fail loud）。
- shell-ready md 契約：frontmatter task identity contract（card_id／task_baseline 必填——
  codex v2 blind spot 規格化）＋diagram_heights keyed by diagram id（與 body
  diagram-assign id-multiset 全等鎖死）＋report_type 折疊預設映射（開放語義：
  已知 report_type 用表內預設；未知 report_type 全部 fold 預設收合＋warning，非 hard
  fail——卡面只授權「預設映射」）＋task_type 圖預設。
- 三級 gate：hard 六項（ordered semantic leaves 全等＋屬性臂 href/iframe src 有序比對
  ／首屏 active 行為面／折疊不重載 行為面／aria＋localStorage 行為面／meta
  completeness／確定性重跑）＋mutation 七型（測試端防同源自洽，見 tests/test_build_shell.py）。
- 祖父＋碰觸遷移：目標檔無 built-by marker → 拒絕覆寫（legacy-curated 維持手填）；
  有 marker → 重生（regeneration contract）；輸出目標是 symlink → 拒絕；寫入走
  tmp＋os.replace 原子寫。
- 樣式/互動參照源：同目錄 illustrate-report-shell.html（唯讀）。本檔內嵌其 CSS/JS 同步
  副本（@9936ce5）——改殼行為先改模板再同步此處；gate 以內嵌 canonical JS 錨定行為面。

shell-ready md 範例：

    ---
    card_id: AIR-73
    task_baseline: 9936ce5
    title: 報告標題
    report_type: task-plan
    task_type: architecture
    diagram_heights:
      arch: 640
    ---

    <!-- section-group: {"id": "overview", "title": "① 總覽", "sub": "一句話"} -->
    段落（一行一葉）。**粗體**、`code`、[連結](ep.md)。

    - 清單葉一
    - 清單葉二

    <!-- fold: appendix -->
    摺疊群組內文（預設開合由 report_type 映射決定）。

    <!-- section-group: {"id": "source", "title": "② 回源", "sub": "殼是展示層"} -->
    <!-- diagram-assign: {"id": "arch", "src": "diagram-architecture.html", "title": "架構圖"} -->
"""

import html as _html
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

BUILDER_NAME = "build_shell.py"
BUILDER_VERSION = "1.0.0"
MARKER_PREFIX = "built-by: build_shell.py"

_LOG = logging.getLogger("skills._common.build_shell")

# ── 折疊/圖型預設映射（開放語義單一源）────────────────────────────

# report_type → fold group 預設開合（成果殼 delta-report 加強前後對比與機制講解——09-15 輸入④）。
# 開放語義：已知 report_type 用表內預設；表外（未知 report_type 或未知組合）全部預設收合
# ＋warning log——非 hard fail（外審 A：卡面只授權「預設映射」）。
REPORT_TYPE_FOLD_DEFAULTS: dict[str, dict[str, bool]] = {
    "task-plan": {"appendix": False, "mechanism": True},
    "delta-report": {"comparison": True, "mechanism": True, "appendix": False},
    "study-notes": {"appendix": True, "evidence": True},
}

FOLD_LABELS: dict[str, str] = {
    "appendix": "附錄",
    "evidence": "證據",
    "comparison": "前後對比",
    "mechanism": "機制講解",
}

# task 型態圖預設：UI→mockup、流程→流程圖、演算法→步驟圖解、架構→架構圖講解（09-15 輸入②）
TASK_TYPE_DIAGRAM_PRESET: dict[str, str] = {
    "ui": "UI mockup 圖",
    "flow": "流程圖",
    "algorithm": "步驟圖解",
    "architecture": "架構圖講解",
    "none": "mermaid 圖",
}

STATUS_BADGES: dict[str, str] = {
    "plan": "📋 計畫",
    "progress": "🟡 進行中",
    "done": "✅ 完成",
}

DIAGRAM_PRESET_NONE = "none"


class BuildError(Exception):
    """契約違反——fail loud（crash-only），禁靜默降級。"""


class InputError(BuildError):
    """輸入讀取失敗（檔案缺失／非 UTF-8）——仍是 fail loud，但 exit 2 與契約紅 3 分流。"""


# ── frontmatter（自製最小解析器；依賴零）───────────────────────────


@dataclass
class ShellMeta:
    card_id: str
    task_baseline: str
    title: str
    report_type: str
    mode: str = "lossless"
    task_type: str = DIAGRAM_PRESET_NONE
    status: str = "plan"
    ep_path: str | None = None
    diagram_heights: dict[str, int] = field(default_factory=dict)


_FM_REQ = ("card_id", "task_baseline", "title", "report_type")


def parse_frontmatter(md: str) -> tuple[ShellMeta, str]:
    lines = md.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BuildError("frontmatter 缺失（檔首必須是 --- 開頭的 YAML 子集）")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise BuildError("frontmatter 未閉合（缺第二個 ---）")
    raw: dict[str, str] = {}
    heights: dict[str, int] = {}
    in_heights = False
    for line in lines[1:end]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if in_heights:
            if line[:1].isspace():
                key, _, val = line.strip().partition(":")
                if not key or not val.strip():
                    raise BuildError(f"diagram_heights 項目不合法：{line!r}")
                try:
                    h = int(val.strip())
                except ValueError as e:
                    raise BuildError(f"diagram_heights 高度必須是整數：{line!r}") from e
                if h <= 0:
                    raise BuildError(f"diagram_heights 高度必須為正：{line!r}")
                heights[key.strip()] = h
                continue
            in_heights = False
        key, sep, val = line.partition(":")
        if not sep:
            raise BuildError(f"frontmatter 行不合法：{line!r}")
        key, val = key.strip(), val.strip()
        if key == "diagram_heights":
            in_heights = True
            continue
        raw[key] = val
    missing = [k for k in _FM_REQ if k not in raw]
    if missing:
        raise BuildError(f"frontmatter 缺必填欄位（task identity contract）：{', '.join(missing)}")
    meta = ShellMeta(
        card_id=raw["card_id"],
        task_baseline=raw["task_baseline"],
        title=raw["title"],
        report_type=raw["report_type"],
        mode=raw.get("mode", "lossless"),
        task_type=raw.get("task_type", DIAGRAM_PRESET_NONE),
        status=raw.get("status", "plan"),
        ep_path=raw.get("ep_path") or None,
        diagram_heights=heights,
    )
    if meta.mode != "lossless":
        raise BuildError(
            f"mode={meta.mode}：curated 殼由手維護，非本 builder 範圍（lossless 分流）"
        )
    # report_type 開放語義（外審 A）：未知值不在此 hard fail——渲染期全部 fold 預設收合＋warning。
    if meta.task_type not in TASK_TYPE_DIAGRAM_PRESET:
        raise BuildError(
            f"未知 task_type={meta.task_type!r}；可用：{sorted(TASK_TYPE_DIAGRAM_PRESET)}"
        )
    if meta.status not in STATUS_BADGES:
        raise BuildError(f"未知 status={meta.status!r}；可用：{sorted(STATUS_BADGES)}")
    return meta, "\n".join(lines[end + 1 :])


# ── body 解析：section-group／diagram-assign／fold＋語義葉 ─────────


@dataclass
class SectionSpec:
    id: str
    title: str
    sub: str | None = None


@dataclass
class DiagramSpec:
    id: str
    title: str
    src: str | None = None


type Event = tuple[str, object]
# ("section", SectionSpec) | ("diagram", DiagramSpec) | ("fold", str) | ("leaf", (kind, text))

_SEC_RE = re.compile(r"^<!--\s*section-group:\s*(\{.*\})\s*-->$")
_DIA_RE = re.compile(r"^<!--\s*diagram-assign:\s*(\{.*\})\s*-->$")
_FOLD_RE = re.compile(r"^<!--\s*fold:\s*(\S+)\s*-->$")
_LIST_RE = re.compile(r"^(?:-|\*|\d+\.)\s+(.*)$")
_ROW_SKIP_RE = re.compile(r"^:?-{3,}:?$")


def norm_inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_body(body: str) -> list[Event]:
    events: list[Event] = []
    in_fence = False
    fence_buf: list[str] = []
    for raw in body.splitlines():
        if in_fence:
            if raw.strip().startswith("```"):
                events.append(("leaf", ("code", "\n".join(fence_buf))))
                in_fence = False
                fence_buf = []
            else:
                fence_buf.append(raw)
            continue
        st = raw.strip()
        if st.startswith("```"):
            in_fence = True
            fence_buf = []
            continue
        if not st:
            continue
        if st.startswith("<!--"):
            m = _SEC_RE.match(st)
            if m:
                spec = json.loads(m.group(1))
                if "id" not in spec or "title" not in spec:
                    raise BuildError(f"section-group 缺 id/title：{st!r}")
                events.append(
                    ("section", SectionSpec(spec["id"], spec["title"], spec.get("sub")))
                )
                continue
            m = _DIA_RE.match(st)
            if m:
                spec = json.loads(m.group(1))
                if "id" not in spec or "title" not in spec:
                    raise BuildError(f"diagram-assign 缺 id/title：{st!r}")
                events.append(
                    ("diagram", DiagramSpec(spec["id"], spec["title"], spec.get("src")))
                )
                continue
            m = _FOLD_RE.match(st)
            if m:
                events.append(("fold", m.group(1)))
                continue
            continue  # 非契約註解——忽略
        if st.startswith("### "):
            events.append(("leaf", ("h3", norm_inline(st[4:]))))
            continue
        if st.startswith("## "):
            events.append(("leaf", ("h2", norm_inline(st[3:]))))
            continue
        if st.startswith(">"):
            events.append(("leaf", ("note", norm_inline(st.lstrip("> ")))))
            continue
        m = _LIST_RE.match(st)
        if m:
            events.append(("leaf", ("li", norm_inline(m.group(1)))))
            continue
        if st.startswith("|") and st.endswith("|"):
            cells = [c.strip() for c in st[1:-1].split("|")]
            if cells and all(_ROW_SKIP_RE.match(c) for c in cells):
                continue
            events.append(("leaf", ("row", norm_inline(" | ".join(cells)))))
            continue
        events.append(("leaf", ("p", norm_inline(st))))
    if in_fence:
        raise BuildError("code fence 未閉合")
    return events


def _diagram_ids(events: list[Event]) -> list[str]:
    ids: list[str] = []
    for kind, payload in events:
        if kind == "diagram":
            assert isinstance(payload, DiagramSpec)
            ids.append(payload.id)
    return ids


def _md_leaves_from(meta: ShellMeta, events: list[Event]) -> list[tuple[str, str]]:
    leaves: list[tuple[str, str]] = []
    for kind, payload in events:
        if kind == "section":
            assert isinstance(payload, SectionSpec)
            leaves.append(("h2", norm_inline(payload.title)))
            if payload.sub:
                leaves.append(("p", norm_inline(payload.sub)))
        elif kind == "diagram":
            assert isinstance(payload, DiagramSpec)
            leaves.append(("p", norm_inline(payload.title)))
        elif kind == "leaf":
            leaves.append(payload)  # type: ignore[arg-type]
    return leaves


def md_leaves(md: str) -> list[tuple[str, str]]:
    """shell-ready md → 有序語義葉（gate 全等對照的 md 側基準）。"""
    meta, body = parse_frontmatter(md)
    return _md_leaves_from(meta, parse_body(body))


# ── HTML 渲染（canonical 殼；CSS/JS 內嵌自 illustrate-report-shell.html）──

CSS = """  :root{
    --bg:#0d1117; --panel:#161b22; --panel2:#1c2129; --border:#30363d;
    --fg:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --green:#3fb950;
    --amber:#d29922; --rose:#f85149; --violet:#bc8cff;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{background:var(--bg);color:var(--fg);font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;display:flex}
  nav#sidebar{width:264px;min-width:264px;background:var(--panel);border-right:1px solid var(--border);padding:20px 0;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto;overflow-x:hidden;transition:width .18s ease,min-width .18s ease,padding .18s ease}
  nav#sidebar .brand{padding:0 20px 16px;border-bottom:1px solid var(--border);white-space:normal}
  nav#sidebar .brand .badge{display:inline-block;border-radius:12px;padding:2px 10px;font-size:13px;font-weight:600;white-space:nowrap}
  nav#sidebar .brand .badge.plan{background:#1f6f3c33;border:1px solid #2ea04366;color:var(--green)}
  nav#sidebar .brand .badge.progress{background:#2d220066;border:1px solid #d2992266;color:var(--amber)}
  nav#sidebar .brand .badge.done{background:#1f6f3c33;border:1px solid #2ea04366;color:var(--green)}
  nav#sidebar .brand h1{font-size:15.5px;margin-top:8px;line-height:1.45}
  nav#sidebar .brand .meta{font-size:11.5px;color:var(--muted);margin-top:8px;line-height:1.7;font-family:ui-monospace,Menlo,monospace}
  nav#sidebar ul{list-style:none;padding:10px 0;flex:1}
  nav#sidebar li a{display:flex;align-items:center;gap:10px;padding:9px 20px;color:var(--muted);text-decoration:none;font-size:13.5px;border-left:2px solid transparent;white-space:nowrap}
  nav#sidebar li a .num{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--fg);background:var(--panel2);border:1px solid var(--border);border-radius:5px;padding:1px 6px;min-width:26px;text-align:center}
  nav#sidebar li a:hover{color:var(--fg);background:#1f242c}
  nav#sidebar li a.active{color:var(--fg);background:#1f242c;border-left-color:var(--accent)}
  nav#sidebar .backlinks{padding:14px 20px;border-top:1px solid var(--border);font-size:12px;line-height:2;white-space:nowrap}
  nav#sidebar .backlinks a{color:var(--accent);text-decoration:none}
  body.sidebar-collapsed nav#sidebar{width:0;min-width:0;padding-left:0;padding-right:0;border-right:0}
  body.sidebar-collapsed main{max-width:none}
  main{flex:1;min-width:0;max-width:1480px;padding:26px 34px;overflow-y:auto}
  section{display:none}
  section.active{display:block}
  section h2{font-size:20px;margin-bottom:4px}
  section .sub{color:var(--muted);font-size:13px;margin-bottom:18px}
  section h3{font-size:14.5px;color:var(--accent);margin:18px 0 8px}
  p,li{font-size:14px;line-height:1.75;color:var(--fg)}
  ul.dots{list-style:none;margin:6px 0}
  ul.dots li{padding-left:18px;position:relative;margin:4px 0}
  ul.dots li::before{content:"";position:absolute;left:2px;top:9px;width:6px;height:6px;border-radius:50%;background:var(--accent)}
  .frame-wrap{margin-top:14px;border:1px solid var(--border);border-radius:10px;overflow:hidden;background:var(--panel)}
  .frame-wrap .bar{display:flex;justify-content:space-between;align-items:center;padding:8px 14px;border-bottom:1px solid var(--border);font-size:12px;color:var(--muted);font-family:ui-monospace,Menlo,monospace}
  .frame-wrap .bar a{color:var(--accent);text-decoration:none}
  iframe{width:100%;height:calc(100vh - 190px);min-height:640px;border:0;display:block;background:#fff}
  .frame-wrap.degraded .degraded-body{padding:22px 18px;font-size:13.5px;line-height:1.8;color:var(--muted)}
  .frame-wrap.degraded .degraded-body b{color:var(--fg)}
  table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13px}
  th,td{border:1px solid var(--border);padding:7px 11px;text-align:left;vertical-align:top;line-height:1.6}
  th{background:var(--panel2);color:var(--muted);font-weight:600;font-size:12px}
  td code{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--accent);background:#1b222c;border-radius:4px;padding:1px 5px}
  .flow{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;line-height:1.9;color:var(--fg);background:#161b22;border:1px solid var(--border);border-radius:10px;padding:14px 18px;overflow-x:auto;white-space:pre;margin:10px 0}
  .note{border-left:3px solid var(--amber);background:#2d220066;padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;line-height:1.7;margin:12px 0}
  details{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin:12px 0}
  summary{cursor:pointer;color:var(--accent);font-size:13.5px}
  .collapse-tab{position:fixed;top:50%;z-index:30;width:26px;height:64px;padding:0;cursor:pointer;background:var(--panel2);border:1px solid var(--border);color:var(--muted);font-size:13px;line-height:1;border-radius:0 8px 8px 0}
  .collapse-tab:hover{color:var(--fg);border-color:var(--accent)}
  #collapse-btn{left:264px;transform:translateY(-50%)}
  body.sidebar-collapsed #collapse-btn{display:none}
  #expand-btn{left:0;top:20px;transform:none;border-radius:0 8px 8px 0;display:none}
  body.sidebar-collapsed #expand-btn{display:block}"""

# 內嵌自 skills/_common/illustrate-report-shell.html（@9936ce5）——三硬約束的行為錨：
# ① init 首屏＝首個含 .frame-wrap 的章節（AIR-14）② setCollapsed 只切 body class（不重載）
# ③ <button>＋aria-expanded＋localStorage 記憶
CANONICAL_JS = """function go(id,el){
  var section=document.getElementById(id);
  if(!section||!section.matches('main section'))return false;
  document.querySelectorAll('main section').forEach(s=>s.classList.remove('active'));
  section.classList.add('active');
  document.querySelectorAll('#sidebar li a').forEach(a=>a.classList.remove('active'));
  if(el)el.classList.add('active');
  history.replaceState(null,'','#'+id);
  return false;
}
var SIDEBAR_KEY='illustrate-shell-sidebar-collapsed';
function setCollapsed(c,moveFocus){
  document.body.classList.toggle('sidebar-collapsed',!!c);
  try{localStorage.setItem(SIDEBAR_KEY,c?'1':'0');}catch(e){}
  var sidebar=document.getElementById('sidebar');
  sidebar.toggleAttribute('inert',!!c);
  if(c)sidebar.setAttribute('aria-hidden','true');else sidebar.removeAttribute('aria-hidden');
  document.querySelectorAll('#collapse-btn,#expand-btn').forEach(function(b){
    b.setAttribute('aria-expanded',String(!c));
  });
  if(moveFocus)document.getElementById(c?'expand-btn':'collapse-btn').focus();
  return false;
}
(function init(){
  // 折疊態先於首屏恢復（只改 nav 寬度，不碰 iframe/section——不觸發重載）
  var c=false;
  try{c=localStorage.getItem(SIDEBAR_KEY)==='1';}catch(e){}
  if(c)setCollapsed(true);
  // hash restore 優先；無 hash 時首屏＝首個含 .frame-wrap 的章節（.degraded 計入），都無則首章（AIR-14）
  var h=location.hash.slice(1);
  var candidate=h&&document.getElementById(h);
  var target=(candidate&&candidate.matches('main section'))?h:null;
  if(!target){
    var framed=document.querySelector('main section .frame-wrap');
    target=framed?framed.closest('section').id:document.querySelector('main section').id;
  }
  var link=document.querySelector('#sidebar li a[href="#'+target+'"]');
  go(target,link);
})();"""

_BTN_COLLAPSE = (
    '<button type="button" id="collapse-btn" class="collapse-tab" '
    'aria-expanded="true" aria-controls="sidebar" aria-label="收合章節導覽" '
    'onclick="return setCollapsed(true,true)">‹</button>'
)
_BTN_EXPAND = (
    '<button type="button" id="expand-btn" class="collapse-tab" '
    'aria-expanded="false" aria-controls="sidebar" aria-label="展開章節導覽" '
    'onclick="return setCollapsed(false,true)">›</button>'
)


def render_inline(text: str) -> str:
    t = _html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def _render_frame(spec: DiagramSpec, height: int | None, task_type: str) -> str:
    title_esc = _html.escape(spec.title, quote=True)
    if spec.src:
        src = _html.escape(spec.src, quote=True)
        style = f' style="height:{height}px;min-height:0"' if height else ""
        return (
            '<div class="frame-wrap">\n'
            f'<div class="bar"><span>{_html.escape(spec.title, quote=False)}</span>'
            f'<a href="{src}" target="_blank">↗ 全屏</a></div>\n'
            f'<iframe src="{src}?embed=1" title="{title_esc}"{style}></iframe>\n'
            "</div>"
        )
    preset = TASK_TYPE_DIAGRAM_PRESET[task_type]
    return (
        '<div class="frame-wrap degraded">\n'
        f'<div class="bar"><span>{_html.escape(spec.title, quote=False)}</span></div>\n'
        f'<div class="degraded-body"><b>圖尚未產生</b>——預設圖型：{preset}'
        "。渲染與重生規則見 skills/_common/illustrate-html-mode.md「重生」段。</div>\n"
        "</div>"
    )


def _render_section_items(
    items: list[Event], report_type: str, task_type: str, heights: dict[str, int]
) -> list[str]:
    fold_table = REPORT_TYPE_FOLD_DEFAULTS.get(report_type, {})
    out: list[str] = []
    state = {"details": False, "run": ""}

    def close_run() -> None:
        if state["run"] == "li":
            out.append("</ul>")
        elif state["run"] == "row":
            out.append("</table>")
        state["run"] = ""

    def close_details() -> None:
        if state["details"]:
            out.append("</details>")
            state["details"] = False

    for kind, payload in items:
        if kind == "fold":
            group = str(payload)
            if group not in FOLD_LABELS:
                raise BuildError(f"未知 fold group={group!r}；可用：{sorted(FOLD_LABELS)}")
            open_default = fold_table.get(group)
            if open_default is None:
                # 開放語義（外審 A）：已知 group 無映射 → 預設收合＋warning，非 hard fail
                _LOG.warning(
                    "build_shell: fold group=%r 無 report_type=%r 折疊預設——預設收合（開放語義）",
                    group,
                    report_type,
                )
                open_default = False
            close_run()
            close_details()
            out.append("<details open>" if open_default else "<details>")
            out.append(f"<summary>{FOLD_LABELS[group]}</summary>")
            state["details"] = True
            continue
        if kind == "diagram":
            assert isinstance(payload, DiagramSpec)
            close_run()
            out.append(_render_frame(payload, heights.get(payload.id), task_type))
            continue
        assert isinstance(payload, tuple)
        leaf_kind, text = str(payload[0]), str(payload[1])
        if leaf_kind == "li":
            if state["run"] != "li":
                close_run()
                out.append('<ul class="dots">')
            out.append(f"<li>{render_inline(text)}</li>")
            state["run"] = "li"
            continue
        if leaf_kind == "row":
            if state["run"] != "row":
                close_run()
                out.append("<table>")
            cells = [c.strip() for c in text.split(" | ")]
            tag = "th" if state["run"] != "row" else "td"
            out.append(
                "<tr>"
                + "".join(f"<{tag}>{render_inline(c)}</{tag}>" for c in cells)
                + "</tr>"
            )
            state["run"] = "row"
            continue
        close_run()
        if leaf_kind == "code":
            out.append(f'<div class="flow">{_html.escape(text, quote=False)}</div>')
        elif leaf_kind == "note":
            out.append(f'<div class="note">{render_inline(text)}</div>')
        else:
            out.append(f"<{leaf_kind}>{render_inline(text)}</{leaf_kind}>")
    close_run()
    close_details()
    return out


def render_html(meta: ShellMeta, events: list[Event], source_name: str) -> str:
    sections: list[tuple[SectionSpec, list[Event]]] = []
    for ev in events:
        kind, payload = ev
        if kind == "section":
            assert isinstance(payload, SectionSpec)
            sections.append((payload, []))
            continue
        if kind in ("diagram", "fold", "leaf"):
            if not sections:
                raise BuildError("section-group 標記前不得有 diagram/fold/內容葉（殼由章節組成）")
            sections[-1][1].append(ev)

    sec_ids = [spec.id for spec, _items in sections]
    dup_sec = sorted({i for i in sec_ids if sec_ids.count(i) > 1})
    if dup_sec:
        raise BuildError(f"section-group id 重複：{dup_sec}")
    dia_ids = _diagram_ids(events)
    dup_dia = sorted({i for i in dia_ids if dia_ids.count(i) > 1})
    if dup_dia:
        raise BuildError(f"diagram-assign id 重複：{dup_dia}")
    if sorted(meta.diagram_heights) != sorted(dia_ids):
        raise BuildError(
            "diagram_heights 與 diagram-assign key-set 不全等（multiset 鎖死）："
            f"frontmatter={sorted(meta.diagram_heights)} body={sorted(dia_ids)}"
        )
    if meta.report_type not in REPORT_TYPE_FOLD_DEFAULTS:
        _LOG.warning(
            "build_shell: report_type=%r 無折疊預設映射——全部 fold 預設收合（開放語義）",
            meta.report_type,
        )

    parts: list[str] = []
    parts.append('<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>')
    parts.append('<meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append(f"<title>{_html.escape(meta.title, quote=False)}</title>")
    parts.append("<style>")
    parts.append(CSS)
    parts.append("</style>\n</head>\n<body>")
    parts.append(_BTN_EXPAND)
    parts.append('<nav id="sidebar" aria-label="章節導覽">')
    parts.append('  <div class="brand">')
    parts.append(f'    <span class="badge {meta.status}">{STATUS_BADGES[meta.status]}</span>')
    parts.append(f"    <h1>{_html.escape(meta.title, quote=False)}</h1>")
    parts.append(
        f'    <div class="meta">卡 {_html.escape(meta.card_id, quote=False)} · '
        f"baseline {_html.escape(meta.task_baseline, quote=False)}<br>"
        f"{meta.report_type}</div>"
    )
    parts.append("  </div>")
    parts.append("  <ul>")
    for i, (spec, _items) in enumerate(sections, 1):
        sid = _html.escape(spec.id, quote=True)
        parts.append(
            f'    <li><a href="#{sid}" onclick="return go(\'{sid}\',this)">'
            f'<span class="num">{i:02d}</span>'
            f"{_html.escape(spec.title, quote=False)}</a></li>"
        )
    parts.append("  </ul>")
    parts.append('  <div class="backlinks">')
    parts.append("    <span>← backlog board（VSCode Backlog Cards）</span><br>")
    if meta.ep_path:
        parts.append(f'    <a href="{_html.escape(meta.ep_path, quote=True)}">EP 全文</a>')
    else:
        parts.append("    <span>EP 詳見 task 目錄</span>")
    parts.append("  </div>\n</nav>")
    parts.append(_BTN_COLLAPSE)
    parts.append("<main>")
    for spec, items in sections:
        sid = _html.escape(spec.id, quote=True)
        parts.append(f'<section id="{sid}">')
        parts.append(f"<h2>{_html.escape(spec.title, quote=False)}</h2>")
        if spec.sub:
            parts.append(f'<div class="sub">{render_inline(spec.sub)}</div>')
        parts.extend(
            _render_section_items(items, meta.report_type, meta.task_type, meta.diagram_heights)
        )
        parts.append("</section>")
    parts.append(
        f"<!-- {MARKER_PREFIX}@{BUILDER_VERSION} | mode={meta.mode} "
        f"| card_id={meta.card_id} | task_baseline={meta.task_baseline} "
        f"| report_type={meta.report_type} | source={source_name} "
        f"| diagrams={','.join(dia_ids)} -->"
    )
    parts.append("</main>")
    parts.append("<script>")
    parts.append(CANONICAL_JS)
    parts.append("</script>")
    parts.append("</body>\n</html>")
    return "\n".join(parts) + "\n"


def build(md: str, source_name: str = "report.md") -> str:
    """shell-ready md → 報告殼 HTML（契約違反 fail loud；自我 gate 綠才回傳）。"""
    meta, body = parse_frontmatter(md)
    events = parse_body(body)
    html_out = render_html(meta, events, source_name)
    violations = [v for v in _gate_static(md, html_out) if not v.startswith("determinism:")]
    if violations:
        raise BuildError("build 自我 gate 紅（渲染器缺陷或契約違反）：\n" + "\n".join(violations))
    return html_out


# ── HTML 語義葉萃取（html.parser；與 md_leaves 對照）────────────────


class _LeafExtractor(HTMLParser):
    """只走 <main>；葉＝h2/h3/p/li/row/code/note＋frame bar 圖題（p）。

    skip 子樹：summary（摺疊標題非內容葉）、.degraded-body（樣板提示文非 md 葉）。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.leaves: list[tuple[str, str]] = []
        self.main_depth = 0
        self.skip = 0
        self.cap: dict[str, str] | None = None  # {tag, kind, buf}
        self.row: list[str] | None = None
        self.in_bar = False
        self.span_in_bar = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = dict(attrs).get("class") or ""
        if tag == "main":
            self.main_depth += 1
            return
        if not self.main_depth:
            return
        if self.skip:
            if tag in ("summary", "div"):
                self.skip += 1
            return
        if tag == "summary" or "degraded-body" in cls:
            self.skip += 1
            return
        if tag == "div" and "bar" in cls.split():
            self.in_bar = True
            return
        if self.in_bar and tag == "span":
            self.span_in_bar = True
            return
        if self.cap is not None:
            return  # capture 中——巢狀 inline（b/code/a）文字自然累積
        if tag == "tr":
            self.row = []
            return
        if tag in ("td", "th") and self.row is not None:
            self.cap = {"tag": tag, "kind": "cell", "buf": ""}
            return
        if tag == "div" and "flow" in cls.split():
            self.cap = {"tag": "div", "kind": "code", "buf": ""}
            return
        if tag == "div" and "sub" in cls.split():
            self.cap = {"tag": "div", "kind": "p", "buf": ""}
            return
        if tag == "div" and "note" in cls.split():
            self.cap = {"tag": "div", "kind": "note", "buf": ""}
            return
        if tag in ("h2", "h3", "p", "li"):
            self.cap = {"tag": tag, "kind": tag, "buf": ""}

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.main_depth -= 1
            return
        if not self.main_depth:
            return
        if self.skip:
            if tag in ("summary", "div"):
                self.skip -= 1
            return
        if self.cap is not None and tag == self.cap["tag"]:
            text, kind = self.cap["buf"], self.cap["kind"]
            self.cap = None
            if kind == "cell":
                if self.row is not None:
                    self.row.append(_ws(text))
            elif kind == "code":
                self.leaves.append(("code", text.rstrip("\n")))
            else:
                self.leaves.append((kind, _ws(text)))
            return
        if self.span_in_bar and tag == "span":
            self.span_in_bar = False
            return
        if self.in_bar and tag == "div":
            self.in_bar = False
            return
        if tag == "tr" and self.row is not None:
            self.leaves.append(("row", " | ".join(self.row)))
            self.row = None

    def handle_data(self, data: str) -> None:
        if not self.main_depth or self.skip:
            return
        if self.cap is not None:
            self.cap["buf"] += data
        elif self.span_in_bar:
            t = _ws(data)
            if t:
                self.leaves.append(("p", t))


def html_leaves(html: str) -> list[tuple[str, str]]:
    """生成殼 HTML → 有序語義葉（gate 全等對照的 html 側）。"""
    p = _LeafExtractor()
    p.feed(html)
    p.close()
    return p.leaves


# ── gate（hard 六項）───────────────────────────────────────────────

_MARKER_RE = re.compile(r"<!--\s*built-by: build_shell\.py@([\w.]+)\s*\|([^>]*)-->")

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HTML_ATTR_RE = re.compile(r'<a href="([^"]+)"[^>]*>|<iframe src="([^"]+)"')


def _md_attr_expect(events: list[Event]) -> list[tuple[str, str]]:
    """md 側屬性期望序列（與渲染器同構、文件序）：section sub 連結 href＋diagram src
    （每圖兩個屬性位——bar href 與 iframe src?embed=1）。body 葉內連結經 norm_inline
    已還原為文字、不產生 html 屬性——兩側一致不出現。"""
    expect: list[tuple[str, str]] = []
    for kind, payload in events:
        if kind == "section":
            assert isinstance(payload, SectionSpec)
            if payload.sub:
                for m in _LINK_RE.finditer(payload.sub):
                    expect.append(("href", _html.escape(m.group(2), quote=False)))
        elif kind == "diagram":
            assert isinstance(payload, DiagramSpec)
            if payload.src:
                src = _html.escape(payload.src, quote=True)
                expect.append(("href", src))
                expect.append(("src", src + "?embed=1"))
    return expect


def _html_attr_observed(html: str) -> list[tuple[str, str]] | None:
    """html 側屬性觀察序列（僅 <main> 內、文件序）；缺 main 邊界回 None。"""
    if "<main>" not in html or "</main>" not in html:
        return None
    main = html[html.index("<main>") : html.index("</main>")]
    observed: list[tuple[str, str]] = []
    for m in _HTML_ATTR_RE.finditer(main):
        if m.group(2) is not None:
            observed.append(("src", m.group(2)))
        else:
            observed.append(("href", m.group(1)))
    return observed


def _marker_fields(html: str) -> dict[str, str]:
    m = _MARKER_RE.search(html)
    if not m:
        return {}
    fields: dict[str, str] = {"version": m.group(1)}
    for part in m.group(2).split("|"):
        k, _, v = part.strip().partition("=")
        fields[k.strip()] = v.strip()
    return fields


def _gate_static(md: str, html: str) -> list[str]:
    """hard 六項中不需第二次產物的五項（leaves／三行為面／meta）。"""
    violations: list[str] = []
    try:
        meta, body = parse_frontmatter(md)
        events = parse_body(body)
    except BuildError as e:
        return [f"meta: md 契約解析失敗：{e}"]
    # ① ordered semantic leaves 全等
    md_l = _md_leaves_from(meta, events)
    html_l = html_leaves(html)
    if md_l != html_l:
        detail = f"葉數不符 md={len(md_l)} html={len(html_l)}"
        for i, (a, b) in enumerate(zip(md_l, html_l)):
            if a != b:
                detail = f"第 {i} 葉不符 md={a!r} html={b!r}"
                break
        violations.append(f"leaves: ordered semantic leaves 非全等——{detail}")
    # ①b 屬性臂（lossless 補洞，外審 B／mutation M7）：href/iframe src 有序比對
    expect = _md_attr_expect(events)
    observed = _html_attr_observed(html)
    if observed is None:
        violations.append("attrs: html 缺 <main> 邊界——屬性臂無法定位")
    elif expect != observed:
        detail = f"屬性位數 md={len(expect)} html={len(observed)}"
        for i, (a, b) in enumerate(zip(expect, observed)):
            if a != b:
                detail = f"第 {i} 屬性位不符 md={a} html={b}"
                break
        violations.append(f"attrs: href/iframe src 有序序列非全等——{detail}")
    # ②③④ 三硬約束行為面（canonical JS/按鈕組為行為錨）
    js_block = "<script>\n" + CANONICAL_JS + "\n</script>"
    if js_block not in html:
        violations.append("first-screen: init JS 與 canonical 不符（首屏 active 規則 AIR-14）")
        violations.append("collapse: setCollapsed 與 canonical 不符（折疊禁觸發 iframe 重載）")
        violations.append("a11y: aria-expanded/localStorage 語義與 canonical 不符")
    if _BTN_COLLAPSE not in html or _BTN_EXPAND not in html:
        violations.append("a11y: 折疊鈕缺 canonical <button>＋aria-expanded 標記")
    if "SIDEBAR_KEY='illustrate-shell-sidebar-collapsed'" not in html:
        violations.append("a11y: localStorage 折疊記憶 key 缺失")
    if 'class="active"' in html:
        violations.append("first-screen: 出現預設 active class——首屏必須由 canonical JS 決定")
    nav_hrefs = set(re.findall(r'<a href="#([^"]+)" onclick="return go', html))
    section_ids = set(re.findall(r'<section id="([^"]+)">', html))
    if nav_hrefs != section_ids or not section_ids:
        violations.append(
            "first-screen: nav 與 section 對應破損 "
            f"nav={sorted(nav_hrefs)} sections={sorted(section_ids)}"
        )
    # ⑤ meta completeness＋diagram key-set multiset 鎖死
    if sorted(meta.diagram_heights) != sorted(_diagram_ids(events)):
        violations.append(
            "meta: diagram_heights 與 diagram-assign key-set 不全等（multiset 鎖死）"
        )
    fields = _marker_fields(html)
    if not fields:
        violations.append("meta: built-by marker 缺失")
    else:
        for key, expect in (
            ("card_id", meta.card_id),
            ("task_baseline", meta.task_baseline),
            ("report_type", meta.report_type),
            ("mode", meta.mode),
        ):
            if fields.get(key) != expect:
                violations.append(
                    f"meta: {key} marker={fields.get(key)!r} 與 frontmatter={expect!r} 不符"
                )
        if fields.get("diagrams", "") != ",".join(_diagram_ids(events)):
            violations.append(
                f"meta: diagrams={fields.get('diagrams')!r} "
                f"與 body diagram-assign={_diagram_ids(events)} 不符"
            )
    return violations


def run_gate(md: str, html: str, prev_html: str | None = None) -> list[str]:
    """hard 六項 gate。回傳違規清單（前綴＝leaves/attrs/first-screen/collapse/a11y/meta/determinism）。"""
    violations = _gate_static(md, html)
    if prev_html is not None and prev_html != html:
        violations.append("determinism: 確定性重跑失敗——同一 md 兩次產物不一致")
    return violations


# ── CLI ────────────────────────────────────────────────────────────


def _parse_cli(argv: list[str]) -> tuple[bool, bool, str, str | None]:
    check = False
    stdout = False
    rest: list[str] = []
    for a in argv:
        if a == "--check":
            check = True
        elif a == "--stdout":
            stdout = True
        else:
            rest.append(a)
    if check:
        if len(rest) != 2:
            raise BuildError("--check 用法：build_shell.py --check <report.md> <index.html>")
        return True, stdout, rest[0], rest[1]
    if len(rest) != 1:
        raise BuildError("用法：build_shell.py [--check md html | --stdout] <report.md>")
    return False, stdout, rest[0], None


def _read_text(path: str) -> str:
    """讀檔統一入口：缺失／非 UTF-8 → InputError（exit 2，fail loud 不變——外審 D）。"""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise InputError(f"讀取失敗：{path}（{e}）") from e


def main(argv: list[str] | None = None) -> int:
    """回傳碼：0 綠／2 拒絕覆寫 legacy-curated 或輸入讀取失敗／3 契約或 gate 紅。"""
    try:
        args = sys.argv[1:] if argv is None else argv
        check, stdout, md_path, html_path = _parse_cli(list(args))
        md = _read_text(md_path)
        if check:
            assert html_path is not None
            html_out = _read_text(html_path)
            violations = run_gate(md, html_out)
            if violations:
                print("\n".join(violations))
                return 3
            print("gate 綠：hard 六項全過")
            return 0
        html_out = build(md, source_name=Path(md_path).name)
        if stdout:
            sys.stdout.write(html_out)
            return 0
        out_path = Path(md_path).parent / "index.html"
        if out_path.is_symlink():
            raise BuildError(
                f"輸出目標是 symlink：{out_path}——拒絕跟隨寫入（先移除 symlink 再重生）"
            )
        if out_path.exists() and MARKER_PREFIX not in _read_text(str(out_path)):
            print(
                f"拒絕覆寫：{out_path} 無 builder marker（legacy-curated 維持手填；"
                "轉 shell-ready md 或先移除舊殼）"
            )
            return 2
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        tmp_path.write_text(html_out, encoding="utf-8")
        os.replace(tmp_path, out_path)  # 原子寫（外審 F）
        print(f"已寫出 {out_path}（lossless，gate 綠）")
        return 0
    except InputError as e:
        print(f"build_shell: {e}", file=sys.stderr)
        return 2
    except BuildError as e:
        print(f"build_shell: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
