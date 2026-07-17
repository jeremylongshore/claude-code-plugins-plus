# Supabase Realtime — Full Walkthrough

Supabase Realtime provides three channel types: database change listeners, client-to-client broadcast, and presence tracking for online status.

## Postgres Changes (listen to INSERT/UPDATE/DELETE on tables)

```typescript
// Subscribe to new messages in a chat table
const channel = supabase
  .channel('chat-room')
  .on(
    'postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'messages',
    },
    (payload) => {
      console.log('New message:', payload.new)
      // payload.new → full row data
      // payload.old → null for INSERT
    }
  )
  .on(
    'postgres_changes',
    {
      event: 'UPDATE',
      schema: 'public',
      table: 'messages',
      filter: 'room_id=eq.42',  // server-side filter
    },
    (payload) => {
      console.log('Updated:', payload.old, '→', payload.new)
    }
  )
  .on(
    'postgres_changes',
    {
      event: 'DELETE',
      schema: 'public',
      table: 'messages',
    },
    (payload) => {
      console.log('Deleted:', payload.old)
      // payload.new → null for DELETE
    }
  )
  .subscribe((status) => {
    console.log('Channel status:', status)
    // 'SUBSCRIBED' | 'TIMED_OUT' | 'CLOSED' | 'CHANNEL_ERROR'
  })

// Enable Realtime on the table (required one-time setup in SQL)
// ALTER PUBLICATION supabase_realtime ADD TABLE messages;

// Unsubscribe when done
supabase.removeChannel(channel)
```

## RLS integration — Realtime respects row-level security

```sql
-- Only receive changes for rows the user owns
CREATE POLICY "users_own_messages"
  ON messages FOR SELECT
  USING (auth.uid() = user_id);

-- The Realtime listener will only fire for rows passing this policy
```

## Broadcast (client-to-client, no database involved)

```typescript
const room = supabase.channel('collab-room')

// Listen for cursor movements from other users
room.on('broadcast', { event: 'cursor-move' }, ({ payload }) => {
  console.log(`User ${payload.userId} at (${payload.x}, ${payload.y})`)
})

// Subscribe first, then send
room.subscribe((status) => {
  if (status === 'SUBSCRIBED') {
    // Send cursor position to all other clients
    room.send({
      type: 'broadcast',
      event: 'cursor-move',
      payload: { userId: 'abc', x: 120, y: 340 },
    })
  }
})
```

## Presence (track who is online)

```typescript
const room = supabase.channel('app-presence')

// Sync event fires whenever the presence state changes
room.on('presence', { event: 'sync' }, () => {
  const state = room.presenceState()
  // state → { 'user-abc': [{ user_id: 'abc', online_at: '...' }], ... }
  const onlineUsers = Object.keys(state)
  console.log('Online:', onlineUsers.length, 'users')
})

room.on('presence', { event: 'join' }, ({ key, newPresences }) => {
  console.log('Joined:', key, newPresences)
})

room.on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
  console.log('Left:', key, leftPresences)
})

// Subscribe and track this user's presence
room.subscribe(async (status) => {
  if (status === 'SUBSCRIBED') {
    await room.track({
      user_id: currentUser.id,
      username: currentUser.email,
      online_at: new Date().toISOString(),
    })
  }
})

// Untrack when leaving (e.g., on component unmount)
await room.untrack()
```

Python Realtime equivalent: [python-examples.md](python-examples.md).
