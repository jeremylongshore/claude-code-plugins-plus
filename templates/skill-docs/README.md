# Skill submission documents

Fill-in-the-blank templates for the documents every marketplace submission ships with.
These are the single source of truth — external contributors and Intent Solutions' own
skills use the same templates and are held to the same standard. Full process:
[`000-docs/700-DR-GUID-skill-submission-standard.md`](../../000-docs/700-DR-GUID-skill-submission-standard.md).

## Which docs does my submission need?

The bar scales with the tier — a bigger claim carries more paperwork, not a bigger skill.

| Tier                                       | What it covers                                   | Required docs                                                                        |
| ------------------------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **Micro-skill**                            | a single command or skill, no scripts            | `PRD.md` (short form OK)                                                             |
| **Standard plugin**                        | skills plus scripts/commands                     | `PRD.md` + `ADR.md`                                                                  |
| **Pack / flagship / featured / paid-tier** | multi-skill packs, featured picks, anything sold | `PRD.md` + `ADR.md` + `ONE-PAGER.md` (+ `CFO-ONE-PAGER.md` where money is the pitch) |

## The templates

| Template                               | What it proves                                                                    |
| -------------------------------------- | --------------------------------------------------------------------------------- |
| [`PRD.md`](PRD.md)                     | The problem is real, the users exist, success is measurable                       |
| [`ADR.md`](ADR.md)                     | The design was a decision, not an accident — including least-privilege tool scope |
| [`ONE-PAGER.md`](ONE-PAGER.md)         | An installer-in-a-hurry can evaluate it from one screen                           |
| [`CFO-ONE-PAGER.md`](CFO-ONE-PAGER.md) | The money claim survives a skeptical reader (enterprise/flagship/paid only)       |

## How to use them

1. **Open the submission issue first.** The
   [plugin-submission issue template](../../.github/ISSUE_TEMPLATE/plugin-submission.yml)
   captures the PRD-level answers (problem, users, success criteria, top requirements)
   before any code review happens. A PR without a linked submission issue will be asked
   to file one.
2. **Copy the templates your tier requires** into your plugin directory as
   `docs/PRD.md`, `docs/ADR.md`, `docs/ONE-PAGER.md`, `docs/CFO-ONE-PAGER.md`.
3. **Fill them in and delete the italic instruction lines.** Angle-bracket placeholders
   (`<like this>`) mark every blank.
4. **Link the issue from your PR** (`Closes #N` or `Refs #N`) with the docs included.

Each template is deliberately short (under ~80 lines). If your filled-in version is
shorter than the template, that's fine — completeness beats length, same as the rest of
the marketplace bar.
