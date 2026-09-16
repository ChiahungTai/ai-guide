"""S3 部署面探針：三端 bundle gate＋尾端哨兵＋Claude 未動＋trust 面數字。只讀（被測面在 $HOME，repo 只寫 .out）。"""

import pathlib

HOME = pathlib.Path.home()
TASKS = "ai-analysis/_tasks/09-08-context-lifecycle-unification"
GATES = {
    "zcode": (HOME / ".zcode" / "AGENTS.md", 90 * 1024),
    "codex": (HOME / ".codex" / "AGENTS.md", 90 * 1024),
    "muse": (HOME / ".config" / "muse" / "AGENTS.md", 50 * 1024),
}
SENTINEL = "<!-- bundle-end -->"


def main():
    print("== per-target bundle ==")
    for label, (path, gate) in GATES.items():
        raw = path.read_bytes()
        n = len(raw)
        tail_ok = raw.rstrip().endswith(SENTINEL.encode())
        verdict = "PASS" if n <= gate and tail_ok else "FAIL"
        print(f"{label}: {n}B / gate {gate} tail={tail_ok} -> {verdict}")
    print("== claude untouched ==")
    cl = HOME / ".claude" / "CLAUDE.md"
    print(
        "symlink:",
        cl.is_symlink(),
        "->",
        (str(cl.resolve()) if cl.is_symlink() else "-"),
    )
    print("== pool surfaces (ai-rules trusted) ==")
    pool = HOME / ".claude" / "projects" / "-Users-ctai-Github-ai-rules" / "memory"
    mem = (pool / "MEMORY.md").read_bytes()
    bodies = list(pool.glob("*.md"))
    print(f"MEMORY.md {len(mem)}B entries={len(bodies)} (lane cap 65536 trusted)")
    print("== lane math (ai-rules ws) ==")
    proj = len(pathlib.Path("AGENTS.md").read_bytes())
    muse_n = len(GATES["muse"][0].read_bytes())
    print(
        f"user {muse_n} + project {proj} + wrapper ~1100 = {muse_n + proj + 1100} vs 65536"
    )
    print("== trust ==")
    print(
        "live pool: trusted path only; untrusted/project-omitted degraded path = designed, runtime unverified"
    )


if __name__ == "__main__":
    main()
