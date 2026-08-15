# 731-BL-LICN — E7.13 AGPL and Consent Remediation Packet

**Filed:** 2026-08-14  
**Bead:** `claude-s03q.2` — E7.13 — AGPL/consent remediation packet  
**Parent:** `claude-s03q` — Epic 7 — Provenance and publication containment  
**Status:** Owner decision required; documentation PR pending; no external mutation performed

## Scope and method

This is a decision packet, not authorization to publish, deprecate, unpublish, contact, or alter any external system. Scope is the 58 live `@intentsolutionsio/*` package manifests identified by machine-readable `plugins/**/.source.json` provenance on main `be8dd2e19b76dd1b22a4151694320ea7eb0395f2`. npm metadata was read from the public registry; upstream identity and license metadata were compared with the recorded source repository and GitHub API. No written consent record was found in repository evidence; that absence is not proof that no private agreement exists.

Evidence commands:

```bash
find plugins -type f -name .source.json
npm view @intentsolutionsio/<name>@<version> time --json
npm view @intentsolutionsio/<name>@<version> dist.tarball --json
gh api repos/<upstream-repo> --jq '.license.spdx_id // "NOASSERTION"'
jq '.plugins | length' .claude-plugin/marketplace.json
jq '.plugins | length' marketplace/public/downloads/manifest.json
```

### Reconciled populations

The following command-backed measurement was rerun against current `origin/main` `be8dd2e19b76dd1b22a4151694320ea7eb0395f2`:

```bash
node scripts/check-mirror-packages-private.mjs
find plugins -type f -name .source.json | wc -l
jq '[.plugins[] | select(.name | startswith("@intentsolutionsio/"))] | length' .claude-plugin/marketplace.json
```

Results: 63 provenance-marked package directories; 63 contain `package.json`; 63 carry `"private": true`; 58 are live `@intentsolutionsio/*` npm packages; 52 of those are clearly third-party; Skyvern is one additional clearly third-party package and the AGPL defect; 5 are first-party/ownership-ambiguous. Thus the current clearly third-party total is **53 including Skyvern**, not 52. The five repository mirrors outside the scoped npm inventory are `hyperflow`, `claude-channel-slack`, `cli-power-skills`, `pr-to-spec`, and `x-bug-triage-plugin`. The historical 55 count grouped `brand-forge` and `content-multiplier` as third-party; their `localplugins/plugins` provenance does not establish external ownership, so both are now ambiguous. No count above is interchangeable with another cohort.

The author field is attribution, not consent. A copyright license such as MIT or Apache-2.0 permits only the acts it grants; it does not establish endorsement, trademark permission, consent to use Intent Solutions' package identity, or approval to publish under this npm scope.

## A. AGPL artifact: `@intentsolutionsio/skyvern@0.1.5`

