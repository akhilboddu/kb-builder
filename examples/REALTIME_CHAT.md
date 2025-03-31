# Supabase Realtime Chat Integration

This guide explains how to implement real-time chat features using Supabase Realtime in the Chatwise AI Sales Agent.

## Overview

Supabase Realtime allows for real-time updates when data changes in your database. For chat applications, this enables:

1. Real-time message delivery
2. Typing indicators
3. Online status updates
4. Live conversation assignments

## Backend Implementation

The backend implementation includes:

1. Supabase client setup for realtime channels
2. REST API endpoints for managing subscriptions
3. Service functions to handle realtime events

### Key Components

- **Realtime Service**: Handles subscriptions, message saving, and broadcasting events
- **Chat Router**: Provides endpoints for subscribing to conversations and sending typing indicators

## Frontend Implementation

The frontend implementation includes:

1. A Supabase Realtime client wrapper
2. React components for the chat interface

### Usage Example

```jsx
// Import the chat component
import ChatComponent from './examples/ChatComponent';

// Use in your app
function App() {
  return (
    <div className="app">
      <h1>Chatwise AI Sales Agent</h1>
      <ChatComponent 
        botId="bot-123"
        userEmail="user@example.com"
        userPassword="password123"
      />
    </div>
  );
}
```

## Database Schema Requirements

Your Supabase database should include:

1. `conversations` table with:
   - `id` (primary key)
   - `bot_id` (foreign key)
   - `status` (open, assigned, closed)
   - `created_at` and `updated_at` timestamps
   - `assigned_agent_id` (optional)

2. `messages` table with:
   - `id` (primary key)
   - `conversation_id` (foreign key)
   - `sender_type` (user, bot, system)
   - `content` (message text)
   - `timestamp`
   - `citations` (JSON, optional)
   - `confidence_score` (JSON, optional)

## Enabling Supabase Realtime

1. In your Supabase project, go to Database → Replication
2. Enable Realtime for the `messages` and `conversations` tables
3. Configure publication to include INSERT operations at minimum

## Realtime Events

The implementation handles these key event types:

1. **New Messages**: When a new message is saved to the database
2. **Typing Indicators**: When a user starts or stops typing
3. **Conversation Status Changes**: When a conversation is assigned or closed

## Security Considerations

1. Client-side subscriptions are authenticated using JWT tokens
2. Server validates user access to conversations before allowing subscriptions
3. All real-time events go through the same authorization checks as REST endpoints

## Testing Realtime Features

Test the realtime features using the provided example client:

1. Start the API server locally
2. Open the example chat UI in a browser
3. Use multiple browser windows to simulate different users
4. Monitor network traffic to see the WebSocket connections

## Performance Optimization

For high-traffic applications:

1. Consider setting up dedicated Supabase realtime servers
2. Implement connection pooling for database operations
3. Add rate limiting for typing indicators to prevent spam

---

For more details, see the code examples in the `examples/` directory:
- `supabase_realtime_client.js`: Client-side wrapper for Supabase Realtime
- `ChatComponent.jsx`: React component implementing the chat interface 