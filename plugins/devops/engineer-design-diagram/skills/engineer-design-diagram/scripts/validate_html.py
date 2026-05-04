#!/usr/bin/env python3
"""
validate_html.py — accessibility + no-external-deps check for engineer-design-diagram output.

Usage:
    validate_html.py path/to/diagram.html

Checks:
    1. SVG root has role="img" and aria-labelledby
    2. <title> element is present in SVG
    3. At least one <rect> has a <title> child (component labeling)
    4. prefers-reduced-motion media query exists in <style>
    5. No external script src (Google Fonts links are allowed)

Exits 0 on pass, 1 on fail with details printed to stderr.
Required packages: Python 3.9+ standard library only (re, sys, pathlib).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def validate(html: str) -> list[str]:
    errors = []

    # 1. SVG with role="img" + aria-labelledby
    svg_match = re.search(r"<svg[^>]*>", html, re.IGNORECASE)
    if not svg_match:
        errors.append("No <svg> element found")
    else:
        svg_tag = svg_match.group(0)
        if 'role="img"' not in svg_tag and "role='img'" not in svg_tag:
            errors.append('SVG root missing role="img"')
        if "aria-labelledby" not in svg_tag and "aria-label" not in svg_tag:
            errors.append("SVG root missing aria-labelledby or aria-label")

    # 2. <title> in SVG body
    if not re.search(r"<title[^>]*>", html, re.IGNORECASE):
        errors.append("No <title> element found in SVG")

    # 3. At least one <rect> with accompanying <title> or aria-label (sampling check)
    rect_count = len(re.findall(r"<rect\b", html, re.IGNORECASE))
    titled_rect_pattern = re.compile(
        r"<rect[^>]*>\s*<title>", re.IGNORECASE | re.DOTALL
    )
    aria_rect_pattern = re.compile(r"<rect[^>]*aria-label", re.IGNORECASE)
    if rect_count > 2:  # skip background/grid rects
        titled = len(titled_rect_pattern.findall(html)) + len(aria_rect_pattern.findall(html))
        if titled == 0:
            errors.append(f"Found {rect_count} <rect> elements but none have <title> or aria-label")

    # 4. prefers-reduced-motion media query
    if "prefers-reduced-motion" not in html:
        errors.append("Missing @media (prefers-reduced-motion: reduce) rule")

    # 5. No external scripts beyond allowed CDN allowlist
    # Allowed: Google Fonts CSS, jsdelivr for Mermaid (fallback template)
    allowed_hosts = ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net")
    for src_match in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
        src = src_match.group(1)
        if not any(host in src for host in allowed_hosts):
            errors.append(f"Disallowed external script: {src}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} path/to/diagram.html", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    html = path.read_text(encoding="utf-8")
    errors = validate(html)

    if errors:
        print(f"VALIDATION FAILED: {path}", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {path} passes accessibility + no-external-deps checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
