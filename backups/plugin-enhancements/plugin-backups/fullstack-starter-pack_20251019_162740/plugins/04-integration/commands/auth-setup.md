---
description: Generate authentication boilerplate with JWT, OAuth, and session support
shortcut: as
category: backend
difficulty: intermediate
estimated_time: 5-10 minutes
---

# Auth Setup

Generates complete authentication boilerplate including JWT, OAuth (Google/GitHub), session management, and password reset flows.

## What This Command Does

**Generated Auth System:**
-  JWT authentication with refresh tokens
-  OAuth2 (Google, GitHub, Facebook)
-  Password hashing (bcrypt)
-  Email verification
-  Password reset flow
-  Session management
-  Rate limiting on auth endpoints
-  Authentication middleware

**Output:** Complete authentication system ready for production

**Time:** 5-10 minutes

---

## Usage

```bash
# Generate full auth system
/auth-setup jwt

# Shortcut
/as oauth --providers google,github

# With specific features
/as jwt --features email-verification,password-reset,2fa
```

---

## Example Output

### **JWT Authentication**

**auth.service.ts:**
```typescript
import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
import { User } from './models/User'

export class AuthService {
  async register(email: string, password: string, name: string) {
    // Check if user exists
    const existing = await User.findOne({ email })
    if (existing) {
      throw new Error('Email already registered')
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 12)

    // Create user
    const user = await User.create({
      email,
      password: hashedPassword,
      name,
      emailVerified: false
    })

    // Generate verification token
    const verificationToken = this.generateToken({ userId: user.id, type: 'verify' }, '24h')

    // Send verification email (implement sendEmail)
    await this.sendVerificationEmail(email, verificationToken)

    // Generate auth tokens
    const accessToken = this.generateAccessToken(user)
    const refreshToken = this.generateRefreshToken(user)

    return {
      user: { id: user.id, email: user.email, name: user.name },
      accessToken,
      refreshToken
    }
  }

  async login(email: string, password: string) {
    const user = await User.findOne({ email })
    if (!user) {
      throw new Error('Invalid credentials')
    }

    const validPassword = await bcrypt.compare(password, user.password)
    if (!validPassword) {
      throw new Error('Invalid credentials')
    }

    if (!user.emailVerified) {
      throw new Error('Please verify your email')
    }

    const accessToken = this.generateAccessToken(user)
    const refreshToken = this.generateRefreshToken(user)

    return {
      user: { id: user.id, email: user.email, name: user.name },
      accessToken,
      refreshToken
    }
  }

  async refreshToken(refreshToken: string) {
    try {
      const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET!) as any

      const user = await User.findById(decoded.userId)
      if (!user) {
        throw new Error('User not found')
      }

      const accessToken = this.generateAccessToken(user)
      return { accessToken }
    } catch (error) {
      throw new Error('Invalid refresh token')
    }
  }

  async verifyEmail(token: string) {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any

    if (decoded.type !== 'verify') {
      throw new Error('Invalid token type')
    }

    await User.findByIdAndUpdate(decoded.userId, { emailVerified: true })
    return { message: 'Email verified successfully' }
  }

  async requestPasswordReset(email: string) {
    const user = await User.findOne({ email })
    if (!user) {
      // Don't reveal if user exists
      return { message: 'If email exists, reset link sent' }
    }

    const resetToken = this.generateToken({ userId: user.id, type: 'reset' }, '1h')
    await this.sendPasswordResetEmail(email, resetToken)

    return { message: 'If email exists, reset link sent' }
  }

  async resetPassword(token: string, newPassword: string) {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any

    if (decoded.type !== 'reset') {
      throw new Error('Invalid token type')
    }

    const hashedPassword = await bcrypt.hash(newPassword, 12)
    await User.findByIdAndUpdate(decoded.userId, { password: hashedPassword })

    return { message: 'Password reset successfully' }
  }

  private generateAccessToken(user: any) {
    return jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET!,
      { expiresIn: '15m' }
    )
  }

  private generateRefreshToken(user: any) {
    return jwt.sign(
      { userId: user.id },
      process.env.JWT_REFRESH_SECRET!,
      { expiresIn: '7d' }
    )
  }

  private generateToken(payload: any, expiresIn: string) {
    return jwt.sign(payload, process.env.JWT_SECRET!, { expiresIn })
  }

  private async sendVerificationEmail(email: string, token: string) {
    // Implement with SendGrid, Resend, etc.
  }

  private async sendPasswordResetEmail(email: string, token: string) {
    // Implement with SendGrid, Resend, etc.
  }
}
```

