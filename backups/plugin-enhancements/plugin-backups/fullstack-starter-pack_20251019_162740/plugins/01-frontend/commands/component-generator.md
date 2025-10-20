---
description: Generate React components from descriptions with TypeScript and tests
shortcut: cg
category: frontend
difficulty: beginner
estimated_time: 2-5 minutes
---

# Component Generator

Generates production-ready React components from natural language descriptions, including TypeScript types, styling, and tests.

## What This Command Does

**Component Generation:**
-  Creates React component with TypeScript
-  Generates prop types and interfaces
-  Adds basic styling (CSS modules or Tailwind)
-  Creates test file (React Testing Library)
-  Includes JSDoc comments
-  Follows React best practices

**Output:** Complete component with types, styles, and tests

**Time:** 2-5 minutes

---

## Usage

```bash
# Generate component from description
/component-generator "Create a Card component with image, title, description, and action button"

# Shortcut
/cg "Button component with loading state and icon support"

# Specify framework/style
/cg "Modal dialog with animations" --style tailwind --test vitest

# Generate with directory
/cg "UserProfile component" --output src/components/UserProfile
```

---

## Example Output

**Input:**
```
/cg "Create a Button component with variants (primary, secondary, ghost), sizes (sm, md, lg), loading state, and icon support"
```

**Generated Files:**

**Button.tsx:**
```tsx
import { ButtonHTMLAttributes, ReactNode } from 'react'
import styles from './Button.module.css'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button visual variant */
  variant?: 'primary' | 'secondary' | 'ghost'
  /** Button size */
  size?: 'sm' | 'md' | 'lg'
  /** Show loading spinner */
  loading?: boolean
  /** Icon to display before text */
  icon?: ReactNode
  /** Button content */
  children: ReactNode
}

/**
 * Button component with multiple variants and sizes
 *
 * @example
 * ```tsx
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   Click me
 * </Button>
 * ```
 */
export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <span className={styles.spinner} aria-label="Loading" />
      ) : (
        <>
          {icon && <span className={styles.icon}>{icon}</span>}
          {children}
        </>
      )}
    </button>
  )
}
```

**Button.module.css:**
```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Variants */
.primary {
  background: #3b82f6;
  color: white;
}

.primary:hover:not(:disabled) {
  background: #2563eb;
}

.secondary {
  background: #e5e7eb;
  color: #374151;
}

.ghost {
  background: transparent;
  color: #3b82f6;
}

/* Sizes */
.sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.md {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

.lg {
  padding: 1rem 2rem;
  font-size: 1.125rem;
}

.spinner {
  display: inline-block;
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

**Button.test.tsx:**
```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>)

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-busy', 'true')
    expect(button).toBeDisabled()
  })

  it('disables button when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('renders with icon', () => {
    const icon = <span data-testid="icon"></span>
    render(<Button icon={icon}>With Icon</Button>)

    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('applies correct variant classes', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('primary')

    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('secondary')
  })
})
```

---

## Component Templates

### Common Components Generated

**1. Card Component:**
```tsx
<Card
  image="/product.jpg"
  title="Product Name"
  description="Product description"
  action={<Button>Buy Now</Button>}
/>
```

**2. Modal Component:**
```tsx
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
>
  <p>Are you sure?</p>
</Modal>
```

**3. Form Field Component:**
```tsx
<FormField
  label="Email"
  type="email"
  error={errors.email}
  required
/>
```

**4. Dropdown Component:**
```tsx
<Dropdown
  items={options}
  value={selected}
  onChange={handleChange}
  placeholder="Select option"
/>
```

---

## Features

### Accessibility Built-In
- Semantic HTML elements
- ARIA attributes where needed
- Keyboard navigation support
- Focus management
- Screen reader announcements

### TypeScript Support
- Full type definitions
- Prop validation
- IntelliSense support
- Generic types where appropriate

### Testing Included
- Unit tests with React Testing Library
- Accessibility tests
- User interaction tests
- Edge case coverage

### Styling Options
- CSS Modules (default)
- Tailwind CSS
- Styled Components
- Emotion
- Plain CSS

---

## Best Practices Applied

**Component Structure:**
- Single responsibility
- Composable design
- Prop drilling avoided
- Performance optimized (React.memo where beneficial)

**Code Quality:**
- ESLint compliant
- Prettier formatted
- TypeScript strict mode
- JSDoc comments

**Testing:**
- 80%+ code coverage
- User-centric tests (not implementation details)
- Accessibility assertions
- Happy path + edge cases

---

## Related Commands

- `/css-utility-generator` - Generate utility CSS classes
- React Specialist (agent) - React architecture guidance
- UI/UX Expert (agent) - Design review

---

**Generate components in seconds. Ship features faster.** ️
