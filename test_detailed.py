import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv("SERVICENOW_INSTANCE")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

print(f"Testing connection to: {INSTANCE}")
print(f"Username: {USERNAME}")
print(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}")
print()

try:
    response = requests.get(
        f"{INSTANCE}/api/now/table/sys_user",
        params={"sysparm_limit": 1},
        auth=(USERNAME, PASSWORD),
        headers={"Accept": "application/json"},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("âœ… Connection successful!")
        print("Response preview:", response.json())
    elif response.status_code == 401:
        print("âŒ Authentication failed - check username/password")
    elif response.status_code == 403:
        print("âŒ Forbidden - check user permissions")
    else:
        print(f"âŒ Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("âŒ Request timed out after 30 seconds")
    print("   - Instance may be hibernated/suspended")
    print("   - Check if VPN is required")
    print("   - Try accessing instance in browser first")
except requests.exceptions.ConnectionError as e:
    print(f"âŒ Connection error: {e}")
    print("   - Verify instance URL")
    print("   - Check network connection")
except Exception as e:
    print(f"âŒ Unexpected error: {e}")