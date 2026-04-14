# OAuth Flow Implementation (Public Apps)

Express-based OAuth flow for public Shopify apps. Handles the redirect to Shopify and the callback that exchanges the authorization code for an access token.

```typescript
// routes/auth.ts — Express example
import express from "express";
import shopify from "../shopify";

const router = express.Router();

// Step 1: Begin OAuth — redirect merchant to Shopify
router.get("/auth", async (req, res) => {
  const shop = req.query.shop as string;
  // Generates the authorization URL with HMAC validation
  const authRoute = await shopify.auth.begin({
    shop: shopify.utils.sanitizeShop(shop, true)!,
    callbackPath: "/auth/callback",
    isOnline: false, // offline = long-lived token
    rawRequest: req,
    rawResponse: res,
  });
});

// Step 2: Handle callback — exchange code for access token
router.get("/auth/callback", async (req, res) => {
  const callback = await shopify.auth.callback({
    rawRequest: req,
    rawResponse: res,
  });

  // callback.session contains the access token
  const session: Session = callback.session;
  console.log("Access token:", session.accessToken);
  console.log("Shop:", session.shop); // "store-name.myshopify.com"
  console.log("Scopes:", session.scope); // "read_products,write_products,..."

  // IMPORTANT: Persist session to your database
  await saveSession(session);

  res.redirect(`/?shop=${session.shop}&host=${req.query.host}`);
});

export default router;
```
