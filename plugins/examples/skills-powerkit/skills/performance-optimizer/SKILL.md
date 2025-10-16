---
name: Performance Optimizer
description: Automatically analyzes code for performance bottlenecks, memory leaks, and optimization opportunities when user mentions performance, optimization, speed, or slow code. Provides actionable optimization strategies.
allowed-tools: Read, Grep
---

# Performance Optimizer

## Purpose
Automatically identifies performance bottlenecks, inefficient algorithms, memory leaks, and optimization opportunities. Provides specific, measurable improvements with benchmarks.

## Trigger Keywords
- "performance" or "optimize"
- "slow" or "speed up"
- "bottleneck"
- "memory leak"
- "improve performance"
- "faster"
- "efficiency"
- "latency"
- "throughput"

## Performance Analysis

### 1. Algorithm Complexity
- Identify O(n²) algorithms that could be O(n) or O(log n)
- Unnecessary nested loops
- Inefficient search/sort algorithms
- Recursive functions without memoization

### 2. Memory Issues
- Memory leaks (event listeners, closures)
- Unnecessary object creation
- Large data structures in memory
- Missing garbage collection opportunities
- Circular references

### 3. Database Queries
- N+1 query problems
- Missing indexes
- Unoptimized JOINs
- SELECT * instead of specific columns
- Missing query caching

### 4. Network & I/O
- Unnecessary API calls
- Missing response caching
- Inefficient file I/O
- Lack of connection pooling
- No request batching

### 5. Frontend Performance
- Unnecessary re-renders (React)
- Missing virtualization for long lists
- Unoptimized images
- Blocking JavaScript
- Missing code splitting

## Optimization Process

When activated, I will:

1. **Profile the code** to identify:
   - Execution hotspots
   - Time complexity issues
   - Memory usage patterns
   - I/O bottlenecks

2. **Analyze bottlenecks** and calculate:
   - Current performance metrics
   - Expected improvement percentage
   - Optimization priority (high/medium/low)

3. **Provide optimizations** with:
   - Before/after code examples
   - Performance benchmarks
   - Complexity analysis
   - Trade-off considerations

4. **Suggest infrastructure improvements** when applicable

## Output Format

For each optimization:

### Issue Identified
- **Location**: File and line number
- **Problem**: Specific performance issue
- **Impact**: Estimated performance cost
- **Severity**: Critical/High/Medium/Low

### Optimization
- **Strategy**: What to change
- **Code Example**: Before and after
- **Expected Gain**: Performance improvement estimate
- **Complexity**: Old vs new Big-O notation

### Benchmarks
```
Before: 2.5s for 10,000 items (O(n²))
After:  0.15s for 10,000 items (O(n log n))
Improvement: 94% faster
```

## Optimization Examples

### 1. Algorithm Improvement
```javascript
// SLOW: O(n²) - 2.5s for 10k items
const duplicates = arr.filter((item, index) =>
  arr.indexOf(item) !== index
)

// FAST: O(n) - 0.05s for 10k items
const seen = new Set()
const duplicates = arr.filter(item =>
  seen.has(item) ? true : (seen.add(item), false)
)
```

### 2. Database Query Optimization
```javascript
// SLOW: N+1 queries
for (const user of users) {
  user.posts = await db.query('SELECT * FROM posts WHERE user_id = ?', user.id)
}

// FAST: Single query with JOIN
const users = await db.query(`
  SELECT u.*, p.*
  FROM users u
  LEFT JOIN posts p ON p.user_id = u.id
`)
```

### 3. Memoization
```javascript
// SLOW: Recalculates every time
const fibonacci = (n) =>
  n <= 1 ? n : fibonacci(n-1) + fibonacci(n-2)

// FAST: Memoized version
const memo = new Map()
const fibonacci = (n) => {
  if (n <= 1) return n
  if (memo.has(n)) return memo.get(n)
  const result = fibonacci(n-1) + fibonacci(n-2)
  memo.set(n, result)
  return result
}
```

### 4. React Re-render Prevention
```javascript
// SLOW: Re-renders every time parent updates
const ExpensiveComponent = ({ data }) => {
  return <div>{heavyCalculation(data)}</div>
}

// FAST: Memoized with React.memo
const ExpensiveComponent = React.memo(({ data }) => {
  const result = useMemo(() => heavyCalculation(data), [data])
  return <div>{result}</div>
})
```

## Performance Metrics

I provide quantifiable improvements:
- **Execution time** reduction (ms, seconds)
- **Memory usage** reduction (MB, GB)
- **Database queries** reduced (count)
- **API calls** reduced (count)
- **Bundle size** reduction (KB, MB)
- **Time complexity** improvement (Big-O)

## Best Practices

I recommend:
- Lazy loading for large datasets
- Caching strategies (Redis, CDN)
- Database indexing
- Code splitting
- Image optimization
- Debouncing/throttling
- Worker threads for CPU-intensive tasks
- Connection pooling

## Restrictions

- Read-only access (no modifications)
- Static analysis only
- No runtime profiling
- No external tools execution

## Examples

**User says:** "This function is slow, can you optimize it?"

**I automatically:**
1. Analyze function complexity
2. Identify bottlenecks
3. Calculate current Big-O
4. Provide optimized version
5. Show performance improvement

**User says:** "Performance review of the API layer"

**I automatically:**
1. Scan all API endpoints
2. Identify N+1 queries
3. Find missing caching
4. Suggest optimization strategies
5. Prioritize by impact

**User says:** "Memory leak in this component"

**I automatically:**
1. Analyze lifecycle methods
2. Check event listeners
3. Identify closure issues
4. Find circular references
5. Provide leak-free version
