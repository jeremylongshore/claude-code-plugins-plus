#!/usr/bin/env python3
"""Generate the README/landing hero from config/features.json.

A brutalist chain diagram: warm-paper card, hard 2px ink borders,
solid offset shadows, mono skill names, stage-color bars, and the plan and
execute stages shown as brackets around the chain with a Worker -> Reviewer review note.

Two variants render well at any width:
  - docs/assets/hero.svg          — horizontal banner (desktop)
  - docs/assets/hero-vertical.svg — vertical stack (narrow / mobile, via <picture>)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FONT = "'Space Grotesk', ui-sans-serif, -apple-system, BlinkMacSystemFont, system-ui, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

PAPER = "#F4F1E8"
PAPER2 = "#ECE7D7"
CARD = "#FBFAF4"
INK = "#14110C"
MUTED = "#6B6456"
ACCENT = "#E8470F"

# The chain (scaffold is a one-time init, shown as a precursor — not a flow step).
CHAIN = ["plan", "dispatch", "audit", "deploy"]
ROLE = {"plan": "thinking", "dispatch": "worker", "audit": "gate", "deploy": "gate"}
SUB = {"plan": "CHAIN STARTER", "dispatch": "ENDPOINT", "audit": "GATE", "deploy": "GATE"}
CAPTION = {"plan": "sharpen · design · decompose",
           "dispatch": "parallel build + review", "audit": "L1–L5 review", "deploy": "pre-push gates"}


def esc(t: str) -> str:
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def load_features() -> dict:
    return json.loads((ROOT / "config" / "features.json").read_text())


class Canvas:
    def __init__(self, w, h, title, desc):
        self.w, self.h = w, h
        self.p = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"',
            f'     role="img" aria-labelledby="t d" font-family="{FONT}">',
            f'  <title id="t">{esc(title)}</title>',
            f'  <desc id="d">{esc(desc)}</desc>',
            '  <defs>',
            f'    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">'
            f'<path d="M28 0 L0 0 0 28" fill="none" stroke="{PAPER2}" stroke-width="1"/></pattern>',
            f'    <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
            f'orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{INK}"/></marker>',
            '  </defs>',
        ]

    def o(self, s): self.p.append(s)

    def text(self, x, y, s, size=12, fill=INK, weight=400, anchor="start", mono=False, ls=None, op=None):
        a = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"', f'font-size="{size}"', f'font-weight="{weight}"',
             f'text-anchor="{anchor}"']
        if mono: a.append(f'font-family="{MONO}"')
        if ls is not None: a.append(f'letter-spacing="{ls}"')
        if op is not None: a.append(f'opacity="{op}"')
        self.o(f'  <text {" ".join(a)}>{esc(s)}</text>')

    def rect(self, x, y, w, h, fill="none", stroke=None, sw=2, dash=None):
        a = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"', f'fill="{fill}"']
        if stroke: a += [f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash: a.append(f'stroke-dasharray="{dash}"')
        self.o(f'  <rect {" ".join(a)}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=2, marker=None, op=None):
        a = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"', f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if marker: a.append(f'marker-end="url(#{marker})"')
        if op is not None: a.append(f'stroke-opacity="{op}"')
        self.o(f'  <line {" ".join(a)}/>')

    def card(self, x, y, w, h, off=4):
        self.rect(x + off, y + off, w, h, fill=INK)
        self.rect(x, y, w, h, fill=CARD, stroke=INK, sw=2)

    def frame(self):
        self.rect(0, 0, self.w, self.h, fill=PAPER)
        self.rect(0, 0, self.w, self.h, fill="url(#grid)")
        self.rect(1, 1, self.w - 2, self.h - 2, stroke=INK, sw=2)

    def wordmark(self, x, base, size):
        self.text(x, base, "Hyper", size=size, fill=INK, weight=700, ls="-2")
        bx, bw, bh = x + round(size * 2.92), round(size * 2.5), round(size * 1.02)
        by = base - round(size * 0.78)
        self.rect(bx + 4, by + 4, bw, bh, fill=INK)
        self.rect(bx, by, bw, bh, fill=ACCENT)
        self.text(bx + bw / 2, base, "flow", size=size, fill=PAPER, weight=700, anchor="middle", ls="-2")

    def badge(self, right, top, version):
        lab = f"v{version}"
        bw = len(lab) * 9 + 22
        self.rect(right - bw, top, bw, 26, fill=CARD, stroke=INK, sw=2)
        self.text(right - bw / 2, top + 18, lab, size=12, fill=INK, weight=700, anchor="middle", mono=True)

    def tier_color(self, role, think, work):
        return {"thinking": think, "worker": work, "gate": INK, "standalone": MUTED}[role]

    def svg(self):
        self.o('</svg>')
        return "\n".join(self.p)


def render_horizontal(features, version):
    c = features["branding"]["colors"]
    THINK, WORK = c["thinking"], c["worker"]
    tagline = features.get("tagline", "")
    W, H, PAD = 1200, 470, 48
    cv = Canvas(W, H, f"Hyperflow v{version}",
                f"{tagline} — first init once with scaffold, then the chain: "
                f"plan, dispatch, audit, deploy, with plan and execute stages and a Worker to Reviewer review at every step.")
    cv.frame()
    cv.wordmark(PAD, 64, 38)
    cv.badge(W - PAD, 40, version)
    cv.text(PAD, 92, (tagline if len(tagline) <= 70 else tagline[:67] + "…"), size=12.5, fill=MUTED, mono=True)
    cv.text(PAD, 116, "INIT ONCE  ·  scaffold sets up the project + .hyperflow/ cache", size=11, fill=INK, mono=True)

    # plan-stage bracket
    cv.text(W / 2, 150, "PLAN STAGE", size=11, fill=THINK, anchor="middle", ls="0.18em")
    cv.text(W / 2, 164, "orchestrates every phase · triages · reviews every output", size=9, fill=MUTED, anchor="middle")
    cv.line(PAD, 182, W - PAD, 182, stroke=THINK, sw=1.25, op=0.5)
    cv.line(PAD, 182, PAD, 176, stroke=THINK, sw=1.25, op=0.5)
    cv.line(W - PAD, 182, W - PAD, 176, stroke=THINK, sw=1.25, op=0.5)

    n = len(CHAIN)
    cw, ch, cy = 164, 86, 200
    gap = (W - 2 * PAD - n * cw) / (n - 1)
    for i, name in enumerate(CHAIN):
        role = ROLE[name]
        nx = PAD + i * (cw + gap)
        cv.card(nx, cy, cw, ch)
        if role == "gate":
            cv.rect(nx, cy, cw, ch, stroke=INK, sw=2, dash="5 4")
            cv.rect(nx, cy, cw, 5, fill=PAPER2)
        else:
            cv.rect(nx, cy, cw, 5, fill=cv.tier_color(role, THINK, WORK))
        cv.text(nx + cw / 2, cy + 34, "/" + name, size=17, fill=INK, weight=700, anchor="middle", mono=True)
        cv.text(nx + cw / 2, cy + 52, SUB[name], size=8, fill=MUTED, anchor="middle", ls="0.8", mono=True)
        cv.line(nx + 16, cy + 62, nx + cw - 16, cy + 62, stroke="#C9C2AE", sw=1)
        cv.text(nx + cw / 2, cy + 77, CAPTION[name], size=10, fill=MUTED, anchor="middle")
        if i < n - 1:
            cv.line(nx + cw + 4, cy + ch / 2, nx + cw + gap - 4, cy + ch / 2, marker="arr")

    # execute-stage bracket
    by = cy + ch + 18
    cv.line(PAD, by, W - PAD, by, stroke=WORK, sw=1.25, op=0.5)
    cv.line(PAD, by, PAD, by + 6, stroke=WORK, sw=1.25, op=0.5)
    cv.line(W - PAD, by, W - PAD, by + 6, stroke=WORK, sw=1.25, op=0.5)
    cv.text(W / 2, by + 22, "EXECUTE STAGE", size=11, fill=WORK, anchor="middle", ls="0.18em")
    cv.text(W / 2, by + 36, "executes in parallel — persona-stitched per task", size=9, fill=MUTED, anchor="middle")

    # review note
    ry = by + 52
    cv.rect(PAD, ry, W - 2 * PAD, 26, fill="#ECE7D7", stroke="#C9C2AE", sw=1, dash="3 3")
    cv.text(W / 2, ry + 17, "every step dispatches a Worker → Reviewer pair · no output reaches the next step unreviewed",
            size=9.5, fill=MUTED, anchor="middle")

    fy = H - 22
    cv.text(PAD, fy, "github.com/Mohammed-Abdelhady/hyperflow", size=10.5, fill=MUTED, mono=True)
    cv.text(W - PAD, fy, "premium multi-agent orchestration · Claude Code · OpenCode · Antigravity",
            size=10.5, fill=MUTED, anchor="end", mono=True)
    return cv.svg()


def render_vertical(features, version):
    c = features["branding"]["colors"]
    THINK, WORK = c["thinking"], c["worker"]
    tagline = features.get("tagline", "")
    W, H, PAD = 760, 880, 44
    cv = Canvas(W, H, f"Hyperflow v{version}",
                f"{tagline} — first init once with scaffold, then the chain stacked top to bottom: "
                f"plan, dispatch, audit, deploy, every step reviewed by a Worker to Reviewer pair.")
    cv.frame()
    cv.wordmark(PAD, 92, 56)
    cv.badge(W - PAD, 50, version)
    cv.text(PAD, 132, (tagline if len(tagline) <= 52 else tagline[:49] + "…"), size=13, fill=MUTED, mono=True)
    cv.text(PAD, 160, "INIT ONCE · scaffold sets up the project", size=11.5, fill=INK, mono=True)

    cv.rect(PAD, 178, 12, 12, fill=THINK)
    cv.text(PAD + 22, 188, "plan · plans + reviews every step", size=11, fill=INK, mono=True)
    cv.rect(PAD, 200, 12, 12, fill=WORK)
    cv.text(PAD + 22, 210, "execute · runs in parallel", size=11, fill=INK, mono=True)

    cv.text(PAD, 250, "THE CHAIN", size=11, fill=MUTED, weight=700, ls="2", mono=True)
    rx, rw, rh, gap, y0 = PAD, W - 2 * PAD, 70, 18, 266
    for i, name in enumerate(CHAIN):
        role = ROLE[name]
        ry = y0 + i * (rh + gap)
        cv.card(rx, ry, rw, rh)
        if role == "gate":
            cv.rect(rx, ry, rw, rh, stroke=INK, sw=2, dash="5 4")
            cv.rect(rx, ry, 8, rh, fill=PAPER2)
        else:
            cv.rect(rx, ry, 8, rh, fill=cv.tier_color(role, THINK, WORK))
        cv.text(rx + 28, ry + 32, "/" + name, size=22, fill=INK, weight=700, mono=True)
        cv.text(rx + 28, ry + 54, CAPTION[name], size=12, fill=MUTED)
        cv.text(rx + rw - 20, ry + 28, SUB[name], size=9, fill=MUTED, anchor="end", ls="0.6", mono=True)
        if i < len(CHAIN) - 1:
            cx = rx + rw / 2
            cv.line(cx, ry + rh + 2, cx, ry + rh + gap - 2, marker="arr")

    ny = y0 + len(CHAIN) * (rh + gap) + 4
    cv.rect(PAD, ny, rw, 30, fill="#ECE7D7", stroke="#C9C2AE", sw=1, dash="3 3")
    cv.text(W / 2, ny + 19, "every step → Worker → Reviewer · nothing ships unreviewed", size=10, fill=MUTED, anchor="middle")

    fy = H - 22
    cv.text(W / 2, fy, "github.com/Mohammed-Abdelhady/hyperflow", size=10.5, fill=MUTED, anchor="middle", mono=True)
    return cv.svg()


def main():
    import sys
    ap = argparse.ArgumentParser(description="Generate the Hyperflow hero images")
    ap.add_argument("--version")
    ap.add_argument("--output", default=str(ROOT / "docs" / "assets" / "hero.svg"))
    ap.add_argument("--vertical-output", default=str(ROOT / "docs" / "assets" / "hero-vertical.svg"))
    args = ap.parse_args()
    feats = load_features()
    version = args.version or feats.get("version", "0.0.0")
    for path, svg in ((Path(args.output), render_horizontal(feats, version)),
                      (Path(args.vertical_output), render_vertical(feats, version))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path} ({len(svg):,} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
