"""Regression checks for ROOT resolution in the ``sync-marketplace`` chain.

Issue #1436. Both generators in the chain derived their repository root as
``resolve(dirname(new URL(import.meta.url).pathname), '..')``. ``URL.pathname``
is platform-independent and keeps a leading slash before a Windows drive letter,
so ``/C:/repo/scripts/x.mjs`` is read as drive-relative and ROOT resolves to
``C:\\C:\\repo``. The code is correct on POSIX and only wrong on Windows, which
is why CI stayed green.

One half failed loudly and one half did not, and the silent half is the reason
these checks exist. ``generate-plugin-package-jsons.mjs`` globbed nothing on the
bad ROOT, printed ``Wrote 0 package.json files.`` and exited 0 -- on a tree
holding 440 plugins. Only ``generate-readme-toc.mjs``, further down the chain,
raised ENOENT.

These tests run on Linux CI, where the original defect is by definition
unreproducible. So the static half pins the corrected form in both scripts, and
the behavioural half provokes the *consequence* -- an empty discovery -- in a way
that is platform-independent: run the generator from a location where
``../plugins`` does not exist and require it to fail rather than to succeed
quietly.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_JSON_GENERATOR = REPO_ROOT / "scripts" / "generate-plugin-package-jsons.mjs"
TOC_GENERATOR = REPO_ROOT / "scripts" / "generate-readme-toc.mjs"

# Exactly the two scripts `npm run sync-marketplace` invokes after
# sync-marketplace.cjs. The wider `.pathname` usage elsewhere in scripts/ is
# deliberately out of scope here -- see the issue thread.
CHAIN_GENERATORS = (PACKAGE_JSON_GENERATOR, TOC_GENERATOR)

PATHNAME_FORM = "new URL(import.meta.url).pathname"
CORRECT_FORM = "fileURLToPath(import.meta.url)"


@pytest.mark.parametrize("generator", CHAIN_GENERATORS, ids=lambda p: p.name)
def test_chain_generator_derives_root_with_file_url_to_path(generator: Path) -> None:
    source = generator.read_text(encoding="utf-8")

    root_lines = [
        line for line in source.splitlines() if line.startswith("const ROOT =")
    ]
    assert len(root_lines) == 1, f"{generator.name}: expected exactly one ROOT binding"

    assert CORRECT_FORM in root_lines[0], (
        f"{generator.name}: ROOT must be derived with fileURLToPath. "
        "URL.pathname resolves to a doubled drive letter on Windows (#1436)."
    )
    assert "fileURLToPath" in source, f"{generator.name}: fileURLToPath is not imported"


@pytest.mark.parametrize("generator", CHAIN_GENERATORS, ids=lambda p: p.name)
def test_chain_generator_does_not_reintroduce_the_pathname_form(generator: Path) -> None:
    """The prose may name the broken form; the code may not use it.

    Both files document why `URL.pathname` is wrong, so a bare substring search
    would match the explanation and never fail. Comment lines are dropped first
    so this asserts on code.
    """
    code_lines = [
        line
        for line in generator.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith(("//", "*", "/*"))
    ]
    offenders = [line.strip() for line in code_lines if PATHNAME_FORM in line]

    assert not offenders, (
        f"{generator.name}: URL.pathname is back in executable code: {offenders}"
    )


def _run_generator_from(directory: Path) -> subprocess.CompletedProcess[str]:
    """Copy the generator somewhere `../plugins` does not exist, and run it.

    The script derives ROOT from its own location and imports only node
    builtins, so relocating it is a faithful way to produce a wrong ROOT on any
    platform -- including the Linux runner, where the drive-letter defect cannot
    occur at all.
    """
    scripts_dir = directory / "scripts"
    scripts_dir.mkdir(parents=True)
    relocated = scripts_dir / PACKAGE_JSON_GENERATOR.name
    shutil.copy2(PACKAGE_JSON_GENERATOR, relocated)

    return subprocess.run(
        ["node", str(relocated), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_package_json_generator_fails_closed_on_zero_discovery() -> None:
    """The silent half of #1436: zero plugins found must not be exit 0.

    Before the fix this printed a success summary and exited 0, so the
    `sync-marketplace` step reported done having written nothing.
    """
    with tempfile.TemporaryDirectory() as tmp:
        result = _run_generator_from(Path(tmp))

    assert result.returncode != 0, (
        "generator exited 0 having discovered no plugins; that is the silent "
        f"failure #1436 is about.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    combined = result.stdout + result.stderr
    assert "Resolved ROOT:" in combined, (
        "the refusal must name the resolved ROOT -- when this fires, the "
        f"resolved path is the diagnosis.\n{combined}"
    )
    assert "Wrote 0 package.json files." not in result.stdout, (
        "the generator reported a successful write summary on an empty discovery"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
def test_package_json_generator_still_discovers_this_repository() -> None:
    """The other direction, so the guard cannot be satisfied by refusing always.

    A check that is happiest when the tool is broken is measuring the wrong
    thing: this asserts the corrected ROOT actually finds the plugin tree.
    """
    result = subprocess.run(
        ["node", str(PACKAGE_JSON_GENERATOR), "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"dry run failed against the real repository.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    discovered = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("Plugins with package.json already:")
    ]
    assert discovered, f"no discovery summary in output:\n{result.stdout}"

    count = int(discovered[0].split(":")[1].strip())
    assert count > 0, (
        "discovered 0 plugins in a repository that has them -- the ROOT "
        "regression is back"
    )
