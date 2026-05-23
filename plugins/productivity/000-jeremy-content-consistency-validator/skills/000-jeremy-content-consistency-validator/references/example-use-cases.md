# Example Use Cases

## Example Use Cases

### Use Case 1: Version Consistency Check

**Trigger:** "Check if all docs mention the same version number"

**Result:**

```
Version Analysis Report
Website: v1.2.1 (5 mentions)
GitHub: v1.2.1 (3 mentions), v1.2.0 (2 mentions) ⚠️
Local Docs: v1.2.0 (8 mentions) 🔴

Action: Update Local Docs to v1.2.1
```

### Use Case 2: Feature Claim Validation

**Trigger:** "Validate that all platforms claim the same features"

**Result:**

```
Feature Consistency Analysis
"236 plugins": Website ✅, GitHub ✅, Docs ❌ (says "230+")
"Agent Skills": Website ✅, GitHub ✅, Docs ✅
"MCP Support": Website ✅, GitHub ✅, Docs ⚠️ (unclear mention)

Action: Update Docs to specify "236 plugins" and clarify MCP support
```

### Use Case 3: Pre-Training Update

**Trigger:** "Before I update training materials, what's changed on the website?"

**Result:**

```
Website Changes Since Last Training Update (Oct 15)
- New feature added: "Skill Enhancers" (not in training)
- Pricing updated: $39/mo → $49/mo (not in training)
- Contact form URL changed (broken link in training)

Suggested Training Updates:
1. Add Skill Enhancers section
2. Update pricing screenshots
3. Fix contact form URL
```
