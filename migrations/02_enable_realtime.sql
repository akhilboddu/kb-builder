-- Migration to specifically enable Supabase Realtime for chat functionality
-- Run this in your Supabase SQL Editor

-- Check if the Realtime publication exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        -- Create the publication if it doesn't exist
        CREATE PUBLICATION supabase_realtime FOR TABLE conversations, messages, handover_requests;
        RAISE NOTICE 'Created supabase_realtime publication';
    ELSE
        -- Add tables to existing publication
        ALTER PUBLICATION supabase_realtime ADD TABLE conversations, messages, handover_requests;
        RAISE NOTICE 'Added tables to existing supabase_realtime publication';
    END IF;
END
$$;

-- Configure the tables for INSERT, UPDATE, DELETE (depends on your requirements)
BEGIN;
    -- For messages - we care about new messages (INSERT) and possibly edits (UPDATE)
    SELECT supabase_realtime.enable_publication(
        publication_name => 'supabase_realtime',
        table_name => 'messages',  
        events => '{INSERT, UPDATE}'
    );

    -- For conversations - we care about status changes (UPDATE)
    SELECT supabase_realtime.enable_publication(
        publication_name => 'supabase_realtime',
        table_name => 'conversations',
        events => '{INSERT, UPDATE}'
    );

    -- For handover requests - we care about new requests and status changes
    SELECT supabase_realtime.enable_publication(
        publication_name => 'supabase_realtime',
        table_name => 'handover_requests',
        events => '{INSERT, UPDATE}'
    );
COMMIT;

-- Verify Realtime configuration
SELECT * FROM pg_publication WHERE pubname = 'supabase_realtime';
SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';

-- Note: After running this script, make sure to enable Realtime in the Supabase Dashboard:
-- 1. Go to Database → Replication → Realtime
-- 2. Ensure the tables are in the list of tables with Realtime enabled
-- 3. Check that the appropriate operations (INSERT, UPDATE, DELETE) are enabled for each table 