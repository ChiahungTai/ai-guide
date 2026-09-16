"""P4 helper: section byte split of mosaic root AGENTS.md (read-only)."""

path = "/Users/ctai/Github/mosaic_alpha/AGENTS.md"
with open(path, encoding="utf-8") as f:
    text = f.read()
lines = text.split("\n")
total = 0
current = "(header)"
sizes = []
buf = 0
for line in lines:
    if line.startswith("## "):
        sizes.append((current, buf))
        current = line[3:].strip()
        buf = 0
    buf += len(line.encode("utf-8")) + 1
    total += len(line.encode("utf-8")) + 1
sizes.append((current, buf))
for name, n in sizes:
    print(f"{n:>7}  {name}")
print(f"{total:>7}  TOTAL")
