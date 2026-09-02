# Query Insights boundaries

Primary source:

- [Using query insights to improve performance](https://docs.snowflake.com/en/user-guide/query-insights)
- [QUERY_INSIGHTS Account Usage view](https://docs.snowflake.com/en/sql-reference/account-usage/query_insights)

Query Insights is a platform signal, not a complete health verdict. Each returned
insight describes a detected condition and can include a general next step.

## Example insight families

Current official documentation includes signals for conditions such as:

- missing, inapplicable, or unselective filters;
- leading-wildcard filters;
- clustering-key filter observations;
- search-optimization use;
- exploding joins;
- unnecessary aggregation or set distinctness;
- remote spill;
- excessive warehouse queue time.

Keep the platform's exact `TYPE_ID` and sanitized message. Do not replace it with a
home-grown severity threshold.

## Documented exclusions

Official documentation states that insights are not produced for several categories,
including:

- plans that take multiple steps to finish;
- queries involving secure objects;
- hybrid-table queries;
- Native App-generated queries;
- `EXPLAIN` queries;
- result-reuse executions;
- interactive-table queries.

There are also insight-specific limitations. For example, a filter-selectivity insight
is not produced for queries accelerated by Query Acceleration Service.

Therefore, “no insight returned” can mean:

1. no supported condition was detected;
2. the query falls under an exclusion;
3. the insight surface was unavailable or not collected;
4. source timing/visibility prevented the row from appearing.

The report must say which interpretation is supported.

## Use with operator evidence

- A remote-spill insight plus positive remote-spill bytes is corroborating evidence,
  but the cause still requires query-shape/capacity comparison.
- An exploding-join insight plus an output/input multiple identifies the operator to
  inspect, but does not prove the join semantics are wrong.
- A queue insight plus positive queue-overload time confirms waiting, but not the right
  capacity change.
- No insight does not override positive operator or query-history evidence.

## Output shape

For every supplied insight record:

```text
anchor query ID
type ID
sanitized message
query/operator association if returned
documented general recommendation
known exclusion relevant to this query
corroborating history/operator evidence
decision: confirmed condition / hypothesis / inconclusive
```

Never auto-apply the recommendation. Treat it as one input to a reviewable experiment.
