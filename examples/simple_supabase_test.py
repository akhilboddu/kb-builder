#!/usr/bin/env python3
"""
Simple test script for Supabase connection.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

print(f"Testing connection to Supabase at {SUPABASE_URL}")
print(f"Using service role key: {SUPABASE_KEY[:10]}...{SUPABASE_KEY[-10:]}")

# Create Supabase client with service role key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try fetching some basic information 
try:
    # Simple test query
    response = supabase.auth.get_user(SUPABASE_ANON_KEY)
    print("✅ Successfully connected to Supabase!")
    print("User auth test:", response)
    
    # Test database access
    try:
        # Check if the auth schema exists (should always be there in Supabase)
        response = supabase.rpc('get_schema_version').execute()
        print("✅ Successfully queried database!")
        print("Schema version:", response)
    except Exception as e:
        print("❌ Error querying database:", str(e))
        
except Exception as e:
    print("❌ Error connecting to Supabase:", str(e))
    print("Please check your SUPABASE_URL and SUPABASE_KEY in the .env file")
    
print("\nIf you're seeing errors, please follow the MANUAL_SETUP.md guide") 