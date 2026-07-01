# Xquik TypeScript Types: X Write

```typescript

interface CreateTweetRequest {
  account: string;            // Connected X username or account ID
  text?: string;              // Tweet text (required unless media is provided)
  reply_to_tweet_id?: string; // Tweet ID to reply to
  attachment_url?: string;    // URL to attach as card
  community_id?: string;      // Community ID to post into
  is_note_tweet?: boolean;    // Long-form note tweet (up to 25,000 chars)
  media?: string[];           // Public image URLs, such as mediaUrl from POST /x/media
}

interface CreateTweetResponse {
  tweetId: string;            // ID of the newly created tweet
  success: boolean;           // Always true on success
}

interface WriteActionRequest {
  account: string;            // Connected X username or account ID
}

interface SendDmRequest {
  account: string;            // Connected X username or account ID
  text: string;               // Message text
  media_ids?: string[];       // Media IDs to attach
  reply_to_message_id?: string; // Message ID to reply to
}

interface UpdateProfileRequest {
  account: string;            // Connected X username or account ID
  name?: string;              // Display name
  description?: string;       // Bio
  location?: string;          // Location
  url?: string;               // Website URL
}

```
