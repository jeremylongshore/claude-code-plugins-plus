# Common Freshie Queries

Pre-built SQLite queries for the freshie inventory database. All queries filter to the latest
discovery run unless comparing across runs.

## Table of Contents

- [Grade & Compliance](#grade--compliance)
- [Stub Detection](#stub-detection)
- [Plugin Analysis](#plugin-analysis)
- [Pack Coverage](#pack-coverage)
- [Content Quality](#content-quality)
- [Historical Trends](#historical-trends)
- [Anomalies & Data Quality](#anomalies--data-quality)
- [Field Analysis](#field-analysis)
- [Cross-References](#cross-references)

## Grade & Compliance

### Grade Distribution (Latest Run)

```sql
SELECT grade, COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM skill_compliance WHERE run_id=(SELECT MAX(id) FROM discovery_runs)), 1) as pct
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY grade ORDER BY grade;
```

### Average Score by Category

```sql
SELECT p.category, ROUND(AVG(sc.score), 1) as avg_score, COUNT(*) as skill_count
FROM skill_compliance sc
JOIN skills s ON sc.skill_path = s.path AND sc.run_id = s.run_id
JOIN plugins p ON s.plugin_path = p.path AND s.run_id = p.run_id
WHERE sc.run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY p.category
ORDER BY avg_score DESC;
```

### Low-Grade Skills (D and F)

```sql
SELECT skill_path, score, grade, error_count, warning_count, missing_fields
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND grade IN ('D', 'F')
ORDER BY score ASC;
```

### Skills Just Below A Grade (Upgrade Candidates)

```sql
SELECT skill_path, score, grade, missing_fields
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND score BETWEEN 80 AND 89
ORDER BY score DESC;
```

### Skills with Most Errors

```sql
SELECT skill_path, error_count, warning_count, score, grade
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND error_count > 0
ORDER BY error_count DESC LIMIT 20;
```

## Stub Detection

### All Stub Skills

```sql
SELECT skill_path, score, grade, stub_reasons
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND is_stub = 1
ORDER BY skill_path;
```

### Stub Rate by Category

```sql
SELECT p.category,
  COUNT(*) as total,
  SUM(sc.is_stub) as stubs,
  ROUND(SUM(sc.is_stub) * 100.0 / COUNT(*), 1) as stub_pct
FROM skill_compliance sc
JOIN skills s ON sc.skill_path = s.path AND sc.run_id = s.run_id
JOIN plugins p ON s.plugin_path = p.path AND s.run_id = p.run_id
WHERE sc.run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY p.category
ORDER BY stub_pct DESC;
```

### Non-Stub Skills Scoring Below 70

```sql
SELECT skill_path, score, grade, error_count
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND is_stub = 0 AND score < 70
ORDER BY score ASC;
```

## Plugin Analysis

### Plugin Count by Category

```sql
SELECT category, COUNT(*) as count
FROM plugins
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY category
ORDER BY count DESC;
```

### Plugins Missing Required Companions

```sql
SELECT p.name, p.category,
  GROUP_CONCAT(pc.companion_type) as missing
FROM plugins p
LEFT JOIN plugin_companions pc ON p.path = pc.plugin_path AND p.run_id = pc.run_id
WHERE p.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND pc.exists = 0
GROUP BY p.name
ORDER BY p.category, p.name;
```

### Plugin Compliance Roll-Up

```sql
SELECT p.name, p.category, pc.score, pc.grade
FROM plugin_compliance pc
JOIN plugins p ON pc.plugin_path = p.path AND pc.run_id = p.run_id
WHERE pc.run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY pc.score ASC LIMIT 20;
```

### Plugins with No Skills

```sql
SELECT p.name, p.category, p.path
FROM plugins p
LEFT JOIN skills s ON p.path = s.plugin_path AND p.run_id = s.run_id
WHERE p.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND s.name IS NULL
ORDER BY p.category, p.name;
```

## Pack Coverage

### Pack Skill Counts

```sql
SELECT name, skill_count, category
FROM packs
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY skill_count DESC;
```

### Packs Below Minimum Viable (< 3 Skills)

```sql
SELECT name, skill_count
FROM packs
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND skill_count < 3
ORDER BY skill_count ASC;
```

### Pack Aggregate Metrics

```sql
SELECT pa.pack_name, pa.total_skills, pa.avg_score, pa.min_score, pa.max_score
FROM pack_aggregates pa
WHERE pa.run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY pa.avg_score ASC;
```

## Content Quality

### Lowest Word Count Skills

```sql
SELECT cs.skill_path, cs.word_count, sc.grade, sc.is_stub
FROM content_signals cs
JOIN skill_compliance sc ON cs.skill_path = sc.skill_path AND cs.run_id = sc.run_id
WHERE cs.run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY cs.word_count ASC LIMIT 20;
```

### High Placeholder Density (Likely Templated)

```sql
SELECT cs.skill_path, cs.placeholder_density, cs.word_count, sc.grade
FROM content_signals cs
JOIN skill_compliance sc ON cs.skill_path = sc.skill_path AND cs.run_id = sc.run_id
WHERE cs.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND cs.placeholder_density > 0.1
ORDER BY cs.placeholder_density DESC LIMIT 20;
```

### Skills with Most Code Blocks

```sql
SELECT cs.skill_path, cs.code_block_count, cs.word_count, sc.grade
FROM content_signals cs
JOIN skill_compliance sc ON cs.skill_path = sc.skill_path AND cs.run_id = sc.run_id
WHERE cs.run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY cs.code_block_count DESC LIMIT 20;
```

## Historical Trends

### All Discovery Runs

```sql
SELECT id, run_date, commit_hash, total_plugins, total_skills, total_packs, total_files
FROM discovery_runs ORDER BY id;
```

### Grade Trend Across Runs

```sql
SELECT sc.run_id, sc.grade, COUNT(*) as count
FROM skill_compliance sc
GROUP BY sc.run_id, sc.grade
ORDER BY sc.run_id, sc.grade;
```

### Skills That Changed Grade Between Runs

```sql
SELECT old.skill_path,
  old.grade as old_grade, old.score as old_score,
  new.grade as new_grade, new.score as new_score,
  new.score - old.score as delta
FROM skill_compliance old
JOIN skill_compliance new ON old.skill_path = new.skill_path
WHERE old.run_id = (SELECT MAX(id) - 1 FROM discovery_runs)
  AND new.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND old.grade != new.grade
ORDER BY delta DESC;
```

### New Skills Since Previous Run

```sql
SELECT new.skill_path, new.grade, new.score
FROM skill_compliance new
LEFT JOIN skill_compliance old ON new.skill_path = old.skill_path
  AND old.run_id = (SELECT MAX(id) - 1 FROM discovery_runs)
WHERE new.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND old.skill_path IS NULL
ORDER BY new.score DESC;
```

### Removed Skills Since Previous Run

```sql
SELECT old.skill_path, old.grade, old.score
FROM skill_compliance old
LEFT JOIN skill_compliance new ON old.skill_path = new.skill_path
  AND new.run_id = (SELECT MAX(id) FROM discovery_runs)
WHERE old.run_id = (SELECT MAX(id) - 1 FROM discovery_runs)
  AND new.skill_path IS NULL
ORDER BY old.skill_path;
```

## Anomalies & Data Quality

### All Anomalies (Latest Run)

```sql
SELECT * FROM anomalies
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY rowid;
```

### Duplicate File Detection

```sql
SELECT filename, COUNT(*) as occurrences
FROM duplicate_files
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY filename
HAVING COUNT(*) > 1
ORDER BY occurrences DESC LIMIT 20;
```

### Skills with References Directory

```sql
SELECT skill_path, has_references_dir, has_scripts_dir, has_examples
FROM skill_compliance
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
  AND has_references_dir = 1
ORDER BY skill_path;
```

## Field Analysis

### Most Common Frontmatter Fields

```sql
SELECT field_name, COUNT(*) as usage_count
FROM frontmatter_fields
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY field_name
ORDER BY usage_count DESC;
```

### Agent Compliance Issues

```sql
SELECT ac.agent_path, ac.invalid_fields, ac.missing_fields
FROM agent_compliance ac
WHERE ac.run_id = (SELECT MAX(id) FROM discovery_runs)
  AND (ac.invalid_fields IS NOT NULL OR ac.missing_fields IS NOT NULL)
ORDER BY ac.agent_path;
```

## Cross-References

### Skill-to-Plugin Mapping

```sql
SELECT s.name as skill, p.name as plugin, p.category, sc.grade
FROM skills s
JOIN plugins p ON s.plugin_path = p.path AND s.run_id = p.run_id
JOIN skill_compliance sc ON sc.skill_path = s.path AND sc.run_id = s.run_id
WHERE s.run_id = (SELECT MAX(id) FROM discovery_runs)
ORDER BY p.category, p.name, s.name;
```

### Validators Used

```sql
SELECT validator_name, COUNT(*) as checks_run
FROM validator_checks
WHERE run_id = (SELECT MAX(id) FROM discovery_runs)
GROUP BY validator_name
ORDER BY checks_run DESC;
```
