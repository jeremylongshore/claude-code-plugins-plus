# Current-state boundary

This skill joins three deliberately different evidence classes:

1. `DATA_CLASSIFICATION_LATEST` is Account Usage observation and can lag by up to
   three hours. It never proves immediate classification state.
2. `POLICY_REFERENCES`, `TAG_REFERENCES`, and
   `TAG_REFERENCES_ALL_COLUMNS` are selector-bound current observations but can be
   filtered by privileges.
3. `POLICY_CONTEXT` is an operator-executed, role/context-dependent simulation.
   It is not executed by the shared collector and does not prove every query path.

The owner-approved policy supplies the independent denominator. A separately
trusted scope receipt supplies privilege reconciliation. No result is positive
without both. Even a clean result is named `BOUNDED_COVERAGE_OBSERVED`, with
`pass_supported: false` and the provider-latency and simulation non-claims intact.
