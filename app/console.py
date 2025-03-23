import os
import random
import time
from pymongo import MongoClient
from datetime import datetime
from faker import Faker


fake = Faker()


mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.get_default_database()
collection = db["fingerprints"]


resolutions = [(1920, 1080), (1366, 768), (1440, 900), (2560, 1440), (1280, 720)]
timezones = ["Europe/London", "America/New_York", "Asia/Tokyo", "Australia/Sydney", "Europe/Paris"]
languages = ["en-GB", "en-US", "ja-JP", "fr-FR", "es-ES"]
countries = ["GB", "US", "JP", "AU", "FR"]
asns = ["AS5089", "AS15169", "AS4134", "AS4808", "AS7922"]


personas = {
    "Unknown": {
        "userId": "c6db552f-a2e6-453f-8e5d-03981470fee8",
        "traits": {
            "headless": random.choice([True, False]),
            "cookiesEnabled": random.choice([True, False]),
            "pageLoadTime": lambda: round(random.uniform(200, 500), 2),  # Mixed load times
            "events": {"mousemove": random.choice([True, False]), "keydown": random.choice([True, False]),
                       "scroll": random.choice([True, False]), "copy": random.choice([True, False])},
            "ipDetails": {"is_datacenter": random.choice([True, False])},
            "hardware": {"cpuCores": random.choice([4, 8, 12]), "deviceMemory": random.choice([8, 16, 32])}
        }
    },
    "Square": {
        "userId": "a3d38c70-f3ca-4065-acdc-9018c92dfd85",
        "traits": {
            "headless": False,
            "cookiesEnabled": True,
            "pageLoadTime": lambda: round(random.uniform(400, 800), 2),  # Slow load times
            "events": {"mousemove": True, "keydown": True, "scroll": True, "copy": True},
            "ipDetails": {"is_datacenter": False},
            "hardware": {"cpuCores": 4, "deviceMemory": 8}
        }
    },
    "Casual Punter": {
        "userId": "71b00e76-dbe8-46b5-a7ae-4685b7b09538",
        "traits": {
            "headless": False,
            "cookiesEnabled": True,
            "pageLoadTime": lambda: round(random.uniform(300, 600), 2),  # Average load times
            "events": {"mousemove": True, "keydown": True, "scroll": True, "copy": False},
            "ipDetails": {"is_datacenter": False},
            "hardware": {"cpuCores": 6, "deviceMemory": 16}
        }
    },
    "Sharp": {
        "userId": "961fe5a8-c873-4b7f-832f-9b265e7a1a83",
        "traits": {
            "headless": True,
            "cookiesEnabled": False,
            "pageLoadTime": lambda: round(random.uniform(50, 200), 2),  # Very fast load times
            "events": {"mousemove": False, "keydown": False, "scroll": False, "copy": False},
            "ipDetails": {"is_datacenter": True},
            "hardware": {"cpuCores": 16, "deviceMemory": 64}
        }
    },
    "Semi Sharp": {
        "userId": "7a224b58-371d-44df-afee-fa19607dd59a",
        "traits": {
            "headless": True,
            "cookiesEnabled": False,
            "pageLoadTime": lambda: round(random.uniform(150, 300), 2),  # Faster load times
            "events": {"mousemove": False, "keydown": True, "scroll": False, "copy": False},
            "ipDetails": {"is_datacenter": True},
            "hardware": {"cpuCores": 12, "deviceMemory": 32}
        }
    },
}


def generate_user_activity(persona_name):
    """Generate user activity data based on persona."""
    persona = personas[persona_name]
    traits = persona["traits"]
    screen_width, screen_height = random.choice(resolutions)
    timestamp = int(time.time() * 1000)  # Current time in milliseconds

    return {
        "userId": persona["userId"],
        "timestamp": timestamp,
        "fingerprint": f"Mozilla/5.0::{random.choice(languages)}::{screen_width}x{screen_height}::{traits['hardware']['cpuCores']}::{random.choice(timezones)}",
        "timezone": random.choice(timezones),
        "language": random.choice(languages),
        "headless": traits["headless"],
        "cookiesEnabled": traits["cookiesEnabled"],
        "pageLoadTime": traits["pageLoadTime"](),
        "events": traits["events"],
        "ipDetails": {
            "country": random.choice(countries),
            "asn": random.choice(asns),
            "is_datacenter": traits["ipDetails"]["is_datacenter"]
        },
        "screen": {
            "width": screen_width,
            "height": screen_height,
            "devicePixelRatio": random.choice([1, 1.5, 2]),
            "orientation": random.choice(["landscape-primary", "portrait-primary"])
        },
        "viewport": {
            "innerWidth": screen_width - random.randint(100, 400),
            "innerHeight": screen_height - random.randint(100, 400)
        },
        "battery": {
            "level": round(random.uniform(0.1, 1.0), 2),
            "charging": random.choice([True, False]),
            "chargingTime": random.randint(0, 3600) if random.choice([True, False]) else 0
        },
        "hardware": {
            "cpuCores": traits["hardware"]["cpuCores"],
            "deviceMemory": traits["hardware"]["deviceMemory"]
        },
        "serverTimestamp": datetime.utcnow().isoformat()
    }


def run_indefinite_seeding():
    """Run indefinitely, inserting one record at a time for each persona."""
    print("Starting indefinite seeding process... Press Ctrl+C to stop.")

    while True:
        for persona_name in personas.keys():
            try:
                # Generate and insert one record
                record = generate_user_activity(persona_name)
                result = collection.insert_one(record)

                # Print the record with persona name and inserted ID
                print(f"Inserted record for '{persona_name}' (ID: {result.inserted_id}):")
                print(record)
                print("-" * 50)

                # Small delay to avoid overwhelming the database
                time.sleep(1)

            except Exception as e:
                print(f"Error inserting record for '{persona_name}': {str(e)}")

        # Optional: Add a longer delay between full cycles if needed
        # time.sleep(5)


if __name__ == "__main__":
    # Clear existing data (optional, comment out if not desired)
    collection.delete_many({})
    print("Cleared existing data in collection.")

    # Run indefinite seeding
    run_indefinite_seeding()
