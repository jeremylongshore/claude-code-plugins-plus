# Prisma Session Storage Schema

Complete Prisma schema with Shopify session model and example custom models.

```prisma
// prisma/schema.prisma
datasource db {
  provider = "sqlite"  // or "postgresql" for production
  url      = env("DATABASE_URL")
}

model Session {
  id            String    @id
  shop          String
  state         String
  isOnline      Boolean   @default(false)
  scope         String?
  expires       DateTime?
  accessToken   String
  userId        BigInt?
  firstName     String?
  lastName      String?
  email         String?
  accountOwner  Boolean   @default(false)
  locale        String?
  collaborator  Boolean?  @default(false)
  emailVerified Boolean?  @default(false)
}

// Your app's custom models
model ProductSync {
  id          String   @id @default(cuid())
  shop        String
  productId   String
  lastSynced  DateTime @default(now())
  status      String   @default("pending")
  @@unique([shop, productId])
}
```
