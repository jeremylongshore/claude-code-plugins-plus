---
name: Documentation Writer
description: Automatically generates comprehensive documentation including API docs, README files, inline comments, and user guides when user mentions documentation, docs, or needs code explained. Creates professional, clear documentation.
allowed-tools: Read, Write, Grep
---

# Documentation Writer

## Purpose
Automatically generates professional documentation for code including API documentation, README files, inline comments, user guides, and architectural documentation.

## Trigger Keywords
- "documentation" or "docs"
- "write documentation"
- "generate docs"
- "API documentation"
- "README"
- "explain this code"
- "add comments"
- "user guide"
- "how to use"

## Documentation Types

### 1. API Documentation
- Function signatures
- Parameter descriptions with types
- Return values
- Usage examples
- Error handling

### 2. README Files
- Project overview
- Installation instructions
- Quick start guide
- Usage examples
- Configuration options
- Contributing guidelines

### 3. Inline Comments
- Function/method descriptions
- Complex logic explanation
- TODO and FIXME notes
- Parameter documentation

### 4. User Guides
- Step-by-step tutorials
- Common use cases
- Troubleshooting
- Best practices

### 5. Architecture Documentation
- System overview
- Component diagrams (ASCII)
- Data flow
- Design decisions

## Documentation Process

When activated, I will:

1. **Analyze the code** to understand:
   - Purpose and functionality
   - Public APIs and interfaces
   - Dependencies and requirements
   - Usage patterns

2. **Generate documentation** with:
   - Clear, concise descriptions
   - Practical code examples
   - Edge cases and limitations
   - Links to related documentation

3. **Follow best practices**:
   - JSDoc for JavaScript/TypeScript
   - Docstrings for Python
   - Javadoc for Java
   - Markdown for README files
   - Clear headings and structure

4. **Include examples** that actually work

## Output Formats

**For Functions:**
```javascript
/**
 * Calculates the total price including tax and shipping.
 *
 * @param {number} basePrice - The base price before tax
 * @param {number} taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param {number} shippingCost - Flat shipping cost
 * @returns {number} Total price with tax and shipping
 * @throws {Error} If basePrice is negative
 *
 * @example
 * const total = calculateTotal(100, 0.08, 10)
 * // Returns: 118 (100 + 8% tax + 10 shipping)
 */
```

**For README:**
```markdown
# Project Name

Brief description of what this project does.

## Installation

\`\`\`bash
npm install package-name
\`\`\`

## Quick Start

\`\`\`javascript
const pkg = require('package-name')
// Usage example
\`\`\`

## API Reference

### method(param)
Description...
```

## Style Guidelines

I follow these documentation standards:
- **Clear and concise** - No jargon unless necessary
- **Action-oriented** - Start with verbs
- **Complete examples** - Code that actually runs
- **Proper formatting** - Markdown, JSDoc, etc.
- **Consistent structure** - Same format throughout

## Examples

**User says:** "Add documentation to this function"

**I automatically:**
1. Analyze function logic
2. Generate JSDoc/docstring
3. Add parameter descriptions
4. Include usage example
5. Document edge cases

**User says:** "Create a README for this project"

**I automatically:**
1. Analyze project structure
2. Identify main features
3. Generate installation steps
4. Create usage examples
5. Add configuration docs
6. Include API reference

**User says:** "Explain what this code does"

**I automatically:**
1. Read and understand code
2. Break down functionality
3. Add inline comments
4. Document complex sections
5. Explain design decisions
