import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Look for .env in the root or in the backend folder
load_dotenv()
if not os.getenv("DATABASE_URL"):
    load_dotenv("backend/.env")

# -----------------------------
# CONFIGURATION
# -----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env file!")
    print("Example: DATABASE_URL=postgresql://postgres:your_password@db.pjyivmskjxshqxhkqxhp.supabase.co:5432/postgres")
    exit(1)

# Initialize SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def load_data_to_db():
    print("Reading CSV files from data folders...")

    # Load paths
    medicine_path = "backend/data/Medicine_Details.csv"
    pharmacy_path = "backend/data/pharmacies.csv"
    inventory_path = "backend/data/pharmacy_inventory.csv"

    # 1. READ & CLEAN MEDICINES
    medicine_df = pd.read_csv(medicine_path)
    # Map CSV column names to SQL table columns
    medicine_df.columns = [
        "medicine_name", "composition", "uses", "side_effects", 
        "image_url", "manufacturer", "excellent_review_percent", 
        "average_review_percent", "poor_review_percent"
    ]
    
    # 2. READ PHARMACIES & INVENTORY
    pharmacy_df = pd.read_csv(pharmacy_path)
    inventory_df = pd.read_csv(inventory_path)
    
    # 3. LOAD TO SUPABASE (APPEND MODE)
    print("Step 1/3: Loading Medicines Table (11k+ rows)...")
    medicine_df.to_sql("medicines", engine, if_exists="append", index=False)
    
    print("Step 2/3: Loading Pharmacies Table...")
    pharmacy_df.to_sql("pharmacies", engine, if_exists="append", index=False)
    
    print("Step 3/3: Loading Inventory Table (20k rows)...")
    inventory_df.to_sql("pharmacy_inventory", engine, if_exists="append", index=False)
    
    print("\n-------------------------------------------")
    print("Success! All data loaded to Supabase.")
    print("-------------------------------------------")

if __name__ == "__main__":
    load_data_to_db()
