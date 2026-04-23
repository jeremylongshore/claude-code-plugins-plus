#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def main() -> int:
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else ".changelog-config.json")
    if not config_path.exists():
        print(json.dumps({"ok": False, "error": f"Missing config: {config_path}"}))
        return 2

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"Invalid JSON: {exc}"}))
        return 2

    errors = []
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")

    template = config.get("template")
    if not isinstance(template, str) or not template.strip():
        errors.append("template must be a non-empty string")

    output_path = config.get("output_path")
    if not isinstance(output_path, str) or not output_path.strip():
        errors.append("output_path must be a non-empty string")

    quality_threshold = config.get("quality_threshold")
    if not isinstance(quality_threshold, (int, float)) or not (0 <= quality_threshold <= 100):
        errors.append("quality_threshold must be a number between 0 and 100")

    # Token env vars
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        src_type = source.get("type")
        src_cfg = source.get("config") if isinstance(source.get("config"), dict) else {}
        token_env = src_cfg.get("token_env")
        if src_type in {"github", "slack"} and isinstance(token_env, str) and token_env.strip():
            if not os.getenv(token_env):
                errors.append(f"Missing env var for {src_type}: {token_env}")

    ok = len(errors) == 0
    print(json.dumps({"ok": ok, "errors": errors, "config_path": str(config_path)}))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

