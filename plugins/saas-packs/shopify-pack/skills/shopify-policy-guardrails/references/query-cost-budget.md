# Query Cost Budget Enforcement

Static analysis of GraphQL queries to enforce cost budgets at build/test time before they hit Shopify's API.

```typescript
// Enforce query cost budgets at build/test time
interface QueryCostBudget {
  maxFirstParam: number;        // Max items per page
  maxNestedDepth: number;       // Max nested connection depth
  maxEstimatedCost: number;     // Max estimated query cost
}

const BUDGET: QueryCostBudget = {
  maxFirstParam: 100,           // Never request more than 100 items
  maxNestedDepth: 3,            // No more than 3 levels of edges/node
  maxEstimatedCost: 500,        // Stay well under 1,000 point limit
};

function validateQueryCost(query: string): string[] {
  const violations: string[] = [];

  // Check `first:` parameter values
  const firstParams = query.matchAll(/first:\s*(\d+)/g);
  for (const match of firstParams) {
    if (parseInt(match[1]) > BUDGET.maxFirstParam) {
      violations.push(
        `first: ${match[1]} exceeds budget of ${BUDGET.maxFirstParam}`
      );
    }
  }

  // Check nesting depth (count "edges { node {" patterns)
  const depth = (query.match(/edges\s*\{/g) || []).length;
  if (depth > BUDGET.maxNestedDepth) {
    violations.push(
      `Nesting depth ${depth} exceeds budget of ${BUDGET.maxNestedDepth}`
    );
  }

  // Estimate cost: multiply all `first` values along nested path
  const firstValues = [...query.matchAll(/first:\s*(\d+)/g)].map((m) =>
    parseInt(m[1])
  );
  const estimatedCost = firstValues.reduce((a, b) => a * b, 1);
  if (estimatedCost > BUDGET.maxEstimatedCost) {
    violations.push(
      `Estimated cost ${estimatedCost} exceeds budget of ${BUDGET.maxEstimatedCost}`
    );
  }

  return violations;
}
```
