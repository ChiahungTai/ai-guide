"""projection freshness gate——manifest 宣告的投影 upstream content-hash 比對。

repo-agnostic：本腳本零路徑 hard-code，投影／upstream／section 錨全由
manifest 參數宣告（path 相對 --repo-root，預設自 manifest 所在位置向上找
.git toplevel）。

manifest 檔（TOML，本腳本為其 writer 單一源——--update 重寫整檔，手改僅加
projection/upstream 條目，hash 一律由 --update 維護）：

    [[projection]]
    artifact = "proj/index.html"

    [[projection.upstream]]
    path = "docs/guide.md"
    sha1 = "<40-hex>"

    [[projection.upstream]]
    path = "AGENTS.md"
    section = "命令的受眾視角"
    sha1 = "<40-hex>"

hash 語義：git hash-object 等價（sha1 of blob）；帶 section 錨＝只 hash
該節文字（標題行起、下一個同級或更淺標題前止）——upstream 檔的節外改動
不觸發 drift（防無關改動噪音閘）。

exit 語義：0=全 fresh、1=drift（列哪條投影的哪個 upstream 變了；重投影後
--update 收斂）、2=fatal（manifest/upstream 缺席、快照 sha1 不完整、
TOML/schema 錯誤、section 錨不命中——先修 manifest 或補快照）。
"""

import argparse
import hashlib
import re
import sys
import tomllib
from pathlib import Path

_HEADER = (
    "# 投影 freshness manifest——由 scripts/projection_freshness.py 擁有"
    "（--update 重寫整檔；手改僅加 projection/upstream 條目，hash 快照由 --update 維護）\n"
)

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)


class Fatal(Exception):
    """exit 2 條件（manifest／檔案缺席、schema 不完整、錨不命中）。"""


def blob_hash(data: bytes) -> str:
    """git hash-object 等價：sha1("blob <size>\\x00" + data)——size 後接 NUL byte 再接內容。"""
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def hash_file(path: Path) -> str:
    return blob_hash(path.read_bytes())


def section_slice(text: str, section: str) -> str:
    """取 section 節文字：標題行起、下一個同級或更淺標題前止（不含）。

    標題層級＝進入節那行的 # 數；同檔同名多節取第一個命中。
    """
    match = None
    for m in _HEADING_RE.finditer(text):
        if m.group(2) == section:
            match = m
            break
    if match is None:
        raise Fatal(f"section 錨不命中：找不到節標題「{section}」")
    level = len(match.group(1))
    for stop in _HEADING_RE.finditer(text, match.end()):
        if len(stop.group(1)) <= level:
            return text[match.start() : stop.start()]
    return text[match.start() :]


def hash_section(path: Path, section: str) -> str:
    return blob_hash(
        section_slice(path.read_text(encoding="utf-8"), section).encode("utf-8")
    )


def resolve_repo_root(manifest: Path, given: Path | None) -> Path:
    if given is not None:
        return given.resolve()
    for parent in manifest.resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise Fatal(f"無法定位 repo root（--repo-root 未傳且 {manifest} 向上找不到 .git）")


def load_manifest(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise Fatal(f"manifest 缺席：{path}") from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise Fatal(f"manifest TOML 語法錯誤：{exc}") from exc
    projections = data.get("projection")
    if not isinstance(projections, list) or not projections:
        raise Fatal("manifest schema：[[projection]] 至少需一條")
    for proj in projections:
        if not isinstance(proj, dict) or not isinstance(proj.get("artifact"), str):
            raise Fatal("manifest schema：每條 projection 需字串 artifact")
        upstreams = proj.get("upstream")
        if not isinstance(upstreams, list) or not upstreams:
            raise Fatal(f"manifest schema：{proj.get('artifact')} 需非空 upstream 清單")
        for up in upstreams:
            if not isinstance(up, dict) or not isinstance(up.get("path"), str):
                raise Fatal(
                    f"manifest schema：{proj.get('artifact')} 的 upstream 需字串 path"
                )
    return data


def _display(up: dict) -> str:
    return f"{up['path']}#{up['section']}" if "section" in up else up["path"]


def compute_current(repo_root: Path, data: dict) -> list[tuple[str, dict, str]]:
    """算每條 projection 每個 upstream 的現 hash；回 (artifact, upstream, hash) 清單。"""
    rows: list[tuple[str, dict, str]] = []
    for proj in data["projection"]:
        for up in proj["upstream"]:
            target = repo_root / up["path"]
            if not target.is_file():
                raise Fatal(
                    f"upstream 檔缺席：{up['path']}（projection {proj['artifact']}）"
                )
            try:
                current = (
                    hash_section(target, up["section"])
                    if "section" in up
                    else hash_file(target)
                )
            except Fatal as exc:
                raise Fatal(
                    f"{proj['artifact']} upstream {_display(up)}：{exc}"
                ) from exc
            rows.append((proj["artifact"], up, current))
    return rows


def render_manifest(data: dict) -> str:
    """確定序列化（本腳本為 manifest 格式單一源；--update 冪等重寫）。"""
    lines = [_HEADER]
    for proj in data["projection"]:
        lines.append("[[projection]]")
        lines.append(f'artifact = "{proj["artifact"]}"')
        lines.append("")
        for up in proj["upstream"]:
            lines.append("[[projection.upstream]]")
            lines.append(f'path = "{up["path"]}"')
            if "section" in up:
                lines.append(f'section = "{up["section"]}"')
            lines.append(f'sha1 = "{up["sha1"]}"')
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--manifest", required=True, type=Path, help="manifest TOML 路徑"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="upstream path 的基準 root（預設自 manifest 向上找 .git）",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="把現 hash 寫回 manifest（refresh 後收斂用；唯讀檢查不帶）",
    )
    args = parser.parse_args(argv)
    try:
        repo_root = resolve_repo_root(args.manifest, args.repo_root)
        data = load_manifest(args.manifest)
        rows = compute_current(repo_root, data)
    except Fatal as exc:
        print(f"fatal: {exc}", file=sys.stderr)
        return 2

    drifted: list[tuple[str, dict, str]] = []
    for proj in data["projection"]:
        for up in proj["upstream"]:
            expected = up.get("sha1")
            if not isinstance(expected, str) or not _SHA1_RE.match(expected):
                if not args.update:
                    print(
                        f"fatal: {proj['artifact']} upstream {_display(up)} 快照 sha1 缺席/格式錯"
                        "（先 --update 建快照）",
                        file=sys.stderr,
                    )
                    return 2
                expected = None
            current = next(
                cur for art, u, cur in rows if art == proj["artifact"] and u is up
            )
            if expected is None or expected != current:
                drifted.append((proj["artifact"], up, current))
                up["sha1"] = current

    if args.update:
        args.manifest.write_text(render_manifest(data), encoding="utf-8")
        verb = "hash 刷新" if drifted else "無 drift（檔未變）"
        print(f"updated: {args.manifest}（{len(drifted)}/{len(rows)} upstream {verb}）")
        return 0

    if drifted:
        for art, up, cur in drifted:
            print(f"drift: {art} <- {_display(up)}（got {cur}）")
        print(
            f"drift: {len(drifted)}/{len(rows)} upstream 變更——refresh 重投影後 --update 收斂"
        )
        return 1

    for proj in data["projection"]:
        n = len(proj["upstream"])
        print(f"fresh: {proj['artifact']}（{n} upstream hash 對齊）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
