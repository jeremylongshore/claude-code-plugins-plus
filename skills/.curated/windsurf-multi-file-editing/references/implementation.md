# Implementation Guide

1. **Scope the Operation**
   - Identify all affected files using search/grep
   - Map file dependencies and import relationships
   - Plan change order based on dependencies

2. **Configure Operation Template**
   - Select appropriate template (rename, move, extract)
   - Define find/replace patterns or transformations
   - Set file scope and exclusion rules

3. **Generate Preview**
   - Run Cascade analysis on affected files
   - Review all proposed modifications
   - Verify no unintended changes

4. **Execute with Preview**
   - Apply changes atomically across all files
   - Cascade validates syntax after each change
   - Monitor progress in edit-history.json

5. **Verify Results**
   - Run syntax checks on modified files
   - Execute test suite to catch regressions
   - Validate all references resolve correctly

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
