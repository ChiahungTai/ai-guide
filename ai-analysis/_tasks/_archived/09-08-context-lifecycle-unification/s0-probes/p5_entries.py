"""P5 helper: dump frontmatter of the 10 sampled entries (read-only)."""

import os

POOL = os.path.expanduser(
    "~/.zcode/cli/memories/projects/ai-rules-01610fbb20315a8b/memory"
)
NAMES = [
    "commit-consent-in-autonomous-mode",
    "feedback_verify-wt-before-commit",
    "feedback_dual-family-review-dispatch",
    "feedback_quota-failover-policy",
    "feedback_delegation-claims-verification",
    "feedback_relay-claims-verify-current-state",
    "feedback_read-current-file-before-reviewing",
    "feedback_review-even-on-quick-fix",
    "feedback_dispatch-reread-governing-docs",
    "feedback_full-read-base-not-context-copy",
]
for name in NAMES:
    for prefix in ("", "feedback_", "reference_", "project_"):
        cand = os.path.join(POOL, f"{prefix}{name}.md")
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                text = f.read()
            head = text.split("---")[1] if text.startswith("---") else text[:300]
            desc = ""
            for line in head.split("\n"):
                if line.startswith("description:"):
                    desc = line[len("description:") :].strip()
                    break
            print(f"== {os.path.basename(cand)}")
            print(f"   desc({len(desc)}): {desc}")
            break
    else:
        print(f"== {name}: NOT FOUND")
