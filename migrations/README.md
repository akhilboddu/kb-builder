# Supabase Database Migrations

This directory contains SQL migrations for setting up the Chatwise AI database tables in Supabase, with Realtime functionality enabled.

## Migration Steps

### 1. Run the Migrations

For each migration file, you need to run the SQL in your Supabase project.

#### Steps to Execute Migrations:

1. Log into your Supabase Dashboard at https://app.supabase.com
2. Select your project (URL: https://qbhevelbszcvxkutfmlg.supabase.co)
3. Navigate to the "SQL Editor" in the left sidebar
4. Create a new query
5. Copy the contents of each migration file in order:
   - First `01_create_tables.sql`
   - Then `02_enable_realtime.sql`
6. Run each file separately

### 2. Verify Realtime Is Enabled

After running the migrations, verify that Realtime is properly enabled:

1. Navigate to Database → Replication → Realtime in the Supabase Dashboard
2. Ensure the following tables are listed with Realtime enabled:
   - `conversations`
   - `messages`
   - `handover_requests`
3. For each table, confirm that the appropriate operations are enabled:
   - For `messages`: At minimum, INSERT should be enabled
   - For `conversations`: INSERT and UPDATE should be enabled
   - For `handover_requests`: INSERT and UPDATE should be enabled

### 3. Test Realtime Functionality

To test if Realtime is working correctly:

1. Start your local API server with:
   ```
   cd /Users/akhilboddu/Documents/CHATWISE/chatwise-ai && source venv/bin/activate && python -m uvicorn main:app --reload --port 8081
   ```

2. Create a conversation (using the API or directly in the Supabase database)
3. Insert a message into the conversation
4. Verify that Realtime events are being received in the client

## Troubleshooting Realtime Issues

If Realtime doesn't seem to be working:

1. **Check Supabase Dashboard**:
   - Ensure Realtime is enabled for the relevant tables
   - Verify that the appropriate events (INSERT, UPDATE) are enabled

2. **Check Network Connection**:
   - Open your browser's developer tools
   - Look for WebSocket connections to Supabase
   - Verify if there are any connection errors

3. **Check Database Triggers**:
   - Some custom triggers can interfere with Realtime
   - Check if you have any triggers on the tables that might be causing issues

4. **Check Client Configuration**:
   - Ensure your client is correctly subscribing to the right channels
   - Check that your filter conditions are correct

5. **Restart Realtime Service**:
   - In some cases, restarting the Realtime service in Supabase can help
   - This can be done in the Supabase Dashboard under Database → Replication → Realtime

## Additional Resources

- [Supabase Realtime Documentation](https://supabase.com/docs/guides/realtime)
- [Supabase JavaScript Client Realtime Guide](https://supabase.com/docs/reference/javascript/subscribe) 