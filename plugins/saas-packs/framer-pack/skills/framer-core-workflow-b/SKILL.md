---
name: framer-core-workflow-b
description: |
  Execute Framer secondary workflow: Core Workflow B.
  Use when implementing secondary use case,
  or complementing primary workflow.
  Trigger with phrases like "framer secondary workflow",
  "secondary task with framer".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer, components, overrides]
compatible-with: claude-code
---

# Framer Code Components & Overrides

## Overview

Build code components with property controls and code overrides for Framer sites. Components are custom React rendered on the canvas. Overrides modify existing layer behavior (animations, interactions) without changing the component.

## Prerequisites

- Framer project open in editor
- Understanding of React and Framer Motion

## Instructions

### Step 1: Code Component with Property Controls

```tsx
import { addPropertyControls, ControlType } from 'framer';
import { useRef, useEffect, useState } from 'react';

interface Props { target: number; duration: number; suffix: string; fontSize: number; color: string; }

export default function AnimatedCounter({ target = 1000, duration = 2, suffix = '+', fontSize = 48, color = '#000' }: Props) {
  const ref = useRef(null);
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => { if (e.isIntersecting) setStarted(true); }, { threshold: 0.5 });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!started) return;
    const inc = target / (duration * 60);
    let val = 0;
    const timer = setInterval(() => {
      val += inc;
      if (val >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(val));
    }, 1000 / 60);
    return () => clearInterval(timer);
  }, [started, target, duration]);

  return <div ref={ref} style={{ fontSize, fontWeight: 700, color, textAlign: 'center' }}>{count.toLocaleString()}{suffix}</div>;
}

addPropertyControls(AnimatedCounter, {
  target: { type: ControlType.Number, title: 'Target', defaultValue: 1000 },
  duration: { type: ControlType.Number, title: 'Duration (s)', defaultValue: 2 },
  suffix: { type: ControlType.String, title: 'Suffix', defaultValue: '+' },
  fontSize: { type: ControlType.Number, title: 'Font Size', defaultValue: 48 },
  color: { type: ControlType.Color, title: 'Color', defaultValue: '#000' },
});
```

### Step 2: Data-Fetching Component

```tsx
import { addPropertyControls, ControlType } from 'framer';
import { useEffect, useState } from 'react';

export default function DataList({ apiUrl = 'https://jsonplaceholder.typicode.com/posts', limit = 5 }) {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    fetch(apiUrl).then(r => r.json()).then(d => setItems(d.slice(0, limit))).catch(() => {});
  }, [apiUrl, limit]);
  return (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {items.map((item, i) => <li key={i} style={{ padding: '8px 0', borderBottom: '1px solid #eee' }}>{item.title || item.name}</li>)}
    </ul>
  );
}

addPropertyControls(DataList, {
  apiUrl: { type: ControlType.String, title: 'API URL', defaultValue: 'https://jsonplaceholder.typicode.com/posts' },
  limit: { type: ControlType.Number, title: 'Limit', defaultValue: 5 },
});
```

### Step 3: Code Overrides

```tsx
// overrides.tsx — apply to any layer via properties panel
import { Override } from 'framer';

export function FadeInOnScroll(): Override {
  return { initial: { opacity: 0, y: 20 }, whileInView: { opacity: 1, y: 0 }, transition: { duration: 0.6 }, viewport: { once: true } };
}

export function MagneticHover(): Override {
  return { whileHover: { scale: 1.05 }, whileTap: { scale: 0.95 }, transition: { type: 'spring', stiffness: 400, damping: 17 } };
}

export function TypewriterText(): Override {
  return {
    initial: { width: 0 },
    animate: { width: '100%' },
    transition: { duration: 2, ease: 'linear' },
    style: { overflow: 'hidden', whiteSpace: 'nowrap' },
  };
}
```

### Step 4: Plugin Creating Code Files

```tsx
import { framer } from 'framer-plugin';

async function createOverrideFile() {
  const codeFile = await framer.createCodeFile({ name: 'Animations', language: 'tsx' });
  await codeFile.setFileContent(`
import { Override } from 'framer';
export function FadeIn(): Override {
  return { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.8 } };
}`.trim());
  framer.notify('Override file created');
}
```

## Output

- Animated components with property controls
- Data-fetching components for external APIs
- Reusable code overrides for animations
- Programmatic code file creation

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Component blank | Runtime error | Check Framer browser console |
| Controls not showing | Missing `addPropertyControls` | Call after component export |
| Override not applying | Wrong export | Must return `Override` type |
| Fetch fails | CORS | Use CORS-enabled API |

## Resources

- [Code Components](https://www.framer.com/developers/plugins-with-components)
- [Code Overrides](https://www.framer.com/developers/overrides-introduction)
- [Code File APIs](https://www.framer.com/updates/code-file-apis)

## Next Steps

For common errors, see `framer-common-errors`.
