---
description: Generate Prisma schema from natural language descriptions
shortcut: psg
category: database
difficulty: beginner
estimated_time: 3-5 minutes
---

# Prisma Schema Generator

Generates complete Prisma schema files from natural language descriptions, including models, relationships, indexes, and validation.

## What This Command Does

**Generated Schema:**
-  Prisma models with fields
-  Relationships (one-to-one, one-to-many, many-to-many)
-  Indexes and unique constraints
-  Default values and validators
-  Database-specific configuration
-  Example queries

**Output:** Complete `schema.prisma` file ready for migration

**Time:** 3-5 minutes

---

## Usage

```bash
# Generate schema from description
/prisma-schema-gen "Blog with users, posts, and comments"

# Shortcut
/psg "E-commerce with products, orders, and customers"

# Specify database
/psg "Task management app" --database postgresql

# With specific relationships
/psg "Social network with users, posts, likes, and follows"
```

---

## Example Output

**Input:**
```
/psg "Blog platform with users, posts, comments, and tags"
```

**Generated schema.prisma:**

```prisma
// This is your Prisma schema file

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String
  password  String
  bio       String?
  avatar    String?
  posts     Post[]
  comments  Comment[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([email])
  @@map("users")
}

model Post {
  id          String   @id @default(uuid())
  title       String
  slug        String   @unique
  content     String   @db.Text
  excerpt     String?
  published   Boolean  @default(false)
  publishedAt DateTime?
  viewCount   Int      @default(0)
  authorId    String
  author      User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  comments    Comment[]
  tags        PostTag[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([authorId])
  @@index([slug])
  @@index([published, publishedAt])
  @@map("posts")
}

model Comment {
  id        String   @id @default(uuid())
  content   String   @db.Text
  postId    String
  post      Post     @relation(fields: [postId], references: [id], onDelete: Cascade)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([postId])
  @@index([authorId])
  @@map("comments")
}

model Tag {
  id    String    @id @default(uuid())
  name  String    @unique
  slug  String    @unique
  posts PostTag[]

  @@index([slug])
  @@map("tags")
}

// Junction table for many-to-many
model PostTag {
  id     String @id @default(uuid())
  postId String
  post   Post   @relation(fields: [postId], references: [id], onDelete: Cascade)
  tagId  String
  tag    Tag    @relation(fields: [tagId], references: [id], onDelete: Cascade)

  @@unique([postId, tagId])
  @@index([postId])
  @@index([tagId])
  @@map("post_tags")
}
```

---

## Generated Files

### **Migrations**

```bash
# After generating schema, run:
npx prisma migrate dev --name init

# This creates:
# - migrations/
#   └── 20250110000000_init/
#       └── migration.sql
```

### **Example Queries (TypeScript)**

```typescript
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Create user
async function createUser() {
  const user = await prisma.user.create({
    data: {
      email: '[email protected]',
      name: 'John Doe',
      password: 'hashed_password_here'
    }
  })
  return user
}

// Create post with tags
async function createPost() {
  const post = await prisma.post.create({
    data: {
      title: 'Getting Started with Prisma',
      slug: 'getting-started-with-prisma',
      content: 'Full blog post content...',
      published: true,
      publishedAt: new Date(),
      authorId: 'user-uuid-here',
      tags: {
        create: [
          {
            tag: {
              connectOrCreate: {
                where: { slug: 'prisma' },
                create: { name: 'Prisma', slug: 'prisma' }
              }
            }
          }
        ]
      }
    },
    include: {
      author: true,
      tags: {
        include: {
          tag: true
        }
      }
    }
  })
  return post
}

// Get posts with related data
async function getPosts() {
  const posts = await prisma.post.findMany({
    where: {
      published: true
    },
    include: {
      author: {
        select: {
          id: true,
          name: true,
          avatar: true
        }
      },
      tags: {
        include: {
          tag: true
        }
      },
      _count: {
        select: {
          comments: true
        }
      }
    },
    orderBy: {
      publishedAt: 'desc'
    },
    take: 10
  })
  return posts
}

// Create comment
async function createComment() {
  const comment = await prisma.comment.create({
    data: {
      content: 'Great article!',
      postId: 'post-uuid-here',
      authorId: 'user-uuid-here'
    },
    include: {
      author: {
        select: {
          name: true,
          avatar: true
        }
      }
    }
  })
  return comment
}

// Search posts
async function searchPosts(query: string) {
  const posts = await prisma.post.findMany({
    where: {
      OR: [
        { title: { contains: query, mode: 'insensitive' } },
        { content: { contains: query, mode: 'insensitive' } }
      ],
      published: true
    },
    include: {
      author: true
    }
  })
  return posts
}

// Get post with comments
async function getPostWithComments(slug: string) {
  const post = await prisma.post.findUnique({
    where: { slug },
    include: {
      author: true,
      comments: {
        include: {
          author: {
            select: {
              name: true,
              avatar: true
            }
          }
        },
        orderBy: {
          createdAt: 'desc'
        }
      },
      tags: {
        include: {
          tag: true
        }
      }
    }
  })

  if (!post) {
    throw new Error('Post not found')
  }

  // Increment view count
  await prisma.post.update({
    where: { id: post.id },
    data: { viewCount: { increment: 1 } }
  })

  return post
}

// Get posts by tag
async function getPostsByTag(tagSlug: string) {
  const posts = await prisma.post.findMany({
    where: {
      published: true,
      tags: {
        some: {
          tag: {
            slug: tagSlug
          }
        }
      }
    },
    include: {
      author: true,
      tags: {
        include: {
          tag: true
        }
      }
    },
    orderBy: {
      publishedAt: 'desc'
    }
  })
  return posts
}
```

