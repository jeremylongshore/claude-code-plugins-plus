#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


RE_FRONTMATTER = re.compile(r"^---\\s*\\n(.*?)\\n---\\s*\\n", re.DOTALL)


def has_heading(content: str, heading: str) -> bool:
    return re.search(rf"^##\\s+{re.escape(heading)}\\s*$", content, re.MULTILINE) is not None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: quality_score.py <markdown_path>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    content = path.read_text(encoding="utf-8")

    score = 100
    errors = []
    warnings = []
    checks = {}

    has_fm = RE_FRONTMATTER.search(content) is not None
    checks["frontmatter_present"] = {"pass": has_fm, "message": "frontmatter found" if has_fm else "missing frontmatter"}
    if not has_fm:
        score -= 30
        errors.append("Missing YAML frontmatter block")

    required_sections = ["Highlights", "Features", "Fixes"]
    for section in required_sections:
        ok = has_heading(content, section)
        checks[f"section_{section.lower()}"] = {"pass": ok, "message": "present" if ok else "missing"}
        if not ok:
            score -= 10
            warnings.append(f"Missing section: {section}")

    # Basic link sanity (don’t fetch network)
    broken_md_links = re.findall(r"\\[[^\\]]+\\]\\(([^)]+)\\)", content)
    checks["links_count"] = {"pass": True, "message": f"found {len(broken_md_links)} links"}

    score = max(0, min(100, score))
    ok = len(errors) == 0
    print(json.dumps({"ok": ok, "score": score, "checks": checks, "errors": errors, "warnings": warnings}, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

