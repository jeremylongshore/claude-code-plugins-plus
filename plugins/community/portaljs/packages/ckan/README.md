# PortalJS CKAN Library

This is a library intended for the use with a CKAN Backend, it is composed of:

- Types mapping the CKAN API Objects
- A CKAN object that makes API calls
- Components that are usually needed in a data portal(searching, pagination, listing etc)

## Usage

To install this package on your project:

```bash
npm i @portaljs/ckan
```

> Note: React 18 is required.

You'll also have to import the styles CSS file in your project:

```ts
//  E.g.: Next.js => pages/_app.tsx
import '@portaljs/ckan/styles.css'
```
