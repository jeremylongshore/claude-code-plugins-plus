# Advanced Configuration

## Advanced Configuration

### Context Section

```yaml
context:
  # Key architectural decisions
  architecture: |
    We use a feature-based architecture where each feature
    (auth, products, cart) contains its own components, hooks,
    and API calls. Shared utilities go in lib/.

  # Important patterns
  patterns: |
    - Data fetching: useQuery from @tanstack/react-query
    - Forms: react-hook-form with zod validation
    - State: Zustand for global state
    - API: tRPC for type-safe APIs

  # Things to avoid
  avoid: |
    - Class components
    - Redux (we use Zustand)
    - CSS-in-JS (we use Tailwind)
    - Direct fetch() calls (use our api client)
```

### Examples Section

```yaml
examples:
  component: |
    // Example component structure
    import { useState } from 'react';
    import { Button } from '@/components/ui';

    interface Props {
      title: string;
      onAction: () => void;
    }

    export function MyComponent({ title, onAction }: Props) {
      const [loading, setLoading] = useState(false);

      return (
        <div className="p-4">
          <h2 className="text-lg font-bold">{title}</h2>
          <Button onClick={onAction} loading={loading}>
            Action
          </Button>
        </div>
      );
    }

  api-route: |
    // Example API route
    import { NextRequest, NextResponse } from 'next/server';
    import { z } from 'zod';

    const schema = z.object({
      name: z.string().min(1),
    });

    export async function POST(req: NextRequest) {
      try {
        const body = await req.json();
        const data = schema.parse(body);
        // Process...
        return NextResponse.json({ success: true });
      } catch (error) {
        return NextResponse.json(
          { error: 'Invalid request' },
          { status: 400 }
        );
      }
    }
```

### Testing Section

```yaml
testing:
  framework: vitest
  patterns:
    - Use describe/it blocks
    - Follow AAA pattern (Arrange, Act, Assert)
    - Mock external dependencies
    - Test edge cases and error paths

  example: |
    import { describe, it, expect, vi } from 'vitest';
    import { render, screen } from '@testing-library/react';
    import { MyComponent } from './MyComponent';

    describe('MyComponent', () => {
      it('renders title correctly', () => {
        render(<MyComponent title="Test" onAction={vi.fn()} />);
        expect(screen.getByText('Test')).toBeInTheDocument();
      });

      it('calls onAction when button clicked', async () => {
        const onAction = vi.fn();
        render(<MyComponent title="Test" onAction={onAction} />);
        await userEvent.click(screen.getByRole('button'));
        expect(onAction).toHaveBeenCalled();
      });
    });
```
