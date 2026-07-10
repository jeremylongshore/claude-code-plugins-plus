#!/usr/bin/env python3
"""
generate-demo-cast.py
Writes a synthesized asciinema v2 cast file simulating a Hyperflow demo session.
Content is driven by config/features.json so every release reflects the latest
capabilities automatically.

Usage:
    python3 scripts/generate-demo-cast.py [--output PATH]
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Features loader
# ---------------------------------------------------------------------------

def load_features() -> dict:
    ROOT = Path(__file__).resolve().parent.parent
    return json.loads((ROOT / "config" / "features.json").read_text())


# ---------------------------------------------------------------------------
# Cast DSL
# ---------------------------------------------------------------------------

class Cast:
    """Minimal DSL for building an asciinema v2 event list."""

    def __init__(self):
        self.t: float = 0.0
        self.events: list = []

    def wait(self, seconds: float) -> "Cast":
        self.t += seconds
        return self

    def out(self, text: str, char_delay: float = 0.0) -> "Cast":
        """Emit text as a single event (or char-by-char if char_delay > 0)."""
        if char_delay > 0:
            for ch in text:
                self.events.append([round(self.t, 4), "o", ch])
                self.t += char_delay
        else:
            self.events.append([round(self.t, 4), "o", text])
        return self

    def type(self, text: str, char_delay: float = 0.06) -> "Cast":
        """Simulate user typing keystrokes with per-character delay."""
        return self.out(text, char_delay=char_delay)

    def line(self, text: str) -> "Cast":
        """Emit text followed by CRLF as a single event."""
        self.events.append([round(self.t, 4), "o", text + "\r\n"])
        return self

    def prompt(self, label: str = "$ ") -> "Cast":
        """Emit a shell prompt."""
        self.events.append([round(self.t, 4), "o", label])
        return self


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

RESET   = "\x1b[0m"
BOLD    = "\x1b[1m"
MAGENTA = "\x1b[35m"   # Orchestrator / banner / decision + review roles
CYAN    = "\x1b[36m"   # Workers
GREEN   = "\x1b[32m"   # Success ✓
RED     = "\x1b[31m"   # Failure ✗ / BLOCKED / SECURITY_VIOLATION
YELLOW  = "\x1b[33m"   # Memory
GRAY    = "\x1b[90m"   # Dim/secondary

def mg(s: str) -> str:   return MAGENTA + s + RESET
def worker(s: str) -> str:   return CYAN    + s + RESET
def gn(s: str) -> str:   return GREEN   + s + RESET
def rd(s: str) -> str:   return RED     + s + RESET
def yl(s: str) -> str:   return YELLOW  + s + RESET
def gr(s: str) -> str:   return GRAY    + s + RESET
def bo(s: str) -> str:   return BOLD    + s + RESET
def rb(s: str) -> str:   return RED + BOLD + s + RESET   # red bold


# ---------------------------------------------------------------------------
# Demo script — 9 scenes, ~40s total, driven by features.json
# Elegant style: no ⚡, ✓, ✗ icons. Em-dash separators. Bold for decision/review roles.
# ---------------------------------------------------------------------------

def script(features: dict) -> Cast:
    c = Cast()

    version    = features["version"]
    memory_cfg = features["memory"]

    # ── Scene 1 · Activation (0–7s raw) ──────────────────────────────────────
    # Shows: startup, session-model note, memory loaded from prior session.
    # Target GIF playback at 1.6x: ~4.5s
    c.prompt("~/hyperflow-demo $ ")
    c.wait(0.50)
    c.type("claude")
    c.wait(0.20)
    c.out("\r\n")
    c.wait(0.40)

    c.line(mg(f"Hyperflow v{version}"))
    c.wait(0.20)
    c.line(gr("Every agent runs on your session model — roles differ by responsibility"))
    c.wait(0.50)
    c.line(gr("Analyzing project — 4 searchers in parallel"))
    c.wait(1.20)
    c.line(gn("Cached") + gr(" — .hyperflow/ ready · no incomplete tasks"))
    c.wait(0.40)
    c.line(yl("[memory]") + gr(f"  loaded 3 entries  ·  {memory_cfg['location']}"))
    c.wait(1.20)
    # Scene 1 ends ≈ 7s raw (≈ 4.4s at 1.6x)

    # ── Scene 2 · Full chain: spec → scope → dispatch ─────────────────────────
    # Shows: chain-starter, triage, spec, dispatch, per-batch review,
    #        quality gates, wrap-up.
    # Role split legible via explicit role labels on every Agent line.
    #
    # Claude Code real markers used:
    #   ⏺  filled-circle status bullet ("I'm doing X")
    #   ⎿  tree connector below a bullet for the result
    #   Skill / Agent / Bash / Write / Explore — Claude Code tool-use headers
    #   Done (N tool uses · Xk tokens · Ys) — real result-line format
    c.line(gr(""))
    c.prompt()
    c.wait(0.40)
    c.type("/hyperflow:plan \"Add authentication with login + middleware\"", char_delay=0.04)
    c.wait(0.20)
    c.out("\r\n")
    c.wait(0.40)

    # ── Skill load + step-0 gate ──────────────────────────────────────────────
    c.line(mg("⏺") + gr(" ") + bo("Skill") + gr("(hyperflow:plan)"))
    c.line(gr("  ⎿  Successfully loaded skill"))
    c.wait(0.50)

    c.line(gr(""))
    c.line(yl("?  Advance through the chain automatically or pause between phases?"))
    c.wait(0.30)
    c.line(gr("   ") + bo("Auto (Recommended)") + gr("  — chain forward with no gates"))
    c.wait(0.30)
    c.line(gr("   Manual               — pause between phases and ask before advancing"))
    c.wait(0.40)
    c.line(gr("   your choice: ") + worker("Auto"))
    c.wait(0.60)

    # ── Triage — Classifier (decision role) ──────────────────────────────────
    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Decision") + gr(" — Classifier, triage)"))
    c.line(gr("  ⎿  Done (4 tool uses · 1.8k tokens · 6s)"))
    c.wait(0.30)
    c.line(gr("  types:[api, security, frontend] · flow: standard · ambiguity: 0.4 (light)"))
    c.wait(0.70)

    # ── Design phase (inside plan): Analyst (decision role) + Worker Writers ──
    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Explore") + gr("(Map existing auth context)"))
    c.line(gr("  ⎿  Done (18 tool uses · 22.4k tokens · 32s)"))
    c.wait(0.30)
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Reviewer") + gr(" — context coverage)"))
    c.line(gr("  ⎿  Done (3 tool uses · 6.1k tokens · 9s) · ") + gn("PASS"))
    c.wait(0.60)

    c.line(gr(""))
    c.line(yl("?  Token storage?"))
    c.wait(0.30)
    c.line(gr("   ") + bo("Server sessions (Recommended)") + gr("  — revocable, fits project DB conventions"))
    c.wait(0.30)
    c.line(gr("   JWT stateless                 — simpler, harder to revoke"))
    c.wait(0.40)
    c.line(gr("   your choice: ") + worker("Server sessions"))
    c.wait(0.60)

    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Decision") + gr(" — Analyst, 6-dim exploration)"))
    c.line(gr("  ⎿  Done (6 tool uses · 14.8k tokens · 28s)"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" 5 sections — each ") + worker("Worker") + gr(" Writer → ") + mg("Reviewer") + gr(" → approved"))
    c.line(gr("  ⎿  Architecture · Data flow · Key decisions · Edge cases · File structure"))
    c.wait(0.50)
    c.line(mg("⏺") + gr(" ") + bo("Write") + gr("(.hyperflow/specs/auth.md)"))
    c.line(gr("  ⎿  Wrote 142 lines"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" Design approved — decomposing into a batched task graph."))
    c.wait(0.70)

    # ── Decompose phase (inside plan): Planner builds the batched task file + briefs ──
    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Explore") + gr("(Affected files + tests)"))
    c.line(gr("  ⎿  Done (12 tool uses · 18.6k tokens · 22s)"))
    c.wait(0.30)
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Decision") + gr(" — Planner, batch graph)"))
    c.line(gr("  ⎿  Done (4 tool uses · 9.2k tokens · 17s)"))
    c.wait(0.30)
    c.line(mg("⏺") + gr(" ") + bo("Write") + gr("(.hyperflow/tasks/auth.md + auth/ — 5 build-ready briefs)"))
    c.line(gr("  ⎿  Each brief: scope · exact changes · acceptance criteria · tests + E2E"))
    c.wait(0.50)

    c.line(gr(""))
    c.line(mg("⏺") + gr(" Plan — .hyperflow/tasks/auth.md (") + bo("2 batches, 5 sub-tasks") + gr(")"))
    c.wait(0.30)
    c.line(gr("  ┌───────┬──────────────┬────────────────────────────────────────┐"))
    c.line(gr("  │ ") + bo("Batch") + gr(" │ ") + bo("Workers") + gr("      │ ") + bo("Theme") + gr("                                  │"))
    c.line(gr("  ├───────┼──────────────┼────────────────────────────────────────┤"))
    c.line(gr("  │ 1     │ 3 parallel   │ User model · auth middleware · routes  │"))
    c.line(gr("  │ 2     │ 1 sequential │ Login + reset pages (uses batch 1)     │"))
    c.line(gr("  └───────┴──────────────┴────────────────────────────────────────┘"))
    c.wait(0.60)
    c.line(gr("  Auto-chaining to ") + worker("/hyperflow:dispatch") + gr("."))
    c.wait(0.60)

    # ── Dispatch: parallel Worker agents, Reviewer ────────────────────────────
    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Skill") + gr("(hyperflow:dispatch)"))
    c.line(gr("  ⎿  Successfully loaded skill"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" Batch 1 — 3 parallel ") + worker("Worker") + gr(" agents (persona-stitched)"))
    c.wait(0.50)
    c.line(mg("⏺") + gr(" 3 agents finished"))
    c.line(gr("   ├ T1: ") + worker("Searcher     ") + gr("[security + api]  · 8 tool uses · 14.2k tokens"))
    c.line(gr("   │ ⎿  Done"))
    c.line(gr("   ├ T2: ") + worker("Implementer  ") + gr("[db + security]   · 24 tool uses · 52.1k tokens"))
    c.line(gr("   │ ⎿  Done"))
    c.line(gr("   └ T3: ") + worker("Implementer  ") + gr("[security + api]  · 22 tool uses · 48.7k tokens"))
    c.line(gr("     ⎿  Done"))
    c.wait(0.50)
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Reviewer") + gr(" — Batch 1, L1–L2)"))
    c.line(gr("  ⎿  Done (14 tool uses · 31.5k tokens · 51s) · ") + gn("PASS"))
    c.wait(0.30)
    c.line(gr("  learnings injected: JWT RS256 · zod validation · server sessions"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" ") + bo("Bash") + gr("(pnpm vitest run · pnpm tsc --noEmit)"))
    c.line(gr("  ⎿  399 tests pass · typecheck clean"))
    c.wait(0.60)

    # ── Batch 2 + final integration review ───────────────────────────────────
    c.line(gr(""))
    c.line(mg("⏺") + gr(" Batch 2 — 1 ") + worker("Worker") + gr(" sequential (depends on batch 1)"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" 1 agent finished"))
    c.line(gr("   └ T4: ") + worker("Implementer  ") + gr("[frontend + ui]   · 18 tool uses · 38.4k tokens"))
    c.line(gr("     ⎿  Done (batch 1 learnings injected)"))
    c.wait(0.40)
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(") + mg("Reviewer") + gr(" — Final integration, L1–L2)"))
    c.line(gr("  ⎿  Done (11 tool uses · 24.3k tokens · 42s) · ") + gn("PASS"))
    c.wait(0.30)
    c.line(mg("⏺") + gr(" ") + bo("Bash") + gr("(pnpm vitest · tsc · build · lint)"))
    c.line(gr("  ⎿  All gates ") + gn("pass") + gr(" — 412 tests · 0 type errors · build OK"))
    c.wait(0.70)

    # ── Wrap-up: memory persist + auto-commit ─────────────────────────────────
    c.line(gr(""))
    c.line(mg("⏺") + gr(" ") + bo("Agent") + gr("(Wrap-up: memory append · auto-commit · task cleanup)"))
    c.line(gr("  ⎿  Done (7 tool uses · 9.8k tokens · 11s)"))
    c.wait(0.30)
    c.line(yl("[memory]") + gr("  persisted 2 learnings · branch: feat/auth · commit: feat: add authentication"))
    c.wait(0.70)

    # ── Usage summary ─────────────────────────────────────────────────────────
    c.line(gr(""))
    c.line(gr("── Hyperflow ──────────────────────────────────────────────────"))
    c.wait(0.20)
    c.line(mg("Decision / review") + gr("   14 agents  ") + yl("89.2k") + gr(" tokens"))
    c.wait(0.20)
    c.line(worker("Worker") + gr("              13 agents  ") + yl("198.4k") + gr(" tokens"))
    c.wait(0.20)
    c.line(gr("Total               29 agents  ") + yl("292.0k") + gr(" tokens"))
    c.wait(0.30)
    c.line(gr("───────────────────────────────────────────────────────────────"))
    c.wait(0.50)
    c.line(gr("Done · Next: ") + worker("/hyperflow:deploy") + gr(" — user-explicit, never auto."))
    c.wait(0.60)

    # ── Scene 9 · GitHub-native: issue → reviewed PR ──────────────────────────
    # Shows: /hyperflow:issue entry point — triage, chain, gated PR exit.
    c.line(gr(""))
    c.prompt()
    c.wait(0.40)
    c.type("/hyperflow:issue https://github.com/acme/api/issues/42", char_delay=0.04)
    c.wait(0.20)
    c.out("\r\n")
    c.wait(0.40)
    c.line(mg("⏺") + gr(" ") + bo("Skill") + gr("(hyperflow:issue)"))
    c.line(gr("  ⎿  Issue #42 — \"Pagination returns duplicate rows on page boundaries\""))
    c.wait(0.50)
    c.line(mg("⏺") + gr(" ") + bo("Triage") + gr(" — bug report · root-cause route · not already fixed on main"))
    c.wait(0.60)
    c.line(worker("Writer") + gr(" — spec from issue acceptance criteria · .hyperflow/specs/issue-42.md"))
    c.wait(0.60)
    c.line(gr("Chain — plan → dispatch on ") + worker("fix/issue-42-pagination") + gr(" · 3 workers · ") + bo("2 reviewers"))
    c.wait(1.00)
    c.line(gn("PASS") + gr(" — final integration review · regression test added"))
    c.wait(0.50)
    c.line(yl("?  Open a pull request for this chain?  Yes / No"))
    c.wait(0.30)
    c.line(gr("   ") + bo("Yes") + gr(" — push feature branch · gh pr create"))
    c.wait(0.50)
    c.line(gn("PR #43 opened") + gr(" — fix(pagination): dedupe boundary rows · Closes #42"))
    c.wait(1.00)

    # ── Closing ───────────────────────────────────────────────────────────────
    c.line(gr(""))
    c.line(gn("ready") + gr("  — github.com/Mohammed-Abdelhady/hyperflow"))
    c.wait(3.00)

    return c


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

HEADER = {
    "version": 2,
    "width": 120,
    "height": 34,
    "timestamp": 1715760000,
    "title": "Hyperflow — autonomous multi-agent orchestration",
    "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
}


def write_cast(cast: Cast, output_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(HEADER, separators=(",", ":")) + "\n")
        for event in cast.events:
            fh.write(json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a synthesized asciinema v2 cast for the Hyperflow demo."
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "assets", "demo.cast",
        ),
        help="Output path for the .cast file (default: docs/assets/demo.cast)",
    )
    args = parser.parse_args()

    features = load_features()
    cast = script(features)
    write_cast(cast, args.output)

    duration = cast.t
    line_count = 1 + len(cast.events)  # header + events

    print(f"Cast written to : {os.path.abspath(args.output)}")
    print(f"Total duration  : {duration:.2f}s")
    print(f"Total lines     : {line_count}")


if __name__ == "__main__":
    main()
