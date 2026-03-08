import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker()

# -----------------------------
# USER PARAMETERS
# -----------------------------
NUM_PHARMACIES = 100
INVENTORY_PER_PHARMACY = 200

CENTER_LAT = 11.0283
CENTER_LON = 77.0273
RADIUS_KM = 5

# Path to the source medicine file
MEDICINE_FILE = "backend/data/Medicine_Details.csv"
# Output directory
OUTPUT_DIR = "backend/data"

def generate_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # -----------------------------
    # LOAD MEDICINE DATASET
    # -----------------------------
    if not os.path.exists(MEDICINE_FILE):
        print(f"Error: {MEDICINE_FILE} not found. Please ensure it exists in the root data folder.")
        return

    medicines = pd.read_csv(MEDICINE_FILE)
    medicines = medicines.reset_index(drop=True)
    medicines["medicine_id"] = medicines.index + 1

    # -----------------------------
    # GENERATE PHARMACIES
    # -----------------------------
    pharmacy_names = [
        "Apollo Pharmacy",
        "MedPlus",
        "NetMeds Partner",
        "WellCare Medical",
        "HealthFirst Pharmacy",
        "CityCare Medicals",
        "LifeLine Pharmacy",
        "Sri Medical Store",
        "CarePlus Pharmacy",
        "Community Pharmacy"
    ]

    pharmacies = []

    for i in range(NUM_PHARMACIES):
        # Accurate geographic offsets
        lat_offset = np.random.uniform(-RADIUS_KM, RADIUS_KM) / 111
        lon_offset = np.random.uniform(-RADIUS_KM, RADIUS_KM) / (111 * np.cos(np.radians(CENTER_LAT)))

        pharmacies.append({
            "id": i + 1,
            "pharmacy_name": random.choice(pharmacy_names) + f" #{i+1}",
            "address": fake.address().replace("\n", ", "),
            "latitude": CENTER_LAT + lat_offset,
            "longitude": CENTER_LON + lon_offset,
            "phone_number": fake.phone_number(),
            "opening_time": "08:00",
            "closing_time": "22:00",
            "rating": round(random.uniform(3.5, 5.0), 2)
        })

    pharmacies_df = pd.DataFrame(pharmacies)

    # -----------------------------
    # GENERATE INVENTORY
    # -----------------------------
    inventory = []
    inventory_id = 1

    for pharmacy_id in pharmacies_df["id"]:
        # Sample medicines without duplicates
        medicines_sample = medicines.sample(min(len(medicines), INVENTORY_PER_PHARMACY), replace=False)

        for _, med in medicines_sample.iterrows():
            stock = random.randint(0, 50)
            inventory.append({
                "id": inventory_id,
                "pharmacy_id": pharmacy_id,
                "medicine_id": med["medicine_id"],
                "stock_quantity": stock,
                "price": round(random.uniform(10, 500), 2),
                "availability_status": "in_stock" if stock > 0 else "out_of_stock",
                "last_updated": fake.date_time_this_year()
            })
            inventory_id += 1

    inventory_df = pd.DataFrame(inventory)

    # -----------------------------
    # SAVE CSV FILES
    # -----------------------------
    pharmacies_path = os.path.join(OUTPUT_DIR, "pharmacies.csv")
    inventory_path = os.path.join(OUTPUT_DIR, "pharmacy_inventory.csv")
    
    pharmacies_df.to_csv(pharmacies_path, index=False)
    inventory_df.to_csv(inventory_path, index=False)

    print(f"Generated pharmacies: {pharmacies_df.shape[0]} at {pharmacies_path}")
    print(f"Generated inventory: {inventory_df.shape[0]} at {inventory_path}")

if __name__ == "__main__":
    generate_data()
