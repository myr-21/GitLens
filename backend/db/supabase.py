import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: SUPABASE_URL or SUPABASE_KEY is missing from environment variables.")

# Initialize the Supabase Client
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")

def get_supabase_client() -> Client:
    """Returns the initialized Supabase client."""
    global supabase
    if supabase is None:
        # Retry initialization in case env variables were loaded dynamically
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            supabase = create_client(url, key)
        else:
            raise ValueError("Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY.")
    return supabase