- Publication: `2026-06-18T01:49:03.906Z`; [npm tarball](https://registry.npmjs.org/@intentsolutionsio/skyvern/-/skyvern-0.1.5.tgz).
- Upstream: [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern), path `skyvern/cli/skills/skyvern`, branch `main`; marker last sync `2026-07-13T17:26:54.366Z`. The marker does not record a resolved commit. The latest path commit returned before that sync by `gh api repos/Skyvern-AI/skyvern/commits?path=skyvern/cli/skills/skyvern&until=2026-07-13T17:26:54Z` was `85f15450fd673433a23abcd172a6730fb0dd72d9`; it is not asserted as the resolved snapshot.
- License: `AGPL-3.0` in `.source.json`, package.json, and GitHub repository metadata.
- Exact inspection: `npm view ... dist.tarball`; `curl -fsSL <tarball> -o /tmp/skyvern-0.1.5.tgz`; `tar -tzf /tmp/skyvern-0.1.5.tgz`; `tar -xOzf ... package/package.json`. The tarball contained only `package.json`, `.claude-plugin/plugin.json`, and `README.md`; no `LICENSE`, `COPYING`, or `NOTICE`.
- Identity/channels: Intent Solutions owns the npm name/scope; the repository mirror is `plugins/productivity/skyvern`; it is in the root index, website data, and cowork/download manifest.
- PR #1187 containment makes the manifest private and adds a tree-wide invariant, protecting the repository's current package boundary. It does not yet provide the independent `.source.json` exclusion inside both publishing workflows; that is E7.2. It does not repair the existing tarball, add license text, establish consent, change npm history, or resolve ownership.

Recommended sequence: (1) prepare a corrected package with complete license and attribution; (2) independently verify its tarball; (3) publish only after owner authorization; (4) deprecate `0.1.5` accurately; (5) determine unpublish eligibility without assuming it; (6) preserve a signed correction record. None was performed.

## B. Third-party publication and consent inventory

Disposition rules follow blueprint 727’s hierarchy: retain only with documented consent and corrected attribution; otherwise quarantine pending consent; investigate ownership where provenance is first-party/ambiguous; require legal review where primary license evidence is unresolved or the AGPL defect exists. Current public versions remain unchanged.

| Package                                              | Version | Upstream owner/repo                   | License: package / marker / primary metadata | Published                | Classification        | Recommended disposition    | Channels         |
| ---------------------------------------------------- | ------: | ------------------------------------- | -------------------------------------------- | ------------------------ | --------------------- | -------------------------- | ---------------- |
| `@intentsolutionsio/aomi`                            |  1.0.10 | aomi-labs/skills                      | MIT / MIT / MIT                              | 2026-06-18T01:47:20.183Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/box-cloud-filesystem`            |   1.0.3 | jeremylongshore/box-cloud-filesystem  | MIT / MIT / MIT                              | 2026-06-18T01:48:21.983Z | first-party/ambiguous | investigate ownership      | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/brand-forge`                     |   0.5.1 | localplugins/plugins                  | MIT / MIT / MIT                              | 2026-07-13T17:57:25.726Z | first-party/ambiguous | investigate ownership      | R,N,I,C          |
| `@intentsolutionsio/claude-workflow-skills`          |   1.5.8 | ali5ter/claude-workflow-skills        | MIT / MIT / MIT                              | 2026-06-18T01:48:28.944Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/claudebase`                      |  0.2.11 | rohithzr/claudebase                   | MIT / MIT / MIT                              | 2026-06-18T01:48:35.928Z | third-party           | quarantine pending consent | R,N,I,Wc,Wu,C    |
| `@intentsolutionsio/cli-ux-tester`                   |   3.1.4 | ali5ter/claude-cli-ux-skill           | MIT / MIT / MIT                              | 2026-06-19T00:27:13.740Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/content-multiplier`              |   0.2.1 | localplugins/plugins                  | MIT / MIT / MIT                              | 2026-07-13T17:57:36.928Z | first-party/ambiguous | investigate ownership      | R,N,I,C          |
| `@intentsolutionsio/dolt-mcp-vcs`                    |   0.1.0 | jeremylongshore/dolt-mcp-vcs-plugin   | Apache-2.0 / Apache-2.0 / Apache-2.0         | 2026-06-30T01:07:44.332Z | first-party/ambiguous | investigate ownership      | R,N,I            |
| `@intentsolutionsio/ejentum-anti-deception`          |   0.1.5 | ejentum/ejentum-mcp                   | MIT / MIT / MIT                              | 2026-06-18T01:46:35.704Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/ejentum-code`                    |   0.1.5 | ejentum/ejentum-mcp                   | MIT / MIT / MIT                              | 2026-06-18T01:46:43.075Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/ejentum-memory`                  |   0.1.5 | ejentum/ejentum-mcp                   | MIT / MIT / MIT                              | 2026-06-18T01:46:50.612Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/ejentum-reasoning`               |   0.1.5 | ejentum/ejentum-mcp                   | MIT / MIT / MIT                              | 2026-06-18T01:46:58.231Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/gastown`                         |   1.0.2 | numman-ali/n-skills                   | Apache-2.0 / Apache-2.0 / Apache-2.0         | 2026-06-18T01:47:05.967Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/governed-second-brain`           |   0.1.7 | jeremylongshore/bobs-big-brain-plugin | Apache-2.0 / Apache-2.0 / Apache-2.0         | 2026-07-16T06:55:56.097Z | first-party/ambiguous | investigate ownership      | R,N,I            |
| `@intentsolutionsio/hermes-tweet`                    |   0.1.6 | Xquik-dev/hermes-tweet                | MIT / MIT / MIT                              | 2026-07-01T15:37:30.210Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/kobiton-automate`                |   1.0.6 | kobiton/automate                      | MIT / MIT / MIT                              | 2026-06-18T01:49:40.422Z | third-party           | quarantine pending consent | R,N,I,Wc,Wu,C    |
| `@intentsolutionsio/llm-box`                         |   0.3.0 | alib8b8/llm-box                       | MIT / MIT / NOASSERTION                      | 2026-07-08T01:20:20.608Z | third-party           | legal review required      | R,N,I,C          |
| `@intentsolutionsio/mnemos`                          |   0.9.0 | polyxmedia/mnemos                     | MIT / MIT / MIT                              | 2026-07-08T01:20:27.990Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/obsidian-project-documentation`  |  3.2.11 | ali5ter/obsidian-project-assistant    | MIT / MIT / MIT                              | 2026-06-19T00:25:48.484Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/over-50s-health`                 |  3.2.10 | ali5ter/over-50s-health-advisor       | MIT / MIT / MIT                              | 2026-06-19T00:25:55.361Z | third-party           | quarantine pending consent | R,N,I,Wc,Wu,C    |
| `@intentsolutionsio/pair-programmer`                 |  1.0.11 | ali5ter/pair-programmer               | MIT / MIT / MIT                              | 2026-06-19T00:26:09.561Z | third-party           | quarantine pending consent | R,N,I,Wc,Wu,C    |
| `@intentsolutionsio/portaljs`                        |   0.1.0 | datopian/portaljs                     | MIT / MIT / MIT                              | 2026-07-08T01:20:35.225Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/publishing-skills`               |   0.1.0 | AutomateLab-tech/publishing-skills    | MIT-0 / MIT-0 / MIT-0                        | 2026-06-25T06:22:53.399Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/quit-sponsor`                    |   0.1.0 | metrox-eth/quit-sponsor               | MIT / MIT / MIT                              | 2026-07-13T17:56:57.577Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/schedule-after-usage-reset`      |   1.0.1 | lemondepat/schedule-after-usage-reset | MIT / MIT / 404/unknown                      | 2026-07-07T23:16:27.147Z | third-party           | legal review required      | R,N,I,Wc,C       |
| `@intentsolutionsio/servicegraph`                    |   0.2.1 | nostrband/ServiceGraph                | MIT / MIT / MIT                              | 2026-07-07T23:16:18.717Z | third-party           | quarantine pending consent | R,N,I,Wc         |
| `@intentsolutionsio/skills-janitor`                  |   0.1.0 | khendzel/skills-janitor               | MIT / MIT / MIT                              | 2026-07-13T17:57:08.958Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/skyvern`                         |   0.1.5 | Skyvern-AI/skyvern                    | AGPL-3.0 / AGPL-3.0 / AGPL-3.0               | 2026-06-18T01:49:03.906Z | AGPL defect           | legal review required      | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/sugar`                           |   2.0.6 | roboticforce/sugar                    | MIT / MIT / NOASSERTION                      | 2026-06-19T00:24:58.121Z | third-party           | legal review required      | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/tonone`                          |  0.9.21 | tonone-ai/tonone                      | MIT / MIT / MIT                              | 2026-06-19T00:21:45.088Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/walkie-talkie`                   |   0.1.0 | walkie-talkie-skill/walkie-talkie     | MIT / MIT / MIT                              | 2026-07-13T17:57:17.363Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/wondelai-blue-ocean-strategy`    |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:44:44.376Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-contagious`             |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:44:51.190Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-cro-methodology`        |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:44:57.986Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-crossing-the-chasm`     |   1.0.4 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:05.123Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-design-everyday-things` |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:47:27.143Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-design-sprint`          |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:49:11.783Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-drive-motivation`       |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:12.332Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-hooked-ux`              |   1.0.3 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:47:33.970Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-hundred-million-offers` |   1.0.3 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:19.309Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-influence-psychology`   |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:26.189Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-ios-hig-design`         |   1.0.4 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:47:40.692Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-jobs-to-be-done`        |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:33.147Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-lean-startup`           |   1.0.3 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:49:19.422Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-made-to-stick`          |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:39.922Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-negotiation`            |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:46.626Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-obviously-awesome`      |   1.0.3 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:45:53.619Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-one-page-marketing`     |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:46:00.455Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-predictable-revenue`    |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:46:07.451Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-refactoring-ui`         |   1.0.4 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:47:47.355Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-scorecard-marketing`    |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:46:14.249Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-storybrand-messaging`   |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:46:21.189Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-top-design`             |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:47:54.295Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-traction-eos`           |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:46:28.391Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-ux-heuristics`          |   1.0.3 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:48:01.244Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/wondelai-web-typography`         |   1.0.2 | wondelai/skills                       | MIT / MIT / MIT                              | 2026-06-18T01:48:08.168Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |
| `@intentsolutionsio/x-twitter-scraper`               |   0.1.0 | Xquik-dev/x-twitter-scraper           | MIT / MIT / MIT                              | 2026-07-01T15:37:18.559Z | third-party           | quarantine pending consent | R,N,I,C          |
| `@intentsolutionsio/zai-cli`                         |   1.0.2 | numman-ali/n-skills                   | Apache-2.0 / Apache-2.0 / Apache-2.0         | 2026-06-18T01:47:13.026Z | third-party           | quarantine pending consent | R,N,I,Wc,Ws,Wu,C |

Every row had no written consent record found in repository evidence. The package author and license metadata are retained attribution signals, not permission. Complete license-text carriage is not inferred from metadata; retain decisions require tarball-level verification. `NOASSERTION`, a 404, missing consent records, and missing repository evidence are unresolved states, not proof of absence.

Primary metadata `NOASSERTION`/404 is not proof of no license, but it blocks a retain recommendation pending evidence. The five ambiguous packages are `box-cloud-filesystem`, `brand-forge`, `content-multiplier`, `dolt-mcp-vcs`, and `governed-second-brain`. The AGPL defect is `skyvern`.

### Tarball-level verification

The exact command used for each selected package was:

```bash
url=$(npm view "$SPEC" dist.tarball --json | jq -r 'if type=="array" then .[0] else . end')
curl -fsSL "$url" -o /tmp/package.tgz
sha256sum /tmp/package.tgz
tar -tzf /tmp/package.tgz
tar -xOzf /tmp/package.tgz package/package.json | jq '{name,version,license}'
```

Required legal rows were inspected: Skyvern (`361157c49c8e47a589fd2768fb021ecbb1e156aaf7899cd199150f49e67a3cb3`, no `LICENSE`, `COPYING`, or `NOTICE`); llm-box (`449b1f1bdbe62f239bf738b6002ad146c0c1ef4388152799e8e56751bdb39acb`, no license file); schedule-after-usage-reset (`fb0767d20f157a0d476ed8d49655991f917d0d7e15d1eb7d82c4fe928d3c709f`, includes `LICENSE`); and sugar (`45bf4ad2c9fd823dd211ea830c6406c9c592b61b21524d0bde1bb56dd4f87146`, includes `LICENSE`). A stratified ordinary-license sample was also checked: aomi MIT with `LICENSE`, gastown Apache-2.0 with `LICENSE`, wondelai-blue-ocean-strategy MIT without a license file, and publishing-skills MIT-0 with `LICENSE`. This sample is not a blanket retention approval; every proposed retention still requires exact tarball evidence.

## C. Channel-specific exposure

| Channel                          |                                 Current evidence | Treatment                                                                                                             |
| -------------------------------- | -----------------------------------------------: | --------------------------------------------------------------------------------------------------------------------- |
| Repository mirror                |                              58 scoped; 63 total | Keep content unchanged; PR #1187's private boundary protects future repository publication.                           |
| npm package                      |                                       58/58 live | No current version changes; deprecation, corrected release, or unpublish requires authorization.                      |
| Tons of Skills marketplace/index |                                            58/58 | Index presence is a separate publication decision.                                                                    |
| Website projections              | 45 catalog / 39 skills catalog / 43 search index | Projections are inconsistent; do not regenerate until owner dispositions are decided.                                 |
| Cowork/download archive          |                                            55/58 | Three scoped packages absent: dolt-mcp-vcs, governed-second-brain, servicegraph. Treat archive as a separate channel. |
| Other generated distribution     |                                  Not established | Inventory separately before action.                                                                                   |

## D. Unsent contributor communication drafts

These are owner-gated and were not sent.

**Consent request**

> Hello <upstream owner>, we found your work mirrored in Tons of Skills and distributed under `@intentsolutionsio/<package>`. Could you confirm whether Intent Solutions may redistribute it through the repository, npm, marketplace/index, website, and download archives? Please confirm preferred attribution and license text for each channel. We will keep it contained while awaiting your decision and preserve contributor credit.

**Corrected attribution notice**

> We identified <project> as the upstream source for `<package>`. We are preparing corrected attribution and license presentation for owner review. No further release, correction, deprecation, or removal action will be taken until the appropriate authorization is recorded; your project name, authorship, license, and upstream link will be preserved as confirmed.

**Deprecation/removal offer**

> We are reviewing whether `<package>` should remain under our npm scope. If you do not authorize that distribution, we can prepare accurate deprecation and replacement/removal options while preserving your credit and linking to the upstream project. Nothing has changed yet.

**Repository-caused delay acknowledgement**

> The delay was caused by repository intake and CI/governance problems, not by your contribution. We are resetting intake review, preserving your credit, and will provide an uncomplicated reopen/resubmit route after owner approval.

## E. Owner decision matrix

| Decision                              | Recommendation                   | Evidence                                  | Acting consequence               | Delay consequence                      | Reversible?                          | Eventual external mutation                    | Authorizer                         |
| ------------------------------------- | -------------------------------- | ----------------------------------------- | -------------------------------- | -------------------------------------- | ------------------------------------ | --------------------------------------------- | ---------------------------------- |
| Skyvern 0.1.5                         | Keep private; prepare correction | AGPL declared; tarball lacks license text | Corrected package work           | Defective version remains discoverable | Containment yes; publish not assumed | Corrected npm publish/deprecation if approved | Owner; counsel for legal questions |
| 52 third-party packages               | Quarantine pending consent       | External provenance; no record found      | Current public history unchanged | Ambiguous exposure continues           | Yes                                  | Consent outreach and channel corrections      | Owner; upstream owner              |
| Five ambiguous packages               | Investigate ownership            | Jeremy/local provenance                   | Establish authorship             | Misclassification risk                 | Yes                                  | Possible metadata/channel correction          | Owner                              |
| Unresolved license metadata           | Legal review required            | Primary API NOASSERTION/404               | Blocks retain decision           | License uncertainty persists           | Yes                                  | Corrected metadata or withdrawal              | Owner; qualified counsel           |
| Marketplace/website/download channels | Preserve pending decisions       | Channel counts differ                     | Avoids scope expansion           | Stale projections remain               | Yes                                  | Regenerate projections/archive                | Owner                              |

No secrets, credentials, token identifiers, or speculative legal conclusions are included.

## Verification and review gate

The focused E7.13 documentation PR must be independently reviewed from a clean checkout. The reviewer must rerun counts/classifications, inspect Skyvern’s tarball and primary license evidence, verify zero registry mutations, zero contributor contact, zero mirror-content edits, correct v4.4 ledger/index entries, and no work outside `claude-s03q.2`.

E7.13 remains open at the owner review gate. No E7.2, additional Epic 7 bead, or other epic was activated.
