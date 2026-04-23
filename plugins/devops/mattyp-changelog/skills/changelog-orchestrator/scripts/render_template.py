#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def render(template: str, vars_dict: dict) -> str:
    out = template
    for key, value in vars_dict.items():
        out = out.replace(f"{{{{{key}}}}}", str(value))
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: render_template.py <template_path> <vars_json_path>", file=sys.stderr)
        return 2

    template_path = Path(sys.argv[1])
    vars_path = Path(sys.argv[2])

    template = template_path.read_text(encoding="utf-8")
    vars_dict = json.loads(vars_path.read_text(encoding="utf-8"))

    print(render(template, vars_dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

