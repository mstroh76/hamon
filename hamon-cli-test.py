mport requests
import json

# Home Assistant base URL
HA_URL = "http://192.168.0.236:8123"

# !!! IMPORTANT !!!
# Replace this token with your own long-lived access token from Home Assistant
HA_TOKEN = "REPLACE_ME_WITH_YOUR_TOKEN"

# List of entity IDs to display
# Replace all ENTITY_IDS with valid Home Assistant entity IDs
ENTITY_IDS = [
    "REPLACE.sensor_1", "REPLACE.sensor_2",
    "REPLACE.sensor_3", "REPLACE.sensor_4",
]

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

print("=== Home Assistant API Test ===")
print(f"Server: {HA_URL}")
print("Testing connection...\n")

# 1. Test: Check if API is reachable
try:
    r = requests.get(f"{HA_URL}/api/", headers=headers, timeout=5)
    print("API Response Code:", r.status_code)
    print("API Response Body:", r.text)
except Exception as e:
    print("ERROR: Unable to reach Home Assistant!")
    print(e)
    exit(1)

print("\n=== Testing Entities ===\n")

# 2. Test: Query each entity individually
for entity in ENTITY_IDS:
    print(f"Querying: {entity}")
    try:
        r = requests.get(f"{HA_URL}/api/states/{entity}", headers=headers, timeout=5)
        print("Status Code:", r.status_code)

        if r.status_code == 200:
            data = r.json()
            print("State:", data.get("state"))
            print("Attributes:", json.dumps(data.get("attributes", {}), indent=2))
        else:
            print("Response:", r.text)

    except Exception as e:
        print("ERROR while fetching entity!")
        print(e)

    print("-" * 40)
