# Third-Party Attribution

## Cocoon-AI / architecture-diagram-generator (MIT)

**Source:** https://github.com/Cocoon-AI/architecture-diagram-generator

Semantic color palette, arrow-masking SVG technique, and grid-background aesthetic are inspired by Cocoon-AI's skill. We do not reuse source code from the upstream repo — we borrow design patterns under the MIT license and credit the originators.

### Borrowed patterns
- Semantic OKLCH color palette by component role (cyan/emerald/violet/amber/rose/orange/slate)
- SVG arrow-masking technique (opaque `#0f172a` rect → styled semi-transparent rect on top)
- Grid-pattern background (40x40 units, stroke `#1e293b`, width `0.5`)
- Dashed boundary conventions for security groups (`4,4` rose) and regions (`8,4` amber, `rx="12"`)
- 40px minimum vertical spacing heuristic for component rows
- JetBrains Mono typography

### Original contributions (not borrowed)
- DCI-grounded topology inference from package manifests, docker-compose, k8s, terraform
- PR-diff delta view (`git diff` → before/after architecture)
- Structural fingerprinting + drift detection
- Stack-trace-to-sequence mode
- Accessibility baseline (ARIA, `<title>`/`<desc>`, reduced-motion)
- Four-command surface
- Mermaid fallback routing

### Upstream MIT license (verbatim)

```
MIT License

Copyright (c) 2025 Cocoon AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
