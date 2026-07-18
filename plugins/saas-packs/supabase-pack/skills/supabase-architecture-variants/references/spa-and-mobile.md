# SPA (React/Vue) and Mobile (React Native)

## SPA Architecture (React with Vite)

SPAs use a single browser client with the anon key. All authorization is enforced via RLS. The service_role key is never present in the SPA bundle.

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

// Singleton client — one instance for the entire SPA
export const supabase = createClient<Database>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,  // handles OAuth redirects
      storage: window.localStorage,
    },
  }
)

// Auth state listener — call once at app initialization
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT') {
    // Clear local caches
    queryClient.clear()  // React Query
  }
  if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed')
  }
})
```

## React Hook for Auth-Protected Queries

```typescript
// src/hooks/useSupabaseQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supabase } from '../lib/supabase'

export function useTodos() {
  return useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('todos')
        .select('id, title, is_complete, created_at')
        .order('created_at', { ascending: false })

      if (error) throw new Error(`Failed to load todos: ${error.message}`)
      return data
    },
  })
}

export function useCreateTodo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (title: string) => {
      const { data, error } = await supabase
        .from('todos')
        .insert({ title })
        .select('id, title, is_complete, created_at')
        .single()

      if (error) throw new Error(`Failed to create todo: ${error.message}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
    },
  })
}
```

## Mobile Architecture (React Native with Expo)

React Native needs `AsyncStorage` for session persistence and deep link handling for OAuth.

```typescript
// lib/supabase.ts (React Native)
import { createClient } from '@supabase/supabase-js'
import AsyncStorage from '@react-native-async-storage/async-storage'
import type { Database } from './database.types'

export const supabase = createClient<Database>(
  process.env.EXPO_PUBLIC_SUPABASE_URL!,
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,  // disabled for React Native
    },
  }
)
```

## Mobile OAuth with Deep Links

```typescript
// lib/auth.ts (React Native)
import { supabase } from './supabase'
import * as Linking from 'expo-linking'
import * as WebBrowser from 'expo-web-browser'

const redirectUrl = Linking.createURL('auth/callback')

export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: redirectUrl,
      skipBrowserRedirect: true,  // handle manually for RN
    },
  })

  if (error) throw new Error(`OAuth failed: ${error.message}`)
  if (!data.url) throw new Error('No OAuth URL returned')

  // Open in-app browser
  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectUrl)

  if (result.type === 'success') {
    const url = new URL(result.url)
    const params = new URLSearchParams(url.hash.substring(1))
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')

    if (accessToken && refreshToken) {
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      })
      if (sessionError) throw sessionError
    }
  }
}
```

## App.json Deep Link Configuration (Expo)

```json
{
  "expo": {
    "scheme": "myapp",
    "plugins": [
      [
        "expo-linking",
        {
          "scheme": "myapp"
        }
      ]
    ]
  }
}
```
