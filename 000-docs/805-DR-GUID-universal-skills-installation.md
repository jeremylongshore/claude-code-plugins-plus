<!-- doc-class: record -->

# Universal Skills Installation Guide

Tons of Skills publishes portable Agent Skills and native extensions in separate
catalogues. Start by inspecting the current, machine-verified harness support:

```sh
tons skills list-harnesses
tons skills doctor --harness <harness>
```

Install a portable skill only after the selected harness is shown as verified:

```sh
tons skills install <skill-directory> --harness <harness> --scope project
tons skills install <skill-directory> --harness <harness> --scope user
```

The source directory is the canonical portable artifact and must contain `SKILL.md`.
The installer copies that one source atomically into the target harness's documented
location; it does not maintain harness-specific adapter trees. It refuses unknown or
unverified harnesses and reports the exact destination. Use `--dry-run` to preview the
result. Existing Claude Code marketplace plugin workflows continue to use `ccpi`.

Omarchy shell plugins are not skills. Install them through Omarchy's native plugin flow
only after reviewing the repository and confirmation prompt; they run as unsandboxed
code in the shell process.
