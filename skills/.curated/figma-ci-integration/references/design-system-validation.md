# Step 3: Design System Validation

Deep-dive reference for the `figma-ci-integration` skill — extracted from the 'Step 3: Design System Validation' step of the workflow.

```yaml
      - name: Validate design tokens
        run: |
          # Check that all CSS custom properties are valid
          node -e "
            const fs = require('fs');
            const css = fs.readFileSync('src/styles/tokens.css', 'utf-8');
            const vars = css.match(/--[\w-]+:/g) || [];
            console.log('Token count:', vars.length);
            if (vars.length < 10) {
              console.error('Too few tokens extracted -- possible Figma API error');
              process.exit(1);
            }
            // Check for duplicate variable names
            const dupes = vars.filter((v, i) => vars.indexOf(v) !== i);
            if (dupes.length > 0) {
              console.error('Duplicate tokens:', dupes);
              process.exit(1);
            }
          "
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
