-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge Base tables
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT fk_bot
        FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT fk_knowledge_base
        FOREIGN KEY (knowledge_base_id)
        REFERENCES knowledge_bases(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding VECTOR(1536),
    embedding_model TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT fk_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE
);

-- Create index for similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Conversation and Message tables
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    assigned_agent_id UUID,
    CONSTRAINT fk_bot
        FOREIGN KEY (bot_id)
        REFERENCES bots(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    sender_type TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    citations JSONB,
    confidence_score JSONB,
    CONSTRAINT fk_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE
);

-- Handover Request table
CREATE TABLE IF NOT EXISTS handover_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    last_message_id UUID NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending',
    handled_by UUID,
    CONSTRAINT fk_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_message
        FOREIGN KEY (last_message_id)
        REFERENCES messages(id)
        ON DELETE CASCADE
);

-- Agent Availability table
CREATE TABLE IF NOT EXISTS agent_availability (
    agent_id UUID PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'offline',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Set up Row Level Security for Realtime
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE handover_requests ENABLE ROW LEVEL SECURITY;

-- Create policies for conversations
CREATE POLICY "Agents can view conversations they are assigned to" ON conversations
    FOR SELECT
    USING (
        (assigned_agent_id = auth.uid()) OR 
        (bot_id IN (SELECT id FROM bots WHERE owner_id = auth.uid()))
    );

-- Create policies for messages
CREATE POLICY "Anyone can view messages in conversations they have access to" ON messages
    FOR SELECT
    USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE 
                (assigned_agent_id = auth.uid()) OR
                (bot_id IN (SELECT id FROM bots WHERE owner_id = auth.uid()))
        )
    );

CREATE POLICY "Anyone can insert messages to conversations they have access to" ON messages
    FOR INSERT
    WITH CHECK (
        conversation_id IN (
            SELECT id FROM conversations WHERE 
                (assigned_agent_id = auth.uid()) OR
                (bot_id IN (SELECT id FROM bots WHERE owner_id = auth.uid()))
        )
    );

-- Create policies for handover_requests
CREATE POLICY "Agents can view handover requests" ON handover_requests
    FOR SELECT
    USING (
        conversation_id IN (
            SELECT id FROM conversations WHERE
                (assigned_agent_id = auth.uid()) OR
                (bot_id IN (SELECT id FROM bots WHERE owner_id = auth.uid()))
        )
    );

-- Create Realtime publication for messages
BEGIN;
  DROP PUBLICATION IF EXISTS supabase_realtime;
  CREATE PUBLICATION supabase_realtime;
COMMIT;

-- Add tables to publication
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE handover_requests;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_availability;