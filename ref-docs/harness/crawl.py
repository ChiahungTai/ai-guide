#!/usr/bin/env python3
"""
Multi-harness docs mirror crawler.

Mirrors official docs from Claude Code, ZCode, Codex, Meta (Muse Code)
into ref-docs/harness/<source>/.
Prefers markdown endpoints (llms.txt / .md suffix); falls back to HTML extraction
(zcode, and Claude blog when .md unavailable). Deterministic: writes a file only
when its sha256 changed, so refresh produces minimal diff.

Output convention: print = state-transition summary ([OK]/[WARN]/[FAIL] tags).

Usage:
    uv run python ref-docs/harness/crawl.py                            # all sources
    uv run python ref-docs/harness/crawl.py --source claude-code       # one source
    uv run python ref-docs/harness/crawl.py --source zcode --limit 3   # smoke test
"""

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
USER_AGENT = "ai-rules-harness-mirror/1.0 (local docs cache)"
TIMEOUT = 20
MAX_WORKERS = 4
# Below this many chars of extracted text, treat as a client-rendered shell.
SPARSE_TEXT_THRESHOLD = 200


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def http_get(url: str) -> tuple[int, str]:
    """GET url -> (status, body_text). status 0 = network error; body "" on non-2xx."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception:
        return 0, ""


def fetch_until_ok(url: str, retries: int = 1) -> str | None:
    """GET with one retry; return body on 2xx, else None."""
    for _ in range(retries + 1):
        status, body = http_get(url)
        if 200 <= status < 300:
            return body
        time.sleep(0.4)
    return None


# --------------------------------------------------------------------------- #
# HTML -> text (stdlib; zcode / blog fallback)
# --------------------------------------------------------------------------- #


class _TextExtractor(HTMLParser):
    _SKIP = {"script", "style", "nav", "header", "footer", "noscript", "svg", "form"}
    _BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "tr", "div"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip_depth += 1
        if tag in self._BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in self._BLOCK:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)


def extract_main_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = [ln.strip() for ln in "".join(parser._parts).splitlines()]
    return "\n".join(ln for ln in lines if ln).strip()


def looks_like_html(body: str) -> bool:
    """A requested .md that actually returns an HTML page (false 200)."""
    return body.lstrip().lower().startswith(("<!doctype", "<html", "<head"))


# --------------------------------------------------------------------------- #
# Page model
# --------------------------------------------------------------------------- #


@dataclass
class Page:
    url: str
    relpath: str  # relative to <source>/ dir, e.g. "docs/en/admin-setup.md"


@dataclass
class PageResult:
    url: str
    relpath: str
    status: str  # ok | fail | extracted-html | sparse-html
    sha256: str
    nbytes: int


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #

CLAUDE_BASE = "https://code.claude.com"
CLAUDE_BLOG_BASE = "https://claude.com"  # blog posts live on the marketing host
ZCODE_BASE = "https://zcode.z.ai"
CODEX_BASE = "https://learn.chatgpt.com"
# Merged ChatGPT+Codex docs index; developers.openai.com/codex/* 308-redirects here.
CODEX_LLM = "https://learn.chatgpt.com/docs/llms.txt"

_CLAUDE_DOC_LINK = re.compile(r"- \[[^\]]+\]\((https?://code\.claude\.com[^)]+\.md)\)")
# The blog index (code.claude.com/blog) links to claude.com/blog/<slug>; posts have
# no .md export, so fetch the HTML article and extract. Slugs are host-agnostic.
_CLAUDE_BLOG_SLUG = re.compile(r"/blog/([a-z0-9][a-z0-9-]*[a-z0-9])")


def discover_claude_code() -> list[Page]:
    pages: list[Page] = []

    llms = fetch_until_ok(CLAUDE_BASE + "/llms.txt")
    if llms:
        for url in _CLAUDE_DOC_LINK.findall(llms):
            rel = url.removeprefix(CLAUDE_BASE).lstrip("/")
            pages.append(Page(url, rel))
    else:
        print("[WARN] claude-code: /llms.txt unreachable; docs skipped")

    # Blog — discover slugs from the index; posts are HTML on claude.com (no .md).
    status, blog_html = http_get(CLAUDE_BASE + "/blog")
    if status == 200:
        slugs = sorted(set(_CLAUDE_BLOG_SLUG.findall(blog_html)))
        for slug in slugs:
            pages.append(Page(f"{CLAUDE_BLOG_BASE}/blog/{slug}", f"blog/{slug}.md"))
    else:
        print(
            f"[WARN] claude-code: /blog index unreachable (status {status}); blog skipped"
        )

    return _dedup(pages)


def fetch_claude_code(page: Page) -> tuple[str, bytes]:
    status, body = http_get(page.url)
    if not (200 <= status < 300):
        return "fail", b""
    # Blog posts are HTML articles (no .md export) — extract main text.
    if page.relpath.startswith("blog/"):
        text = extract_main_text(body)
        return ("extracted-html" if text else "sparse-html"), _norm(text)
    return "ok", _norm(body)


_ZCODE_DOC_LINK = re.compile(r'"/(cn|en)/docs/([a-z0-9-]+)"')


def discover_zcode() -> list[Page]:
    # zcode.z.ai is a Next.js app with a catch-all that serves the SPA shell for
    # bogus paths (sitemap.xml / llms.txt / robots.txt all return HTML 200). But
    # real doc routes DO server-render content + the sidebar nav, so seed from the
    # welcome page's nav links — that exposes the whole docs tree.
    seed = ZCODE_BASE + "/cn/docs/welcome"
    html = fetch_until_ok(seed)
    if not html:
        print(f"[WARN] zcode: seed {seed} unreachable; skipped")
        return []
    rels = sorted(
        {f"{lang}/docs/{slug}" for lang, slug in _ZCODE_DOC_LINK.findall(html)}
    )
    return _dedup([Page(f"{ZCODE_BASE}/{rel}", f"{rel}.md") for rel in rels])


def fetch_zcode(page: Page) -> tuple[str, bytes]:
    status, html = http_get(page.url)
    if not (200 <= status < 300):
        return "fail", b""
    text = extract_main_text(html)
    if len(text) < SPARSE_TEXT_THRESHOLD:
        return "sparse-html", _norm(text)
    return "extracted-html", _norm(text)


_CODEX_DOC_LINK = re.compile(
    r"\]\((https?://learn\.chatgpt\.com/docs/[^)]+?\.md(?:\?[^)]*)?)\)"
)


def discover_codex() -> list[Page]:
    # learn.chatgpt.com exposes a docs-scoped llms.txt listing every page as a
    # verbatim .md link (same scheme as meta). developers.openai.com/codex/*
    # 308-redirects to the new host, so the old codex-specific index is gone.
    llms = fetch_until_ok(CODEX_LLM)
    if not llms:
        print("[WARN] codex: /docs/llms.txt unreachable; docs skipped")
        return []
    pages: list[Page] = []
    for url in _CODEX_DOC_LINK.findall(llms):
        url = url.split("?", 1)[0]  # ?surface= variants -> canonical page
        # Strip base + the redundant leading "docs/" (source dir already names it).
        rel = url.removeprefix(CODEX_BASE).lstrip("/").removeprefix("docs/")
        pages.append(Page(url, rel))
    return _dedup(pages)


def fetch_codex(page: Page) -> tuple[str, bytes]:
    status, body = http_get(page.url)
    if 200 <= status < 300:
        return "ok", _norm(body)
    return "fail", b""


XAI_BASE = "https://docs.x.ai"
XAI_LLM = "https://docs.x.ai/llms.txt"  # root-level index; Grok Build pages under /build/

_XAI_DOC_LINK = re.compile(r"\]\((https?://docs\.x\.ai/build/[^)]+\.md)\)")


def discover_grok_build() -> list[Page]:
    # docs.x.ai exposes a root llms.txt listing every page as a verbatim .md
    # link (same scheme as codex/meta); filter to the Grok Build section.
    llms = fetch_until_ok(XAI_LLM)
    if not llms:
        print("[WARN] grok-build: /llms.txt unreachable; docs skipped")
        return []
    pages: list[Page] = []
    for url in _XAI_DOC_LINK.findall(llms):
        # Strip base + the redundant leading "build/" (source dir already names it).
        rel = url.removeprefix(XAI_BASE).lstrip("/").removeprefix("build/")
        pages.append(Page(url, rel))
    return _dedup(pages)


def fetch_grok_build(page: Page) -> tuple[str, bytes]:
    status, body = http_get(page.url)
    if 200 <= status < 300:
        return "ok", _norm(body)
    return "fail", b""


META_BASE = "https://dev.meta.ai"
META_LLM = "https://dev.meta.ai/docs/llms.txt"  # docs-wide index (no root llms.txt)

_META_DOC_LINK = re.compile(r"\]\((https?://dev\.meta\.ai/docs/[^)]+\.md)\)")


def discover_meta() -> list[Page]:
    # dev.meta.ai exposes a docs-scoped llms.txt listing every page as verbatim
    # .md links (same scheme as codex). Covers the Meta Model API, Muse Code
    # CLI, and Muse Glimmer docs.
    llms = fetch_until_ok(META_LLM)
    if not llms:
        print("[WARN] meta: /docs/llms.txt unreachable; docs skipped")
        return []
    pages: list[Page] = []
    for url in _META_DOC_LINK.findall(llms):
        rel = url.removeprefix(META_BASE).lstrip("/").removeprefix("docs/")
        pages.append(Page(url, rel))
    return _dedup(pages)


def fetch_meta(page: Page) -> tuple[str, bytes]:
    status, body = http_get(page.url)
    if 200 <= status < 300:
        return "ok", _norm(body)
    return "fail", b""


SOURCES = {
    "claude-code": (CLAUDE_BASE, discover_claude_code, fetch_claude_code),
    "zcode": (ZCODE_BASE, discover_zcode, fetch_zcode),
    "codex": (CODEX_BASE, discover_codex, fetch_codex),
    "grok-build": (XAI_BASE, discover_grok_build, fetch_grok_build),
    "meta": (META_BASE, discover_meta, fetch_meta),
}


# --------------------------------------------------------------------------- #
# Writer + runner
# --------------------------------------------------------------------------- #


def _norm(text: str) -> bytes:
    return text.rstrip().encode("utf-8") + b"\n"


def _dedup(pages: list[Page]) -> list[Page]:
    seen: set[str] = set()
    out: list[Page] = []
    for p in pages:
        if p.relpath and p.relpath not in seen:
            seen.add(p.relpath)
            out.append(p)
    return out


def write_if_changed(path: Path, content: bytes) -> bool:
    new_hash = hashlib.sha256(content).hexdigest()
    if path.exists():
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() == new_hash:
                return False
        except OSError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return True


def run_source(name: str, base: str, discover, fetch, limit: int) -> dict:
    pages = discover()
    if limit:
        pages = pages[:limit]
    if not pages:
        print(f"[WARN] {name}: no pages discovered")
    results: list[PageResult] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(fetch, p): p for p in pages}
        for fut in as_completed(futs):
            page = futs[fut]
            try:
                status, content = fut.result()
            except Exception as exc:
                print(f"[FAIL] {name}: {page.url}: {exc}")
                status, content = "fail", b""
            sha = ""
            if content and status in ("ok", "extracted-html"):
                # smoke（--limit）零寫入：寫了磁碟不寫 manifest＝integrity split
                # （hash ledger 落後磁碟內容）——smoke 只驗 discover+fetch 連通
                if not limit:
                    dest = BASE_DIR / name / page.relpath
                    write_if_changed(dest, content)
                sha = hashlib.sha256(content).hexdigest()
            results.append(
                PageResult(page.url, page.relpath, status, sha, len(content))
            )
    results.sort(key=lambda r: r.relpath)
    _print_source_summary(name, results)
    return {
        "base": base,
        # 新鮮度 per-source：單源刷新只更新本源時間，不得讓他源共用新時間戳
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "page_count": len(results),
        "pages": [
            {
                "url": r.url,
                "path": r.relpath,
                "status": r.status,
                "sha256": r.sha256,
                "bytes": r.nbytes,
            }
            for r in results
        ],
    }


def _print_source_summary(name: str, results: list[PageResult]) -> None:
    if not results:
        return
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    parts = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"[OK] {name}: {len(results)} pages ({parts})")
    fails = [r for r in results if r.status in ("fail", "sparse-html")]
    for r in fails[:5]:
        tag = "[WARN]" if r.status == "sparse-html" else "[FAIL]"
        print(f"  {tag} {r.url} ({r.status}, {r.nbytes}B)")
    if len(fails) > 5:
        print(f"  ... {len(fails) - 5} more")


def write_manifest(payload: dict) -> None:
    path = BASE_DIR / "manifest.json"
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    write_if_changed(path, text.encode("utf-8"))


def load_existing_sources() -> dict:
    path = BASE_DIR / "manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("sources", {})
    except (OSError, json.JSONDecodeError):
        return {}


def _report_orphans(name: str, entry: dict) -> None:
    """磁碟上有、本次 discovery 沒有的鏡像檔——上游下架或 discovery 變動的帳目。

    只列帳不刪（本地無法判別是 upstream 下架還是漏抓，去留人工裁定）。
    """
    src_dir = BASE_DIR / name
    if not src_dir.is_dir():
        return
    known = {p["path"] for p in entry.get("pages", [])}
    for f in sorted(src_dir.rglob("*")):
        if f.is_file() and f.relative_to(src_dir).as_posix() not in known:
            print(
                f"[WARN] {name}: 磁碟孤兒（本次未發現——上游下架或 discovery 變動，"
                f"人工裁定去留）: {f.relative_to(src_dir)}"
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mirror multi-harness docs.")
    ap.add_argument("--source", choices=list(SOURCES) + ["all"], default="all")
    ap.add_argument(
        "--limit", type=int, default=0, help="pages per source (smoke test)"
    )
    args = ap.parse_args(argv)

    names = list(SOURCES) if args.source == "all" else [args.source]
    sources = load_existing_sources()
    for name in names:
        base, discover, fetch = SOURCES[name]
        sources[name] = run_source(name, base, discover, fetch, args.limit)
    if args.limit:
        # smoke 不寫 manifest：抽樣結果覆寫 source entry 會縮小 coverage、
        # 磁碟頁失去 URL/hash/status ledger（provenance 破壞）
        print("[SMOKE] --limit：不寫 manifest（smoke 不變動 provenance ledger）")
        return 0
    for name in names:
        _report_orphans(name, sources[name])
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sources": dict(sorted(sources.items())),
    }
    write_manifest(manifest)
    print(f"[OK] manifest: {BASE_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
