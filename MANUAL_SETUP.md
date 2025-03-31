# Manual Supabase Setup Guide

Since the CLI migrations are encountering permission issues and your API keys appear to be invalid, follow these steps to set up your Supabase database and enable Realtime:

## 0. Regenerate API Keys

Your current Supabase API keys appear to be invalid or expired. Let's generate new ones:

1. Log into your Supabase Dashboard at https://app.supabase.com
2. Select your project (URL: https://qbhevelbszcvxkutfmlg.supabase.co)
3. Go to "Project Settings" → "API" in the left sidebar
4. Under "Project API keys", you'll find:
   - `anon public` - For client-side code
   - `service_role` - For server-side admin operations (keep this secure)
5. Copy both keys and update your `.env` file:

```
SUPABASE_URL=https://qbhevelbszcvxkutfmlg.supabase.co
SUPABASE_KEY=eyJhbG...  # Replace with your new service_role key
SUPABASE_ANON_KEY=eyJh...  # Replace with your new anon key
```

6. After updating the `.env` file, test the connection:

```bash
cd /Users/akhilboddu/Documents/CHATWISE/chatwise-ai
source venv/bin/activate
python examples/simple_supabase_test.py
```

## 1. Create Tables

1. Log into your Supabase Dashboard at https://app.supabase.com
2. Select your project (URL: https://qbhevelbszcvxkutfmlg.supabase.co)
3. Navigate to the "SQL Editor" in the left sidebar
4. Create a new query
5. Copy and paste the following SQL:

```sql
-- Create enum types for conversation status and sender type
CREATE TYPE conversation_status AS ENUM ('open', 'assigned', 'closed');
CREATE TYPE sender_type AS ENUM ('user', 'bot', 'system');

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    bot_id TEXT NOT NULL,
    status conversation_status NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_agent_id TEXT
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type sender_type NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    citations JSONB,
    confidence_score JSONB,
    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Create handover_requests table
CREATE TABLE IF NOT EXISTS handover_requests (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    last_message_id UUID REFERENCES messages(id),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending',
    handled_by TEXT,
    CONSTRAINT fk_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_bot_id ON conversations(bot_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_handover_requests_conversation_id ON handover_requests(conversation_id);
CREATE INDEX IF NOT EXISTS idx_handover_requests_status ON handover_requests(status);
```

6. Click "Run" to execute the SQL

## 2. Enable Row Level Security (RLS)

1. Run the following SQL to enable Row Level Security:

```sql
-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE handover_requests ENABLE ROW LEVEL SECURITY;

-- Add RLS policies (adjust these based on your auth setup)
-- Example policy for conversations
CREATE POLICY "Authenticated users can view their conversations" 
ON conversations FOR SELECT 
USING (auth.role() = 'authenticated');

-- Example policy for messages
CREATE POLICY "Authenticated users can view messages" 
ON messages FOR SELECT 
USING (auth.role() = 'authenticated');

-- Example policy for handover requests
CREATE POLICY "Authenticated users can view handover requests" 
ON handover_requests FOR SELECT 
USING (auth.role() = 'authenticated');

-- Add insert policies
CREATE POLICY "Authenticated users can insert conversations" 
ON conversations FOR INSERT 
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert messages" 
ON messages FOR INSERT 
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert handover requests" 
ON handover_requests FOR INSERT 
WITH CHECK (auth.role() = 'authenticated');

-- Add update policies
CREATE POLICY "Authenticated users can update conversations" 
ON conversations FOR UPDATE 
USING (auth.role() = 'authenticated');
```

## 3. Enable Realtime

1. In your Supabase dashboard, navigate to "Database" → "Replication" → "Realtime"

2. Toggle on Realtime for the following tables:
   - `conversations`
   - `messages`
   - `handover_requests`

3. For each table, make sure the following events are checked:
   - INSERT (required for all tables)
   - UPDATE (required for status changes)

4. Click "Save" to apply the changes

5. Additionally, you can run this SQL to ensure Realtime is properly configured:

```sql
-- Enable Realtime via publication
BEGIN;
    -- Check if publication exists
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime'
        ) THEN
            -- Create the publication
            CREATE PUBLICATION supabase_realtime;
        END IF;
    END
    $$;

    -- Add tables to publication
    ALTER PUBLICATION supabase_realtime ADD TABLE conversations, messages, handover_requests;

    -- Set comments to help with realtime configuration
    COMMENT ON TABLE messages IS 'schema:public, table:messages';
    COMMENT ON TABLE conversations IS 'schema:public, table:conversations';
    COMMENT ON TABLE handover_requests IS 'schema:public, table:handover_requests';
COMMIT;
```

## 4. Test Your Setup

After completing the setup, you can test it with our test script:

```bash
cd /Users/akhilboddu/Documents/CHATWISE/chatwise-ai
source venv/bin/activate
python examples/test_realtime.py
```

If the test completes successfully, you'll see confirmation that Supabase Realtime is properly configured.

## 5. Troubleshooting

If you encounter issues:

1. **Check Table Creation:**
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public' AND
   table_name IN ('conversations', 'messages', 'handover_requests');
   ```

2. **Verify Realtime Publication:**
   ```sql
   SELECT * FROM pg_publication WHERE pubname = 'supabase_realtime';
   SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';
   ```

3. **Check API Keys:**
   Make sure you're using the service role key (SUPABASE_KEY) for administrative operations, not the anon key.

4. **Enable Realtime in UI:**
   Sometimes the UI toggle for Realtime needs to be manually adjusted even after SQL configuration. 