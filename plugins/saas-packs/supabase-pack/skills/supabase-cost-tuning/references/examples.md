## Examples

### Quick Cost Check

```typescript
// Estimate monthly cost for your usage
const estimate = estimateSupabaseCost(yourMonthlyRequests);
console.log(`Tier: ${estimate.tier}, Cost: $${estimate.estimatedCost}`);
if (estimate.recommendation) {
  console.log(`💡 ${estimate.recommendation}`);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
