# Step 2: OAuth Callback Handler

Deep-dive reference for the `figma-enterprise-rbac` skill — extracted from the 'Step 2: OAuth Callback Handler' step of the workflow.

```typescript
// Express callback handler
app.get('/auth/figma/callback', async (req, res) => {
  const { code, state } = req.query;

  // Verify state matches what we sent (CSRF protection)
  if (state !== req.session.oauthState) {
    return res.status(403).json({ error: 'Invalid state parameter' });
  }

  try {
    // Exchange code within 30 seconds
    const tokens = await exchangeCode(code as string);

    // Get user info with the new token
    const userRes = await fetch('https://api.figma.com/v1/me', {
      headers: { Authorization: `Bearer ${tokens.access_token}` },
    });
    const user = await userRes.json();

    // Store tokens securely (encrypted at rest)
    await saveUserTokens(user.id, {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresAt: new Date(Date.now() + tokens.expires_in * 1000),
    });

    res.redirect('/dashboard?connected=figma');
  } catch (error) {
    console.error('Figma OAuth error:', error);
    res.redirect('/settings?error=figma_auth_failed');
  }
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
