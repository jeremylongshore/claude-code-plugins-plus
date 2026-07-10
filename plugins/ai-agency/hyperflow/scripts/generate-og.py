#!/usr/bin/env python3
"""Generate the social/OG raster assets from config/features.json.

Social scrapers (Facebook, LinkedIn, X, Slack, iMessage) do not render SVG
og:images, so the share card must be a raster. This draws it directly with
Pillow — no SVG rasterizer required — using the same dark brand palette the
site uses (config/features.json branding.colors).

Outputs:
  - docs/assets/og-image.png          — 1200×630 share card (og:image / twitter:image)
  - docs/assets/apple-touch-icon.png  — 180×180 home-screen icon
  - docs/assets/favicon-32.png        — 32×32 raster favicon fallback

Fonts are vendored in scripts/assets/fonts/ (Inter + JetBrains Mono, both
SIL OFL) so output is deterministic on any machine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "scripts" / "assets" / "fonts"

CHAIN = ["plan", "dispatch", "audit", "deploy"]
EYEBROW = "CODEX · CLAUDE CODE · OPENCODE · GROK · ANTIGRAVITY · CURSOR"
HEADLINE = ["One session.", "A whole engineering team."]
SUBLINE = "Every step specialist-reviewed — issue to PR in one command."
SITE = "mohammed-abdelhady.github.io/hyperflow"


def load_colors() -> dict:
    branding = json.loads((ROOT / "config" / "features.json").read_text())["branding"]["colors"]
    return {
        "bg": branding.get("bg_start", "#0B0F1A"),
        "panel": branding.get("bg_end", "#0E1422"),
        "text1": branding.get("text_primary", "#F8FAFC"),
        "text2": branding.get("text_secondary", "#94A3B8"),
        "border": "#26314A",
        "plan": branding.get("thinking", "#7C3AED"),
        "plan_text": "#A78BFA",
        "exec": branding.get("worker", "#14B8A6"),
        "exec_text": "#2DD4BF",
    }


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp_rgb(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def inter(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_DIR / "Inter-Variable.ttf"), size)
    font.set_variation_by_name(weight)
    return font


def mono(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def tracked_text(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking=0.0) -> float:
    """Draw text with letter-spacing; returns the end x position."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def paste_glow(img: Image.Image, center: tuple, radius: int, color: tuple, peak_alpha: int):
    """Soft radial glow: radial_gradient is black-center → white-edge, inverted = falloff mask.

    Falloff is clamped to zero at the inscribed circle (p=128) — the raw gradient
    only reaches 255 at the corners, which leaves a visible square paste edge.
    """
    grad = Image.radial_gradient("L").resize((radius * 2, radius * 2))
    mask = grad.point(lambda p: int(max(0.0, 1.0 - p / 128) * peak_alpha))
    layer = Image.new("RGB", (radius * 2, radius * 2), color)
    img.paste(layer, (center[0] - radius, center[1] - radius), mask)


