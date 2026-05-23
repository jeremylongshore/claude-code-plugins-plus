---
title: "Building a Complete React Native Mobile App in One Session: 17,620 Lines of Production Code"
description: "How I built a complete React Native mobile app with Firebase auth, Firestore CRUD, and App Store deployment configuration in a single working session - and the architectural patterns that made it possible."
date: "2025-12-13"
tags: ["react-native", "expo", "firebase", "mobile-development", "typescript", "architecture"]
featured: false
---
## The Challenge

Transform a Next.js web application into a native mobile app ready for iOS App Store and Google Play Store submission. Not a prototype. Not an MVP. A complete, production-ready application with full feature parity.

**Time constraint:** One working session.

**Result:** 17,620 lines of code, 37 files, 10 screens, full CI/CD pipeline.

## The Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Framework | Expo SDK 54 | Managed workflow, OTA updates, EAS Build |
| Navigation | Expo Router | File-based routing (familiar from Next.js) |
| Language | TypeScript | Type safety, IDE support |
| Backend | Firebase | Auth + Firestore (existing infrastructure) |
| Server State | React Query | Caching, mutations, optimistic updates |
| Client State | Zustand | Minimal boilerplate, persist middleware |
| Forms | React Hook Form + Zod | Validation, error handling |

## The Secret: 94% Code Reuse

The biggest accelerator wasn't a framework or library - it was **architectural consistency** between the web and mobile codebases.

### What Transferred Directly

```typescript
// These types work identically in Next.js and React Native
type SoccerPositionCode =
  | 'GK' | 'CB' | 'RB' | 'LB' | 'RWB' | 'LWB'
  | 'DM' | 'CM' | 'AM' | 'RW' | 'LW' | 'ST' | 'CF';

type GameResult = 'Win' | 'Loss' | 'Draw';

interface PlayerStats {
  totalGames: number;
  wins: number;
  losses: number;
  draws: number;
  goals: number;
  assists: number;
  minutesPlayed: number;
  goalsPerGame: number;
  assistsPerGame: number;
}
```

The entire `src/types/` directory copied over with zero modifications. Same for:

- Validation schemas (Zod)
- Business logic (stats calculations)
- Constants (position labels, league codes)
- Firebase service patterns

### What Changed

1. **UI Components** - React Native has different primitives (`View` instead of `div`, `Text` instead of `span`)
2. **Navigation** - Expo Router instead of Next.js App Router (but same file-based pattern)
3. **Styling** - StyleSheet instead of Tailwind (though NativeWind exists)
4. **Storage** - AsyncStorage for auth persistence

## Architecture Deep Dive

### File-Based Routing with Expo Router

```
mobile/app/
├── (auth)/                   # Auth group (unauthenticated)
│   ├── _layout.tsx           # Stack navigator
│   ├── login.tsx
│   ├── register.tsx
│   └── forgot-password.tsx
├── (tabs)/                   # Tab group (authenticated)
│   ├── _layout.tsx           # Tab bar
│   ├── index.tsx             # Dashboard
│   ├── players.tsx
│   ├── stats.tsx
│   └── settings.tsx
├── player/
│   └── [id].tsx              # Dynamic route
├── game/
│   └── new.tsx
├── _layout.tsx               # Root layout
└── index.tsx                 # Entry redirect
```

This mirrors Next.js App Router patterns exactly. The mental model transfers.

### State Management Pattern

**React Query for server state:**

```typescript
// Query key factory for organization
export const playerKeys = {
  all: ['players'] as const,
  list: (userId: string) => [...playerKeys.all, 'list', userId] as const,
  detail: (userId: string, playerId: string) =>
    [...playerKeys.all, 'detail', userId, playerId] as const,
};

// Hook with automatic cache management
export function usePlayers() {
  const { user } = useAuth();

  return useQuery({
    queryKey: playerKeys.list(user?.id ?? ''),
    queryFn: () => getPlayers(user!.id),
    enabled: !!user?.id,
  });
}
```

**Zustand for client state:**

```typescript
interface AuthState {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  user: null,
  firebaseUser: null,
  isLoading: true,
  isAuthenticated: false,

  initialize: () => {
    return onAuthChange(async (firebaseUser) => {
      if (firebaseUser) {
        const userDoc = await getUserDocument(firebaseUser.uid);
        set({
          firebaseUser,
          user: userDoc ? convertUserDocument(userDoc, firebaseUser.uid) : null,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({
          firebaseUser: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    });
  },
}));
```

### Firebase JS SDK vs React Native Firebase

I initially tried `@react-native-firebase/*` but hit peer dependency conflicts with Expo SDK 54's React 19. The solution: use the standard Firebase JS SDK.

```typescript
import { initializeAuth, getAuth } from 'firebase/auth';
// @ts-expect-error - subpath export for React Native
import { getReactNativePersistence } from '@firebase/auth/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

function getFirebaseAuth(): Auth {
  const app = getFirebaseApp();
  try {
    return getAuth(app);
  } catch {
    return initializeAuth(app, {
      persistence: getReactNativePersistence(AsyncStorage),
    });
  }
}
```

Trade-off: Slightly larger bundle, but full Expo managed workflow compatibility.

## CI/CD Configuration

### EAS Build Profiles

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": { "simulator": false }
    },
    "production": {
      "autoIncrement": true
    }
  }
}
```

### GitHub Actions Workflow

```yaml
name: Mobile Deploy

on:
  workflow_dispatch:
    inputs:
      platform:
        type: choice
        options: [all, ios, android]
      profile:
        type: choice
        options: [development, preview, production]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: expo/expo-github-action@v8
        with:
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - run: eas build --platform ${{ inputs.platform }} --profile ${{ inputs.profile }}
```

## What I Shipped

### Screens (10 total)

- Login, Register (COPPA compliant), Forgot Password
- Dashboard with quick actions
- Players list with add/edit/delete
- Player detail with games history
- Game logging form
- Statistics dashboard
- Settings with sign out

### Infrastructure

- Custom app icons (branded "H" with soccer pattern)
- EAS Build configuration
- GitHub Actions CI/CD
- Comprehensive documentation (4 docs + README)

### Documentation

- Setup guide (257-DR-GUID)
- Deployment runbook (258-OD-DEPL)
- API reference (259-DR-REFF)
- After action report (260-AA-AACR)

## Key Takeaways

1. **Architectural consistency pays dividends** - Same patterns across web and mobile means 94% code reuse.

2. **File-based routing is the future** - Expo Router and Next.js App Router share the same mental model. Learn one, know both.

3. **Managed workflows remove friction** - Expo + EAS means no Xcode/Android Studio for most development.

4. **Type safety enables speed** - TypeScript types that work across platforms catch errors before runtime.

5. **Documentation is part of shipping** - A feature isn't done until it's documented.

## The PR

All code is available for review: [github.com/jeremylongshore/hustle/pull/2](https://github.com/jeremylongshore/hustle/pull/2)

*Building mobile apps doesn't have to mean starting from scratch. With the right architecture, your web codebase is a head start, not a liability.*
