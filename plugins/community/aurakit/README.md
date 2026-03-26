# AuraKit

**Plugin:** `aurakit` | **Skill:** `aura`

AuraKit is an all-in-one Claude Code skill that consolidates 33 operational modes behind a single `/aura` command. It provides 6-layer security enforcement, 23 lifecycle hooks, 8-language support, and achieves 75% token savings through Sonnet-amplified compressed instructions.

## What It Does

AuraKit ships a single auto-activating skill (`aura`) that replaces the need for dozens of separate skills. Modes cover the full development lifecycle: scaffolding, coding, reviewing, testing, debugging, deploying, security auditing, documentation, and more.

### Key Features

- **33 Modes** — `/aura build`, `/aura fix`, `/aura review`, `/aura deploy`, `/aura security`, and 28 more
- **6-Layer Security** — .env guard, disallowed-tools separation, bash-guard, secret scanning, worktree isolation, convention checks
- **23 Hooks** — Pre/post lifecycle hooks for commits, pushes, builds, tests, and deployments
- **8 Languages** — TypeScript, Python, Go, Rust, Java, C#, Ruby, PHP
- **75% Token Savings** — Compressed instruction format optimized for Sonnet context efficiency
- **Cross-Platform** — Windows, macOS, Linux with full path normalization
- **OWASP-Complete** — Built-in security patterns covering the OWASP Top 10

## Installation

### npm (Recommended)

```bash
npm install -g @smorky85/aurakit
```

### Manual

```bash
git clone https://github.com/smorky850612/Aurakit.git
cd Aurakit && bash install.sh
```

### Claude Code Plugin

```bash
claude --plugin-dir /path/to/aurakit
```

## Usage

```
/aura build     — Scaffold and generate project code
/aura fix       — Diagnose and fix bugs
/aura review    — Code review with security focus
/aura deploy    — Build, test, and deploy
/aura security  — OWASP security audit
/aura test      — Generate and run tests
/aura docs      — Generate documentation
/aura refactor  — Refactor with safety checks
```

## Links

- **GitHub:** [smorky850612/Aurakit](https://github.com/smorky850612/Aurakit)
- **npm:** [@smorky85/aurakit](https://www.npmjs.com/package/@smorky85/aurakit)

## License

MIT
