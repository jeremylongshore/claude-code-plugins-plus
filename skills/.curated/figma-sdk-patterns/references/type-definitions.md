# Step 3: Type Definitions

Deep-dive reference for the `figma-sdk-patterns` skill — extracted from the 'Step 3: Type Definitions' step of the workflow.

```typescript
// src/figma-types.ts
export interface FigmaNode {
  id: string;
  name: string;
  type: string;
  children?: FigmaNode[];
  fills?: Paint[];
  strokes?: Paint[];
  absoluteBoundingBox?: { x: number; y: number; width: number; height: number };
  characters?: string;         // TEXT nodes
  style?: TypeStyle;           // TEXT nodes
  componentId?: string;        // INSTANCE nodes
  backgroundColor?: Color;     // CANVAS nodes
}

export interface FigmaFileResponse {
  name: string;
  lastModified: string;
  version: string;
  thumbnailUrl: string;
  document: FigmaNode;
  components: Record<string, ComponentMeta>;
  styles: Record<string, StyleMeta>;
}

export interface FigmaNodesResponse {
  nodes: Record<string, { document: FigmaNode; components: Record<string, ComponentMeta> }>;
}

export interface FigmaImagesResponse {
  images: Record<string, string | null>;  // nodeId -> URL (null = render failed)
}

export interface ImageOptions {
  format?: 'png' | 'svg' | 'jpg' | 'pdf';
  scale?: number;  // 0.01 to 4. SVG always exports at 1x.
}

interface Paint { type: string; color?: Color; opacity?: number }
interface Color { r: number; g: number; b: number; a?: number }
interface TypeStyle { fontFamily: string; fontSize: number; fontWeight: number }
interface ComponentMeta { key: string; name: string; description: string }
interface StyleMeta { key: string; name: string; style_type: 'FILL' | 'TEXT' | 'EFFECT' | 'GRID' }
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
