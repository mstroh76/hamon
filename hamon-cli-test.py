import configparser
import os
import sys
import requests
import json

# Configuration file locations, first match wins (see hamon.conf.example)
CONFIG_PATHS = [
    os.path.expanduser("~/.config/hamon/hamon.conf"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hamon.conf"),
    "/etc/hamon.conf",
]

# Optional: pass the configuration file as first argument
if len(sys.argv) > 1:
    config_path = sys.argv[1]
else:
    config_path = next((p for p in CONFIG_PATHS if os.path.isfile(p)), None)

if config_path is None or not os.path.isfile(config_path):
    print("ERROR: No configuration file found. Copy hamon.conf.example to one of:")
    for p in CONFIG_PATHS:
        print("  " + p)
    exit(1)

config = configparser.ConfigParser(interpolation=None)
config.read(config_path, encoding="utf-8")

HA_URL = config.get("homeassistant", "url", fallback="").rstrip("/")
HA_TOKEN = config.get("homeassistant", "token", fallback="")
ENTITY_IDS = list(config["entities"]) if config.has_section("entities") else []

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

print("=== Home Assistant API Test ===")
print(f"Config: {config_path}")
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
