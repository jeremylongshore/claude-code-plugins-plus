---
title: "Fix the Dependabot Pile-Up: Policy Over Patches"
description: "15 dependabot PRs piling up? Stop merging individually. Group minor/patch updates, auto-merge when green, keep security updates isolated."
date: "2026-07-08"
tags: ["ci-cd", "devops", "automation", "release-engineering"]
featured: false
---
Guidewire's dependabot backlog hit 15 open PRs by late June. tsx 4.21→4.23. undici 6.25→8.3. @opentelemetry/sdk-node. pg 8.20→8.21. GitHub Actions bumps on checkout, upload-artifact, setup-java, gitleaks-action, cache. All of them CI-green. All of them waiting for a human to click merge.

I merged 14. Closed 1.

The 1 that stayed closed was a `biome-2` MAJOR version bump that broke the lint gate. A major version of the lint/format tool can change rule defaults or config schema, so it legitimately turns the Lint gate red until the config is migrated. That's not a flaky failure — that's the tool working as designed. It needed actual triage, not a merge button. It was the only PR that should have waited.

The other 14 should have never piled up at all.

**The symptom vs. the cause.** Merging 14 PRs clears the board for a day. But a cleared board is not a fixed system. Dependabot.yml had no grouping. `open-pull-requests-limit: 10`. No auto-merge configured. Every version bump — patch, minor, major, security alert — opened its own PR and waited for human eyes, even if CI passed. That's the pile-up machine. You can burn down 15 PRs in an afternoon, but if the policy stays broken, 15 more arrive next month. The real fix is the policy.

**Three moves stop the pile-up.**

**Move 1: Group version updates. Leave security updates alone.**

```yaml
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    groups:
      npm-minor-patch:
        applies-to: version-updates   # security-updates are NOT grouped
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
```

Routine patch and minor bumps now roll into one PR per ecosystem. MAJOR bumps stay individual (they need human review). Security updates stay individual (they always did, but this makes it explicit). The grouping kills the noise. The individual carve-outs preserve the safety.

**Move 2: Lower the limit.** From 10 open PRs to 5 for npm, 3 for github-actions. Fewer outstanding PRs mean faster triage cycles and clearer signal.

**Move 3: Auto-merge grouped patch/minor PRs once CI passes.**

```yaml
      - name: Enable auto-merge for patch & minor updates
        if: >-
          ${{ steps.meta.outputs.update-type == 'version-update:semver-patch' ||
          steps.meta.outputs.update-type == 'version-update:semver-minor' }}
        run: gh pr merge --auto --squash "$PR_URL"
```

When dependabot opens a grouped PR, `fetch-metadata` reports `update-type` as the highest semver bump in that group. Since the groups only contain patch + minor, grouped PRs pass this `if:` and auto-merge once every required check passes. MAJOR bumps report `semver-major` and skip the gate. The main branch's ruleset (required checks + required review) still enforces itself. Nothing merges red. Nothing merges unreviewed.

Humans now only see MAJOR version bumps and security updates. The system merges the routine stuff on its own. The pile-up stops recurring.

This is the noise/safety split: silence the former, never the latter.

The measure of the fix is not the empty board today. It's whether next month's routine bumps land themselves and only the ones that need judgment reach a human.

**Also shipped — intent-os:** intent-os got a registry cleanup (2 commits) — corrected the automations docs after a notify-spine hardening. The hashnode monitor is fixed, not disabled. A registry that lies about what your automation does is worse than no registry, because you stop checking it — so this kind of correction keeps the docs trustworthy.

**intent-mail:** One-line README fix: tool count (45→47) and a corrected repo URL.

## Related Posts

- [Backlog Zero: Burning Down the Estate with a Triage Machine](/posts/backlog-zero-estate-triage-machine/)
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/)
