#!/usr/bin/env python3
"""CRAP (Change Risk Analyzer and Predictor) calculator — multi-language.

Reads language-native complexity and coverage outputs, computes
    CRAP(m) = C(m)^2 * (1 - cov(m)/100)^3 + C(m)
for every method, ranks them, and emits CSV + JSON.

Walls 5 and 6 of the Seven Walls (audit-tests skill):
  - Production code: no method CRAP > 30; project average <= 10.
  - Test code:       no method CRAP > 15.

Thresholds are configurable via --threshold (local tuning is logged).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class MethodScore:
    language: str
    path: str
    method: str
    complexity: int
    coverage: float
    crap: float
    kind: str  # "src" or "test"


def crap(complexity: int, coverage_pct: float) -> float:
    cov = max(0.0, min(100.0, coverage_pct)) / 100.0
    return (complexity ** 2) * ((1.0 - cov) ** 3) + complexity


def detect_language(root: Path) -> str:
    candidates = [
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("package.json", "js"),
        ("go.mod", "go"),
        ("Cargo.toml", "rust"),
        ("pom.xml", "java"),
        ("build.gradle", "java"),
        ("build.gradle.kts", "java"),
        ("composer.json", "php"),
        ("Gemfile", "ruby"),
        ("*.csproj", "dotnet"),
    ]
    for pattern, lang in candidates:
        if "*" in pattern:
            if any(root.glob(pattern)):
                return lang
        elif (root / pattern).is_file():
            return lang
    return "unknown"


def which_or_none(cmd: str) -> str | None:
    return shutil.which(cmd)


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return p.returncode, p.stdout, p.stderr


# ---------- Python: radon + coverage ----------

def score_python(root: Path, kind: str) -> list[MethodScore]:
    if kind == "src":
        candidates = ["src", "myapp", "app"]
        scanned = [t for t in candidates if (root / t).is_dir()]
        if not scanned:
            test_dirs = {"tests", "test", "spec", "specs", "features", "__tests__"}
            ignore = {".git", ".venv", "venv", "node_modules", "dist", "build", "target", ".tox", ".mypy_cache", ".pytest_cache", "reports", "__pycache__"}
            scanned = [
                p.name for p in root.iterdir()
                if p.is_dir()
                and not p.name.startswith(".")
                and p.name not in ignore
                and p.name not in test_dirs
                and any(p.rglob("*.py"))
            ]
    else:
        candidates = ["tests", "test"]
        scanned = [t for t in candidates if (root / t).is_dir()]
    if not scanned:
        return []

    if which_or_none("radon") is None:
        print("[crap-score] radon not installed (pip install radon)", file=sys.stderr)
        return []

    complexity: dict[tuple[str, str], int] = {}
    for tgt in scanned:
        rc, out, err = run(["radon", "cc", "-s", "-a", "-j", tgt], root)
        if rc != 0 or not out.strip():
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        for fpath, blocks in data.items():
            for block in blocks:
                name = block.get("name") or ""
                method_key = (fpath, name)
                complexity[method_key] = int(block.get("complexity", 0))

    coverage: dict[str, float] = {}
    cov_json = root / "coverage.json"
    if not cov_json.is_file() and which_or_none("coverage"):
        run(["coverage", "json", "-o", "coverage.json", "--fail-under=0"], root)
    if cov_json.is_file():
        try:
            cov_data = json.loads(cov_json.read_text())
            for fpath, summary in cov_data.get("files", {}).items():
                pct = summary.get("summary", {}).get("percent_covered", 0.0)
                coverage[fpath] = float(pct)
        except (OSError, json.JSONDecodeError):
            pass

    scores: list[MethodScore] = []
    for (fpath, name), c in complexity.items():
        cov = coverage.get(fpath, 0.0)
        scores.append(
            MethodScore(
                language="python",
                path=fpath,
                method=name,
                complexity=c,
                coverage=cov,
                crap=crap(c, cov),
                kind=kind,
            )
        )
    return scores


# ---------- Go: gocyclo + go test -cover ----------

def score_go(root: Path, kind: str) -> list[MethodScore]:
    if which_or_none("gocyclo") is None:
        print("[crap-score] gocyclo not installed", file=sys.stderr)
        return []

    rc, out, _ = run(["gocyclo", "-ignore", "_test.go" if kind == "src" else ".*\\.go$", "."], root)
    complexity: list[tuple[str, str, int]] = []
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) < 4:
            continue
        try:
            c = int(parts[0])
        except ValueError:
            continue
        pkg = parts[1]
        func = parts[2]
        fpath = parts[3].split(":", 1)[0]
        include = fpath.endswith("_test.go") if kind == "test" else not fpath.endswith("_test.go")
        if include:
            complexity.append((fpath, f"{pkg}.{func}", c))

    coverage: dict[str, float] = {}
    cov_out = root / "coverage.out"
    if not cov_out.is_file():
        run(["go", "test", "-coverprofile=coverage.out", "-covermode=atomic", "./..."], root)
    if cov_out.is_file() and which_or_none("go"):
        rc, out, _ = run(["go", "tool", "cover", "-func=coverage.out"], root)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[-1].endswith("%"):
                fpath = parts[0].split(":", 1)[0]
                try:
                    pct = float(parts[-1].rstrip("%"))
                except ValueError:
                    continue
                coverage[fpath] = pct

    scores: list[MethodScore] = []
    for fpath, name, c in complexity:
        cov = coverage.get(fpath, 0.0)
        scores.append(
            MethodScore(
                language="go", path=fpath, method=name, complexity=c,
                coverage=cov, crap=crap(c, cov), kind=kind,
            )
        )
    return scores


# ---------- JS/TS: complexity-report + c8 ----------

def score_js(root: Path, kind: str) -> list[MethodScore]:
    cr_bin = which_or_none("cr") or which_or_none("complexity-report")
    if cr_bin is None:
        print("[crap-score] complexity-report not installed (npm i -D complexity-report)", file=sys.stderr)
        return []
    target = "src" if kind == "src" else "tests"
    if not (root / target).is_dir():
        return []
    rc, out, _ = run([cr_bin, "--format", "json", target], root)
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []

    cov_path = root / "coverage" / "coverage-summary.json"
    coverage: dict[str, float] = {}
    if cov_path.is_file():
        try:
            cov_data = json.loads(cov_path.read_text())
            for fpath, summary in cov_data.items():
                if fpath == "total":
                    continue
                lines_pct = summary.get("lines", {}).get("pct", 0.0)
                coverage[fpath] = float(lines_pct)
        except (OSError, json.JSONDecodeError):
            pass

    scores: list[MethodScore] = []
    for report in data.get("reports", []):
        fpath = report.get("path", "")
        cov = coverage.get(fpath, 0.0)
        for func in report.get("functions", []):
            c = int(func.get("cyclomatic", 1))
            scores.append(
                MethodScore(
                    language="js", path=fpath, method=func.get("name", "<anon>"),
                    complexity=c, coverage=cov, crap=crap(c, cov), kind=kind,
                )
            )
    return scores


# ---------- Rust: rust-code-analysis + tarpaulin ----------

def score_rust(root: Path, kind: str) -> list[MethodScore]:
    rca = which_or_none("rust-code-analysis-cli")
    if rca is None:
        print("[crap-score] rust-code-analysis-cli not installed", file=sys.stderr)
        return []
    target = "src" if kind == "src" else "tests"
    if not (root / target).is_dir():
        return []
    rc, out, _ = run([rca, "-m", "-O", "json", "-p", target], root)
    if rc != 0 or not out.strip():
        return []
    complexity: list[tuple[str, str, int]] = []
    for line in out.splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        fpath = rec.get("name", "")
        metrics = rec.get("metrics", {}).get("cyclomatic", {})
        for func in rec.get("spaces", []):
            c = int(func.get("metrics", {}).get("cyclomatic", {}).get("sum", 1))
            complexity.append((fpath, func.get("name", "<anon>"), c))
    scores: list[MethodScore] = []
    for fpath, name, c in complexity:
        scores.append(
            MethodScore(
                language="rust", path=fpath, method=name, complexity=c,
                coverage=0.0, crap=crap(c, 0.0), kind=kind,
            )
        )
    return scores


DISPATCH = {
    "python": score_python,
    "go": score_go,
    "js": score_js,
    "rust": score_rust,
}


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="Repository root")
    ap.add_argument("--target", choices=["src", "test", "both"], default="both")
    ap.add_argument("--format", choices=["csv", "json", "both"], default="both")
    ap.add_argument("--out", default="reports/crap", help="Output directory")
    ap.add_argument("--lang", default="auto",
                    help="Force language (python|go|js|rust); default auto-detect")
    ap.add_argument("--threshold-prod", type=float, default=30.0,
                    help="Production CRAP max (default 30)")
    ap.add_argument("--threshold-test", type=float, default=15.0,
                    help="Test CRAP max (default 15)")
    ap.add_argument("--threshold-avg", type=float, default=10.0,
                    help="Project average max (default 10)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    lang = args.lang if args.lang != "auto" else detect_language(root)
    if lang not in DISPATCH:
        print(f"[crap-score] unsupported language: {lang}", file=sys.stderr)
        return 2

    if any(t != d for t, d in (
        (args.threshold_prod, 30.0),
        (args.threshold_test, 15.0),
        (args.threshold_avg, 10.0),
    )):
        print(f"[crap-score] threshold override: prod={args.threshold_prod} "
              f"test={args.threshold_test} avg={args.threshold_avg}",
              file=sys.stderr)

    kinds = ["src", "test"] if args.target == "both" else [args.target]
    all_scores: list[MethodScore] = []
    for kind in kinds:
        all_scores.extend(DISPATCH[lang](root, kind))

    out_dir = root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.format in ("csv", "both"):
        for kind in kinds:
            ranked = sorted(
                [s for s in all_scores if s.kind == kind],
                key=lambda s: s.crap, reverse=True,
            )
            csv_path = out_dir / f"crap-{kind}.csv"
            with csv_path.open("w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["rank", "crap", "complexity", "coverage_pct", "path", "method"])
                for i, s in enumerate(ranked, 1):
                    w.writerow([i, f"{s.crap:.2f}", s.complexity,
                                f"{s.coverage:.1f}", s.path, s.method])

    src_scores = [s for s in all_scores if s.kind == "src"]
    test_scores = [s for s in all_scores if s.kind == "test"]
    prod_max = max((s.crap for s in src_scores), default=0.0)
    test_max = max((s.crap for s in test_scores), default=0.0)
    prod_avg = (sum(s.crap for s in src_scores) / len(src_scores)) if src_scores else 0.0

    prod_blockers = [asdict(s) for s in src_scores if s.crap > args.threshold_prod]
    test_blockers = [asdict(s) for s in test_scores if s.crap > args.threshold_test]
    avg_fail = prod_avg > args.threshold_avg

    pass_ = not (prod_blockers or test_blockers or avg_fail)

    summary = {
        "language": lang,
        "thresholds": {
            "production_max": args.threshold_prod,
            "test_max": args.threshold_test,
            "project_avg_max": args.threshold_avg,
        },
        "production": {
            "methods_scored": len(src_scores),
            "max_crap": round(prod_max, 2),
            "avg_crap": round(prod_avg, 2),
            "blockers": prod_blockers,
        },
        "test": {
            "methods_scored": len(test_scores),
            "max_crap": round(test_max, 2),
            "blockers": test_blockers,
        },
        "pass": pass_,
    }

    if args.format in ("json", "both"):
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps({"pass": pass_, "summary_path": str(out_dir / "summary.json")}))
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