def gradient_line(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, width: int, c_from: tuple, c_to: tuple):
    span = max(x1 - x0, 1)
    for x in range(x0, x1):
        t = (x - x0) / span
        draw.line([(x, y - width // 2), (x, y + width // 2)], fill=lerp_rgb(c_from, c_to, t))


def draw_og(colors: dict, version: str, out: Path):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), colors["bg"])

    paste_glow(img, (240, 40), 460, hex_rgb(colors["plan"]), 38)
    paste_glow(img, (1060, 610), 420, hex_rgb(colors["exec"]), 26)

    d = ImageDraw.Draw(img)
    margin = 84

    # Eyebrow — supported CLIs
    tracked_text(d, (margin, 78), EYEBROW, mono(19), colors["plan_text"], tracking=2.2)

    # Headline — shrink until the longest line fits inside the margins
    size = 88
    while size > 40:
        font = inter(size, "Bold")
        if max(d.textlength(line, font=font) for line in HEADLINE) <= W - margin * 2:
            break
        size -= 2
    y = 132
    for line in HEADLINE:
        d.text((margin, y), line, font=inter(size, "Bold"), fill=colors["text1"])
        y += round(size * 1.16)

    # Subline — same fit guard as the headline
    sub_size = 30
    while sub_size > 18 and d.textlength(SUBLINE, font=inter(sub_size, "Regular")) > W - margin * 2:
        sub_size -= 1
    d.text((margin, y + 22), SUBLINE, font=inter(sub_size, "Regular"), fill=colors["text2"])

    # Chain pills with gradient connectors
    py, ph = 452, 64
    pill_font = mono(26, bold=True)
    pad = 26
    gap = 34
    x = margin
    plan_rgb, exec_rgb = hex_rgb(colors["plan"]), hex_rgb(colors["exec"])
    n = len(CHAIN)
    for i, name in enumerate(CHAIN):
        label = f"/{name}"
        w = int(d.textlength(label, font=pill_font)) + pad * 2
        accent = lerp_rgb(plan_rgb, exec_rgb, i / (n - 1))
        d.rounded_rectangle([x, py, x + w, py + ph], radius=14,
                            fill=colors["panel"], outline=colors["border"], width=2)
        d.rounded_rectangle([x + 14, py + 8, x + w - 14, py + 12], radius=2, fill=accent)
        d.text((x + pad, py + 24), label, font=pill_font, fill=colors["text1"])
        if i < n - 1:
            gradient_line(d, x + w + 6, x + w + gap - 6, py + ph // 2, 4,
                          lerp_rgb(plan_rgb, exec_rgb, i / (n - 1)),
                          lerp_rgb(plan_rgb, exec_rgb, (i + 1) / (n - 1)))
        x += w + gap

    # Footer row — wordmark + version pill, site URL right-aligned
    fy = 566
    d.text((margin, fy), "Hyperflow", font=inter(26, "SemiBold"), fill=colors["text1"])
    wm_w = d.textlength("Hyperflow", font=inter(26, "SemiBold"))
    vfont = mono(19)
    vlabel = f"v{version}"
    vw = int(d.textlength(vlabel, font=vfont)) + 24
    vx = margin + int(wm_w) + 18
    d.rounded_rectangle([vx, fy + 1, vx + vw, fy + 31], radius=8,
                        outline=colors["border"], width=2)
    d.text((vx + 12, fy + 6), vlabel, font=vfont, fill=colors["exec_text"])
    site_w = d.textlength(SITE, font=mono(20))
    d.text((W - margin - site_w, fy + 4), SITE, font=mono(20), fill=colors["text2"])

    img.save(out, "PNG", optimize=True)


def draw_icon(colors: dict, size: int, out: Path):
    """Chained-nodes glyph: violet node → gradient link → teal node on a dark rounded square."""
    scale = 4  # supersample for crisp small sizes
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = round(s * 0.22)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=colors["bg"])

    plan_rgb, exec_rgb = hex_rgb(colors["plan"]), hex_rgb(colors["exec"])
    r = round(s * 0.14)
    c1 = (round(s * 0.32), round(s * 0.40))
    c2 = (round(s * 0.68), round(s * 0.60))
    gradient_line(d, c1[0], c2[0], (c1[1] + c2[1]) // 2, max(round(s * 0.10), 2), plan_rgb, exec_rgb)
    d.ellipse([c1[0] - r, c1[1] - r, c1[0] + r, c1[1] + r], fill=plan_rgb)
    d.ellipse([c2[0] - r, c2[1] - r, c2[0] + r, c2[1] + r], fill=exec_rgb)

    img = img.resize((size, size), Image.LANCZOS)
    img.save(out, "PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description="Generate OG/social raster assets")
    parser.add_argument("--version", default=None, help="Version string (defaults to package.json)")
    args = parser.parse_args()

    version = args.version or json.loads((ROOT / "package.json").read_text())["version"]
    colors = load_colors()
    assets = ROOT / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    draw_og(colors, version, assets / "og-image.png")
    draw_icon(colors, 180, assets / "apple-touch-icon.png")
    draw_icon(colors, 32, assets / "favicon-32.png")

    for name in ("og-image.png", "apple-touch-icon.png", "favicon-32.png"):
        path = assets / name
        print(f"✓ {path.relative_to(ROOT)}  ·  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
