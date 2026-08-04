---
title: "The Version Number That Only Existed on the Client"
description: "When a vendor releases v0.5.3, how do you know if your self-hosted relay actually has it? The version number is not the answer."
date: "2026-08-01"
tags: ["devops", "docker", "ci-cd", "debugging", "release-engineering"]
featured: false
canonical: "https://startaitools.com/posts/the-version-number-that-only-existed-on-the-client/"
---
## The Setup

Buzz, Block's open-source Nostr-based team chat relay, shipped v0.5.3. Intent Solutions runs Buzz self-hosted on its production VPS, coordinating alerts and team chat for 49 people. The natural question: does the relay need the update?

The desktop app version is clear. It auto-updates via Tauri. The relay is different. Intent Solutions keeps the relay off auto-update by design. Decision D139 in the ops log is explicit: an unreviewed container image must never auto-promote onto a live system coordinating 49 real users. The wrapped updater exists (stage, scan, test, promote or revert automatically), but arming it is a deliberate human choice.

Jeremy said yes. Update the relay to v0.5.3, stage first, then prod with auto-revert.

Claude Opus 4.8 began investigating. This is where things stalled.

## The Problem

Block ships the Buzz relay as a rolling container: `ghcr.io/block/buzz:latest`. There are no versioned release tags like `v0.5.3` for the relay image. The version string v0.5.3 is real for the codebase and the desktop app. For the relay, it is not a container release. It is a changelog entry.

To know what the relay is actually running, Claude checked the production host:

```bash
$ docker inspect --format='{{index .RepoDigests 0}}' buzz-relay
ghcr.io/block/buzz@sha256:a0f672...
```

The relay was pinned to digest `a0f672…`. Was this the current state of `:latest`, or stale?

Claude resolved the tag to its current digest using the GHCR token API. The digest that matches `docker inspect`'s RepoDigest is not in the manifest body. It comes back as a response header:

```bash
TOKEN=$(curl -s "https://ghcr.io/token?scope=repository:block/buzz:pull" | jq -r '.token')

curl -sI -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  "https://ghcr.io/v2/block/buzz/manifests/latest" | grep -i docker-content-digest
```

Result: `sha256:a0f672…`. The exact same digest already in prod.

Then Claude checked `:main`, same headers, same digest source:

```bash
curl -sI -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  "https://ghcr.io/v2/block/buzz/manifests/main" | grep -i docker-content-digest
```

Result: `sha256:3a0d6ece…`. Different. Bleeding-edge, unversioned, un-reviewed code.

## The Realization

The relay was already current on Block's stable release pointer. There is no "v0.5.3 relay release" to move to. The only place v0.5.3-era code exists is the rolling `:main` tag. A production push to that digest would ship unreleased, untested code to 49 real users because a changelog entry implied "you're behind."

Claude Opus 4.8 stopped the production push it had just started planning and reported back plainly. The real decision (stay on stable, or deliberately ride `:main` behind the wrapped updater) became a tracked, owner-gated call instead.

## Why Not Just Match the Version?

The obvious move is to read the version number and bump the relay to match. This fails when the container is built from the same source but distributed completely differently.

The Buzz relay and desktop app share the codebase but diverge at distribution:

- Desktop: real semver releases via Tauri auto-update. v0.5.3 is a real, auditable release.
- Relay: rolling container tags with no semver. The changelog is metadata about the codebase. The container distribution is about the tags.

A version string in a changelog does not guarantee that version exists as a container release tag. The relay's `:latest` tag already carried v0.5.3-era code, built and published to GHCR, without ever gaining a v0.5.3 release tag of its own. Version numbers are metadata. Registry digests are facts.

The only reliable signal is the digest. Resolve it. Compare it.

## How to Check This Yourself

**How do you know if your self-hosted server actually has the version a vendor announced?** Not by reading the release notes. Resolve the artifact your server is actually running (a registry digest, a resolved package version, a build hash) and compare that against what the vendor's registry currently publishes for the same channel. The version string in a changelog is not that artifact.

The pattern generalizes past Buzz. Any time a vendor's release notes describe a product with more than one distribution channel (a desktop app plus a self-hosted server, a CLI plus a hosted API, a library plus a Docker image), the version string is only trustworthy for the channel it was written about.

