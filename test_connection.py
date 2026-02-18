import os
import requests
from dotenv import load_dotenv

load_dotenv()

INSTANCE = os.getenv("SERVICENOW_INSTANCE")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

print(f"Testing connection to {INSTANCE}...")

response = requests.get(
    f"{INSTANCE}/api/now/table/syslog",
    params={"sysparm_limit": 1},
    auth=(USERNAME, PASSWORD),
    headers={"Accept": "application/json"}
)

print(f"Status code: {response.status_code}")

if response.status_code == 200:
    print("Connection successful!")
    result = response.json().get("result", [])
    if result:
        print(f"Sample log: {result[0].get('message', 'N/A')[:100]}...")
else:
    print(f"Error: {response.text}")
