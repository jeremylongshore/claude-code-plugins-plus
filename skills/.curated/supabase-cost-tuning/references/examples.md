# Examples — Cost Checks and Estimation

Worked scripts referenced from the skill's Examples section.

## Quick cost check for a growing project

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

// Check database size against plan limit
const { data: dbSize } = await supabase.rpc('get_db_size')
// CREATE FUNCTION get_db_size() RETURNS text AS $$
//   SELECT pg_size_pretty(pg_database_size(current_database()));
// $$ LANGUAGE sql;

console.log(`Database size: ${dbSize}`)

// Check if you're approaching storage limits
const { data: buckets } = await supabase.storage.listBuckets()
console.log(`Storage buckets: ${buckets?.length ?? 0}`)
```

## Monthly cost estimation script

```typescript
function estimateMonthlyCost(usage: {
  dbSizeGb: number
  storageGb: number
  bandwidthGb: number
  edgeFnInvocations: number
  mau: number
}) {
  const pro = {
    base: 25,
    dbOverage: Math.max(0, usage.dbSizeGb - 8) * 0.125,
    storageOverage: Math.max(0, usage.storageGb - 100) * 0.021,
    bandwidthOverage: Math.max(0, usage.bandwidthGb - 250) * 0.09,
    edgeFnOverage: Math.max(0, usage.edgeFnInvocations - 2_000_000) / 1_000_000 * 2,
  }

  const total = pro.base + pro.dbOverage + pro.storageOverage
    + pro.bandwidthOverage + pro.edgeFnOverage

  console.log('Estimated monthly cost breakdown:')
  console.log(`  Base Pro plan:     $${pro.base}`)
  console.log(`  DB overage:        $${pro.dbOverage.toFixed(2)}`)
  console.log(`  Storage overage:   $${pro.storageOverage.toFixed(2)}`)
  console.log(`  Bandwidth overage: $${pro.bandwidthOverage.toFixed(2)}`)
  console.log(`  Edge Fn overage:   $${pro.edgeFnOverage.toFixed(2)}`)
  console.log(`  TOTAL:             $${total.toFixed(2)}/mo`)

  return total
}

// Example: project with 12GB DB, 150GB storage, 300GB bandwidth
estimateMonthlyCost({
  dbSizeGb: 12,
  storageGb: 150,
  bandwidthGb: 300,
  edgeFnInvocations: 1_500_000,
  mau: 80_000,
})
// Base Pro plan:     $25
// DB overage:        $0.50
// Storage overage:   $1.05
// Bandwidth overage: $4.50
// Edge Fn overage:   $0.00
// TOTAL:             $31.05/mo
```