### **OAuth2 Setup (Google)**

**oauth.controller.ts:**
```typescript
import { OAuth2Client } from 'google-auth-library'

const googleClient = new OAuth2Client(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  process.env.GOOGLE_REDIRECT_URI
)

export class OAuthController {
  async googleLogin(req: Request, res: Response) {
    const authUrl = googleClient.generateAuthUrl({
      access_type: 'offline',
      scope: ['profile', 'email']
    })

    res.redirect(authUrl)
  }

  async googleCallback(req: Request, res: Response) {
    const { code } = req.query

    const { tokens } = await googleClient.getToken(code as string)
    googleClient.setCredentials(tokens)

    const ticket = await googleClient.verifyIdToken({
      idToken: tokens.id_token!,
      audience: process.env.GOOGLE_CLIENT_ID
    })

    const payload = ticket.getPayload()
    if (!payload) {
      throw new Error('Invalid token')
    }

    // Find or create user
    let user = await User.findOne({ email: payload.email })

    if (!user) {
      user = await User.create({
        email: payload.email,
        name: payload.name,
        avatar: payload.picture,
        emailVerified: true,
        provider: 'google',
        providerId: payload.sub
      })
    }

    // Generate tokens
    const accessToken = generateAccessToken(user)
    const refreshToken = generateRefreshToken(user)

    // Redirect with tokens
    res.redirect(`/auth/success?token=${accessToken}&refresh=${refreshToken}`)
  }
}
```

### **Authentication Middleware**

**auth.middleware.ts:**
```typescript
import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'

declare global {
  namespace Express {
    interface Request {
      user?: {
        userId: string
        email: string
      }
    }
  }
}

export async function authenticate(req: Request, res: Response, next: NextFunction) {
  try {
    const authHeader = req.headers.authorization

    if (!authHeader?.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'No token provided' })
    }

    const token = authHeader.split(' ')[1]

    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any

    req.user = {
      userId: decoded.userId,
      email: decoded.email
    }

    next()
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: 'Token expired' })
    }
    return res.status(401).json({ error: 'Invalid token' })
  }
}

export function authorize(...roles: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Not authenticated' })
    }

    const user = await User.findById(req.user.userId)

    if (!user || !roles.includes(user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }

    next()
  }
}
```

### **Rate Limiting**

```typescript
import rateLimit from 'express-rate-limit'

export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 requests per window
  message: 'Too many login attempts, please try again later',
  standardHeaders: true,
  legacyHeaders: false
})

// Usage
app.post('/api/auth/login', authLimiter, authController.login)
```

---

## Environment Variables

```bash
# JWT
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-key
JWT_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=7d

# OAuth - Google
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback

# OAuth - GitHub
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:3000/api/auth/github/callback

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=[email protected]
```

---

## API Routes

```typescript
// routes/auth.routes.ts
import { Router } from 'express'
import { AuthController } from '../controllers/auth.controller'
import { authenticate } from '../middleware/auth.middleware'
import { authLimiter } from '../middleware/rate-limit'

const router = Router()
const authController = new AuthController()

// Registration & Login
router.post('/register', authController.register)
router.post('/login', authLimiter, authController.login)
router.post('/refresh', authController.refreshToken)
router.post('/logout', authenticate, authController.logout)

// Email Verification
router.post('/verify-email', authController.verifyEmail)
router.post('/resend-verification', authController.resendVerification)

// Password Reset
router.post('/forgot-password', authLimiter, authController.forgotPassword)
router.post('/reset-password', authController.resetPassword)

// OAuth
router.get('/google', authController.googleLogin)
router.get('/google/callback', authController.googleCallback)
router.get('/github', authController.githubLogin)
router.get('/github/callback', authController.githubCallback)

// Profile
router.get('/me', authenticate, authController.getProfile)
router.patch('/me', authenticate, authController.updateProfile)
router.post('/change-password', authenticate, authController.changePassword)

export default router
```

---

## Related Commands

- `/env-config-setup` - Generate environment config
- `/express-api-scaffold` - Generate Express API
- `/fastapi-scaffold` - Generate FastAPI

---

**Secure authentication. Easy integration. Production-ready.** 
