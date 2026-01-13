import sys
import os

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.google_sheets import fetch_practice_data
from dotenv import load_dotenv
import json

# Load env vars
load_dotenv()

try:
    print("Fetching data for 'C2_Writing_Correct spelling'...")
    data = fetch_practice_data("C2_Writing_Correct spelling")
    if data:
        print("\n--- FIRST ITEM KEYS ---")
        print(list(data[0].keys()))
        print("\n--- FIRST ITEM CONTENT ---")
        print(json.dumps(data[0], indent=2))
    else:
        print("No data found")
except Exception as e:
    print(f"Error: {e}")
