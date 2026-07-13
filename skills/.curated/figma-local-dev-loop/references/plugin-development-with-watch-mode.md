# Step 3: Plugin Development with Watch Mode

Deep-dive reference for the `figma-local-dev-loop` skill — extracted from the 'Step 3: Plugin Development with Watch Mode' step of the workflow.

```json
{
  "scripts": {
    "build": "esbuild code.ts --bundle --outfile=dist/code.js --target=es2020",
    "watch": "esbuild code.ts --bundle --outfile=dist/code.js --target=es2020 --watch",
    "dev": "concurrently \"npm run watch\" \"npm run watch:ui\"",
    "watch:ui": "esbuild ui.tsx --bundle --outfile=dist/ui.html --loader:.html=copy --watch"
  },
  "devDependencies": {
    "@figma/plugin-typings": "^1.0.0",
    "esbuild": "^0.20.0",
    "typescript": "^5.0.0"
  }
}
```

Load the plugin in Figma:

1. Figma desktop > Plugins > Development > Import plugin from manifest
2. Select your `manifest.json`
3. Run with `npm run watch` -- changes auto-reload

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
