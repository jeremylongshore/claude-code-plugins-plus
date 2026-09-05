# Databricks production benchmark for Grammarly v2

The Databricks v2 rebuild establishes the repository's practical quality bar:

- consolidate broad product tutorials into a small set of distinct operator pains;
- put deterministic validation and transformations in tested scripts;
- keep deep contracts in progressively loaded references;
- use dry-run or advisory behavior when live authority is absent;
- produce bounded reports and receipts with redaction, evidence, and rollback rules;
- hand-author eval specifications with positive, negative, edge, and adversarial cases;
- add hooks or MCP servers only when they solve a real runtime problem.

Grammarly does not need a custom MCP server or shell hooks. Its public surface is small,
the primary workflow is HTTP document submission, and four of the five new workflows
can be safer as offline analyzers. Adding runtime infrastructure would increase attack
surface without increasing verified capability.

The resulting five pains are access readiness, document evaluation, job reliability,
content-transfer safety, and license governance. The count follows distinct operator
outcomes rather than a marketplace tier quota.

Evidence anchors: Databricks pack `000-docs/006-RL-RSRC-databricks-v2-rebuild-synthesis.md`,
`000-docs/007-AT-ADEC-databricks-v2-cto-decision.md`, its five skill trees, focused
Python tests, and adversarial `eval-spec.yaml` files as inspected on 2026-09-04.
