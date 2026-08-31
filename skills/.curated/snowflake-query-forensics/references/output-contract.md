# Query forensics output contract

## Header

Record:

- account, role, warehouse, query ID, execution state;
- query hash and parameterized hash when available;
- history surface, source maximum timestamp, and collection time;
- operator-stat and Query Insights availability;
- redaction applied.

## Timeline

Report supplied timing fields without a universal threshold:

```text
total elapsed
compilation
execution
queue overload
queue provisioning
queue repair
transaction blocked
other/unexplained if the supplied fields do not reconcile
```

Do not fabricate zeroes for missing fields.

## Confirmed observations

List raw positive evidence: wait time, spill bytes, operator-time percentage, platform
insight, errors, and other supplied counters. Name the exact source.

## Estimated or derived metrics

List ratios separately:

- output rows / input rows;
- partitions scanned / partitions total;
- before/after change if the comparison inputs are aligned.

Derived does not mean incorrect; it means the value was computed rather than directly
reported.

## At-risk hypotheses

Every hypothesis needs:

- evidence;
- competing explanation;
- next read-only check;
- evidence that would falsify it;
- owner for any later experiment.

## One-variable experiment

If the user wants remediation, propose only one variable at a time. State baseline,
change, fixed inputs, measurement window, success criteria supplied by the user, impact,
approval, and rollback. Do not execute the experiment.

## Required non-claims

- No single metric was treated as a proven root cause.
- No universal performance threshold or SLA was applied.
- No SQL, warehouse, clustering, session, or query state was mutated.
- Raw query text was not required by the evidence contract.

## Good conclusion

> Query `01...` recorded remote spill on operator 7 and spent the largest reported
> operator-time share there. Query-shape and capacity pressure remain competing causes.
> Compare the same parameterized hash over an aligned data window before approving a
> one-variable experiment.

## Bad conclusion

> The warehouse is too small; resize it to Large.

The bad conclusion invents the root cause, target size, and authorization.