---

## Common Patterns

### **1. E-commerce Schema**

```prisma
model Customer {
  id       String  @id @default(uuid())
  email    String  @unique
  name     String
  phone    String?
  orders   Order[]
  cart     Cart?
}

model Product {
  id          String      @id @default(uuid())
  name        String
  description String?
  price       Decimal     @db.Decimal(10, 2)
  stock       Int         @default(0)
  orderItems  OrderItem[]
  cartItems   CartItem[]
}

model Order {
  id         String      @id @default(uuid())
  customerId String
  customer   Customer    @relation(fields: [customerId], references: [id])
  items      OrderItem[]
  total      Decimal     @db.Decimal(10, 2)
  status     String      // 'pending', 'paid', 'shipped', 'delivered'
  createdAt  DateTime    @default(now())
}

model OrderItem {
  id        String  @id @default(uuid())
  orderId   String
  order     Order   @relation(fields: [orderId], references: [id])
  productId String
  product   Product @relation(fields: [productId], references: [id])
  quantity  Int
  price     Decimal @db.Decimal(10, 2)
}
```

### **2. Social Network Schema**

```prisma
model User {
  id        String   @id @default(uuid())
  username  String   @unique
  email     String   @unique
  posts     Post[]
  likes     Like[]
  following Follow[] @relation("Following")
  followers Follow[] @relation("Followers")
}

model Post {
  id        String   @id @default(uuid())
  content   String
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
  likes     Like[]
  createdAt DateTime @default(now())
}

model Like {
  id     String @id @default(uuid())
  userId String
  user   User   @relation(fields: [userId], references: [id])
  postId String
  post   Post   @relation(fields: [postId], references: [id])

  @@unique([userId, postId])
}

model Follow {
  id          String @id @default(uuid())
  followerId  String
  followingId String
  follower    User   @relation("Following", fields: [followerId], references: [id])
  following   User   @relation("Followers", fields: [followingId], references: [id])

  @@unique([followerId, followingId])
}
```

### **3. Multi-tenant SaaS Schema**

```prisma
model Organization {
  id      String   @id @default(uuid())
  name    String
  slug    String   @unique
  members Member[]
  projects Project[]
}

model User {
  id          String   @id @default(uuid())
  email       String   @unique
  memberships Member[]
}

model Member {
  id       String       @id @default(uuid())
  userId   String
  user     User         @relation(fields: [userId], references: [id])
  orgId    String
  org      Organization @relation(fields: [orgId], references: [id])
  role     String       // 'owner', 'admin', 'member'

  @@unique([userId, orgId])
}

model Project {
  id    String       @id @default(uuid())
  name  String
  orgId String
  org   Organization @relation(fields: [orgId], references: [id])
  tasks Task[]
}

model Task {
  id        String  @id @default(uuid())
  title     String
  completed Boolean @default(false)
  projectId String
  project   Project @relation(fields: [projectId], references: [id])
}
```

---

## Database Support

**PostgreSQL:**
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// PostgreSQL-specific types
model Example {
  jsonData Json
  textData String @db.Text
  amount   Decimal @db.Decimal(10, 2)
}
```

**MySQL:**
```prisma
datasource db {
  provider = "mysql"
  url      = env("DATABASE_URL")
}
```

**SQLite (Development):**
```prisma
datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}
```

**MongoDB:**
```prisma
datasource db {
  provider = "mongodb"
  url      = env("DATABASE_URL")
}

model User {
  id    String @id @default(auto()) @map("_id") @db.ObjectId
  email String @unique
}
```

---

## Getting Started

**1. Install Prisma:**
```bash
npm install @prisma/client
npm install -D prisma
```

**2. Initialize Prisma:**
```bash
npx prisma init
```

**3. Use generated schema:**
- Replace `prisma/schema.prisma` with generated content
- Set `DATABASE_URL` in `.env`

**4. Create migration:**
```bash
npx prisma migrate dev --name init
```

**5. Generate Prisma Client:**
```bash
npx prisma generate
```

**6. Use in code:**
```typescript
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()
```

---

## Related Commands

- `/sql-query-builder` - Generate SQL queries
- Database Designer (agent) - Schema design review

---

**Generate schemas fast. Migrate safely. Query confidently.** ️
