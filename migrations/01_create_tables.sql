-- Create tables for chatwise-ai with Supabase Realtime support
-- These tables should be executed in your Supabase SQL Editor

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

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE handover_requests ENABLE ROW LEVEL SECURITY;

-- Enable Realtime for all tables
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE handover_requests;

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

-- Set up Realtime broadcast feature
COMMENT ON TABLE messages IS 'schema:public, table:messages';
COMMENT ON TABLE conversations IS 'schema:public, table:conversations';
COMMENT ON TABLE handover_requests IS 'schema:public, table:handover_requests'; 