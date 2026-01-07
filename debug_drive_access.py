
import os
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from app.services.google_auth import get_credentials

# Load env vars
load_dotenv()

def debug_permissions():
    print("--- Google Drive Permission Debugger ---")
    
    # 1. Check Env Var
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    print(f"Target Folder ID from .env: {folder_id}")
    
    if not folder_id:
        print("ERROR: GOOGLE_DRIVE_FOLDER_ID is missing in .env")
        return

    # 2. Get Credentials
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        print("Successfully authenticated with Service Account.")
        
        # Get Service Account Email to confirm identity
        about = service.about().get(fields="user(emailAddress)").execute()
        email = about['user']['emailAddress']
        print(f"Service Account Email: {email}")
        print("(Make sure THIS email is added to your folder's 'Share' list)")
        
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return

    # 3. Check Specific Folder Access
    print(f"\nChecking access to target folder ({folder_id})...")
    try:
        folder = service.files().get(fileId=folder_id, fields="id, name, capabilities").execute()
        print(f"SUCCESS! Found folder: '{folder['name']}'")
        print(f"Can listy children? {folder['capabilities'].get('canListChildren')}")
    except Exception as e:
        print(f"FAILURE: Could not access folder. Reason: {e}")
        print("Likely cause: The folder is not shared with the service account email above.")

    # 4. List ANYTHING we can see
    print("\nListing ALL files/folders visible to this Service Account (limit 20):")
    try:
        results = service.files().list(
            pageSize=20,
            fields="files(id, name, mimeType, parents)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            print("No files found at all. The Service Account sees an empty Drive.")
        else:
            for f in files:
                print(f"- Name: {f['name']} | ID: {f['id']} | Type: {f['mimeType']}")
                if 'parents' in f:
                    print(f"  Parent IDs: {f['parents']}")
                    
    except Exception as e:
        print(f"Error listing files: {e}")

if __name__ == "__main__":
    # Add project root to path so we can import app modules if run from inside api folder
    sys.path.append(os.getcwd())
    debug_permissions()
