from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()  # loads .env into environment variables

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL or key not found in environment variables!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)