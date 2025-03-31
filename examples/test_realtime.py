#!/usr/bin/env python3
"""
Test script for Supabase Realtime connection.
This script verifies that the Supabase Realtime functionality is properly set up.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in the .env file")
    sys.exit(1)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_colored(text, color):
    """Print colored text to terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

async def test_realtime_tables():
    """Test if tables exist and have the right structure."""
    print_colored("Testing database tables...", "blue")
    
    # Check conversations table
    try:
        response = supabase.table("conversations").select("*").limit(1).execute()
        print_colored("✓ Conversations table exists", "green")
    except Exception as e:
        print_colored(f"✗ Error accessing conversations table: {str(e)}", "red")
        return False

    # Check messages table
    try:
        response = supabase.table("messages").select("*").limit(1).execute()
        print_colored("✓ Messages table exists", "green")
    except Exception as e:
        print_colored(f"✗ Error accessing messages table: {str(e)}", "red")
        return False
    
    # Check handover_requests table
    try:
        response = supabase.table("handover_requests").select("*").limit(1).execute()
        print_colored("✓ Handover requests table exists", "green")
    except Exception as e:
        print_colored(f"✗ Error accessing handover_requests table: {str(e)}", "red")
        # This is not critical, so continue
    
    return True

async def test_realtime_subscription():
    """Test Supabase Realtime subscription."""
    print_colored("\nTesting Realtime subscription...", "blue")
    
    # Create a test conversation for this test
    conversation_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create a dictionary to track received events
    received_events = {
        "conversation_created": False,
        "message_received": False
    }
    
    # Create the channel
    channel_name = f"test-conversation:{conversation_id}"
    channel = supabase.channel(channel_name)
    
    # Message handler
    def handle_message_insert(payload):
        print_colored(f"✓ Received message: {payload['new']['content']}", "green")
        received_events["message_received"] = True
        
    # Set up the subscription for messages
    channel.on(
        "postgres_changes",
        event="INSERT",
        schema="public",
        table="messages",
        filter=f"conversation_id=eq.{conversation_id}",
        callback=handle_message_insert
    )
    
    # Conversation handler
    def handle_conversation_insert(payload):
        print_colored("✓ Received conversation created event", "green")
        received_events["conversation_created"] = True
        
    # Set up the subscription for conversations
    channel.on(
        "postgres_changes",
        event="INSERT",
        schema="public",
        table="conversations",
        filter=f"id=eq.{conversation_id}",
        callback=handle_conversation_insert
    )
    
    # Subscribe
    channel.subscribe()
    print_colored("- Subscribed to channel", "cyan")
    
    # Wait a moment for the subscription to be established
    await asyncio.sleep(1)
    
    # Insert the test conversation
    try:
        print_colored("- Creating test conversation...", "cyan")
        conversation_data = {
            "id": conversation_id,
            "bot_id": "test-bot",
            "status": "open",
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        response = supabase.table("conversations").insert(conversation_data).execute()
        print_colored("- Conversation created", "cyan")
    except Exception as e:
        print_colored(f"✗ Error creating test conversation: {str(e)}", "red")
        channel.unsubscribe()
        return False
    
    # Wait for the event to be received
    print_colored("- Waiting for conversation event...", "cyan")
    await asyncio.sleep(2)
    
    # Insert a test message
    try:
        print_colored("- Creating test message...", "cyan")
        message_data = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "sender_type": "user",
            "content": "This is a test message for Realtime",
            "timestamp": datetime.now().isoformat()
        }
        
        response = supabase.table("messages").insert(message_data).execute()
        print_colored("- Message created", "cyan")
    except Exception as e:
        print_colored(f"✗ Error creating test message: {str(e)}", "red")
        channel.unsubscribe()
        return False
    
    # Wait for the events to be received
    print_colored("- Waiting for message event...", "cyan")
    await asyncio.sleep(2)
    
    # Unsubscribe
    channel.unsubscribe()
    print_colored("- Unsubscribed from channel", "cyan")
    
    # Check if all events were received
    if received_events["conversation_created"] and received_events["message_received"]:
        print_colored("✓ Realtime subscription test successful!", "green")
        return True
    else:
        print_colored("✗ Some events were not received:", "red")
        for event, received in received_events.items():
            status = "Received" if received else "Not received"
            print_colored(f"  - {event}: {status}", "yellow")
        return False

async def main():
    """Main test function."""
    print_colored("\n====== SUPABASE REALTIME TEST ======\n", "magenta")
    
    print_colored(f"Supabase URL: {SUPABASE_URL}", "cyan")
    
    # Test tables
    tables_ok = await test_realtime_tables()
    if not tables_ok:
        print_colored("\n✗ Table test failed. Please check your database setup.", "red")
        sys.exit(1)
    
    # Test Realtime subscription
    subscription_ok = await test_realtime_subscription()
    if not subscription_ok:
        print_colored("\n✗ Realtime subscription test failed.", "red")
        print_colored("Please check if Realtime is enabled in the Supabase Dashboard:", "yellow")
        print_colored("1. Go to Database → Replication → Realtime", "yellow")
        print_colored("2. Ensure conversations and messages tables have Realtime enabled", "yellow")
        print_colored("3. Check that INSERT events are enabled", "yellow")
        sys.exit(1)
    
    print_colored("\n====== ALL TESTS PASSED ======", "green")
    print_colored("Supabase Realtime is properly configured!", "green")

if __name__ == "__main__":
    asyncio.run(main()) 