Before matching a version number across channels, resolve what each channel is actually running:

- **Container image:** compare the `Docker-Content-Digest` header from the registry against `docker inspect --format='{{index .RepoDigests 0}}'` on the running container. Not the tag. The digest.
- **npm/PyPI package:** compare the published `dist-tags.latest` against the installed `package.json`/`requirements.txt` resolved version, not against a changelog entry that may describe a different distribution target (CLI vs library).
- **Any rolling tag** (`:latest`, `:main`, `:stable`): treat the tag name as a pointer, not a version. Pointers move. Resolve them to the thing they point at before deciding anything is "behind."

If there's no way to resolve a pinned, reproducible identifier for what's actually running, that's the real finding, independent of whatever the changelog says.

## The Same Day: Two More Labels That Lied

**Twenty CRM SMTP cutover.** The same session repointed Twenty (the last app still sending mail via smtp.gmail.com) to MXroute, and hit the same class of mistake from a different angle. `docker restart twenty-server twenty-worker` reported both containers as running, but running is not the same as running with the new config: `docker restart` does not re-read `.env`, it just restarts the existing container with whatever environment was baked in at creation. Twenty went to 502. The fix was `docker compose up -d`, which recreates the containers so they actually pick up the new `.env`. Recreating both at once then failed the worker's dependency check before the server's health check cleared, and one log line, "Nest application successfully started" on the unchanged pinned image, was what told a slow-boot window apart from a real break. Waited it out, started the worker separately, recovered to 200 within minutes. A status label ("restarted", "up") described the container's process state, not whether it had the change that mattered.

**MiniMax code-review billing lock.** GPT-5.6 Sol opened PR #305 and expected the MiniMax automated code-review GitHub Action to fire. It did not, and the visible label was "workflow disabled." That label was true but incomplete. Checking repo secrets and variables ruled out config. The run logs held the real answer: "recent account payments have failed or your spending limit needs to be increased." A GitHub Actions billing lock, upstream of the workflow, upstream of the self-hosted runner that Jeremy asked about next. GitHub gates the job before it ever reaches runner selection, so switching to an offline runner would not have helped. This stays parked until the GitHub Actions billing itself is fixed.

## Also Shipped

The estate migration off direct Slack webhooks onto the self-hosted governed Buzz relay continued. Claude-code-plugins retired its direct-Slack npm-digest workflow the same day intent-os stood up the Buzz-routed replacement, and iam-bob-intendant shipped the new repository-owned Buzz command transport (PR #14, v0.0.8) that other repos can consume without each one wiring Slack webhooks directly.

Diagnostic-pro shipped evidence-attachment authorization on work-order and document routes, plus a photo-upload handoff clarification on the frontend.

A session handoff document was written at end of day. A second AI, GPT-5.6 Sol, reviewed it cold and caught real defects in it: a mailbox-roster count that did not match the governing tracking issue, a missing doc-index entry, and internally contradictory status language. A handoff doc written by the same session that did the work is not automatically trustworthy.

## Why This Matters

Three labels lied the same day, each in its own layer: a changelog entry implied the relay was behind when the registry digest showed it was current; a "restarted" container implied it was running the new config when it was running the old one; a "workflow disabled" status implied a config problem when the real gate was a billing lock two layers up. None of these were caught by reading the label. All three were caught by resolving the actual state underneath it: a registry digest, a container log line, a run log's rejection message. Intent Solutions runs its own production infrastructure precisely so that "the label says X" is never the last word. Decision D139 exists for the same reason: an unreviewed image must never auto-promote onto a live system just because a version string implied it should. Resolve the artifact. Act on the facts underneath the label.

---

## Related Posts

- [The Ghost in the Catalog](https://startaitools.com/posts/the-ghost-in-the-catalog/) covers another case where system metadata and runtime reality diverged.
- [The Drills Passed, Reality Did Not](https://startaitools.com/posts/the-drills-passed-reality-did-not/) covers the day the Buzz relay's wrapped update lane referenced above was first built, and three separate hermetic test drills that passed while the real system failed.
- [Do Not Blindly Restart](https://startaitools.com/posts/do-not-blindly-restart/) covers the same class of lying label from an earlier week: a notification script that reported success unconditionally, whether or not anything actually sent.
