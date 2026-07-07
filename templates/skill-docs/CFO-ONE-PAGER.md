# <Skill or Plugin Name> — CFO One-Pager

> Required only for enterprise / flagship / paid-tier skills — anywhere money is the
> pitch. If the value story is "saves a developer some keystrokes," skip this document.

_Every number here should survive a skeptical reader. Estimates are fine; label them
as estimates. Delete the italic lines when done._

## The cost of the problem

_What the problem costs today, in dollars or hours. Name the assumption behind the number._

<e.g. "Each manual release audit takes ~3 engineer-hours; a missed finding costs a
patch release (~1 day). Assumption: monthly release cadence.">

## What the skill changes

_The mechanism, one paragraph. What work disappears, what risk shrinks, what becomes possible._

<What changes operationally when this is installed.>

## Impact per run

_Quantify one invocation. Use the rows that apply; delete the rest._

| Dimension     | Per run                                                         |
| ------------- | --------------------------------------------------------------- |
| Time saved    | <e.g. ~2.5 hours vs manual>                                     |
| Risk reduced  | <e.g. catches the 3 failure classes that caused past incidents> |
| Dollars saved | <e.g. ~$400 at a blended $160/hr rate (estimate)>               |

## Adoption cost

_What it takes to start. Honest setup time beats an optimistic one._

| Item          | Cost                               |
| ------------- | ---------------------------------- |
| Setup time    | <e.g. ~15 minutes>                 |
| Prerequisites | <e.g. GitHub CLI authed, Node 20+> |
| Ongoing       | <e.g. none / weekly config review> |

## Risk notes

_What could go wrong and what bounds it — permissions, data exposure, failure modes._

- <Risk 1 and its mitigation>
- <Risk 2 and its mitigation>
