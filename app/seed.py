import random
import time
import csv
from datetime import datetime
from faker import Faker


fake = Faker()


resolutions = [(1920, 1080), (1366, 768), (1440, 900), (2560, 1440), (1280, 720)]
timezones = ["Europe/London", "America/New_York", "Asia/Tokyo", "Australia/Sydney", "Europe/Paris"]
languages = ["en-GB", "en-US", "ja-JP", "fr-FR", "es-ES"]
countries = ["GB", "US", "JP", "AU", "FR"]
asns = ["AS5089", "AS15169", "AS4134", "AS4808", "AS7922"]


def determine_sharpness(record):
    """Determine if a user is a sharp (1) or square (0) bettor based on their specs."""
    score = 0

    # Higher CPU cores = more likely sharp (max 32)
    if record["hardware_cpuCores"] >= 16:
        score += 2
    elif record["hardware_cpuCores"] >= 8:
        score += 1

    # Higher device memory = more likely sharp (max 128)
    if record["hardware_deviceMemory"] >= 64:
        score += 2
    elif record["hardware_deviceMemory"] >= 32:
        score += 1

    # Larger screen area = more likely sharp
    screen_area = record["screen_width"] * record["screen_height"]
    if screen_area >= 2560 * 1440:  # High-end resolution
        score += 2
    elif screen_area >= 1920 * 1080:  # Standard HD
        score += 1

    # Higher battery level = more likely sharp (prepared user)
    if record["battery_level"] >= 0.75:
        score += 1
    elif record["battery_level"] >= 0.5:
        score += 0.5

    # Higher devicePixelRatio = more likely sharp (better display)
    if record["screen_devicePixelRatio"] >= 2:
        score += 1

    # Threshold: Score >= 4 means sharp bettor
    return 1 if score >= 4 else 0


def generate_random_user_activity():
    """Generate randomized user activity data with target label."""
    screen_width, screen_height = random.choice(resolutions)
    timestamp = int(time.time() * 1000)
    cpu_cores = random.choice([2, 4, 6, 8, 12, 16, 24, 32])
    device_memory = random.choice([4, 8, 16, 32, 64, 128])

    record = {
        "userId": fake.uuid4(),
        "timestamp": timestamp,
        "timezone": random.choice(timezones),
        "language": random.choice(languages),
        "headless": random.choice([True, False]),
        "cookiesEnabled": random.choice([True, False]),
        "pageLoadTime": round(random.uniform(50, 1000), 2),
        "event_mousemove": random.choice([True, False]),
        "event_keydown": random.choice([True, False]),
        "event_scroll": random.choice([True, False]),
        "event_copy": random.choice([True, False]),
        "ip_country": random.choice(countries),
        "ip_asn": random.choice(asns),
        "ip_is_datacenter": random.choice([True, False]),
        "screen_width": screen_width,
        "screen_height": screen_height,
        "screen_devicePixelRatio": random.choice([1, 1.5, 2, 2.5, 3]),
        "screen_orientation": random.choice(["landscape-primary", "portrait-primary"]),
        "viewport_innerWidth": screen_width - random.randint(50, 400),
        "viewport_innerHeight": screen_height - random.randint(50, 400),
        "battery_level": round(random.uniform(0.05, 1.0), 2),
        "battery_charging": random.choice([True, False]),
        "battery_chargingTime": random.randint(0, 7200) if random.choice([True, False]) else 0,
        "hardware_cpuCores": cpu_cores,
        "hardware_deviceMemory": device_memory,
        "serverTimestamp": datetime.utcnow().isoformat()
    }

    # Add target based on sharpness
    record["target"] = determine_sharpness(record)
    return record


def generate_csv_dataset(num_records=500000, output_file="user_activity_dataset.csv"):
    """Generate a CSV dataset with random user activities and target labels."""
    # Define CSV headers with target added
    fieldnames = [
        "userId", "timestamp", "timezone", "language", "headless", "cookiesEnabled",
        "pageLoadTime", "event_mousemove", "event_keydown", "event_scroll", "event_copy",
        "ip_country", "ip_asn", "ip_is_datacenter", "screen_width", "screen_height",
        "screen_devicePixelRatio", "screen_orientation", "viewport_innerWidth", "viewport_innerHeight",
        "battery_level", "battery_charging", "battery_chargingTime", "hardware_cpuCores",
        "hardware_deviceMemory", "serverTimestamp", "target"
    ]

    # Generate records
    print(f"Generating {num_records} records...")
    records = []
    start_time = time.time()

    for i in range(num_records):
        record = generate_random_user_activity()
        records.append(record)

        # Progress update every 50,000 records
        if (i + 1) % 50000 == 0:
            elapsed = time.time() - start_time
            print(f"Generated {i + 1} records ({(i + 1) / num_records * 100:.1f}%) in {elapsed:.1f} seconds")

    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    total_time = time.time() - start_time
    print(f"Generated CSV dataset with {num_records} records in '{output_file}' in {total_time:.1f} seconds")


if __name__ == "__main__":
    # Generate CSV with 500,000 random records
    generate_csv_dataset(num_records=500000, output_file="data/user_activity_dataset.csv")
