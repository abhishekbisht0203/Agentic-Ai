from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    exit(1)

# Create the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test the connection by listing tables (querying a known table or running a simple query)
try:
    # Example: try to select from a table (replace 'your_table' with an actual table name)
    # response = supabase.table("your_table").select("*").limit(1).execute()
    # print(f"Connection successful! Found {len(response.data)} rows.")

    # Or just test the auth service as a connectivity check
    session = supabase.auth.get_session()
    print("Connection successful! Supabase client is working.")
except Exception as e:
    print(f"Failed to connect: {e}")
