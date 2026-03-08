-- =========================================
-- 1. Enable Required Extensions
-- =========================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================================
-- 2. Medicines Table
-- Stores the medicine knowledge base (~11k medicines)
-- =========================================

CREATE TABLE IF NOT EXISTS medicines (
    id SERIAL PRIMARY KEY,

    medicine_name TEXT NOT NULL,
    composition TEXT,
    uses TEXT,
    side_effects TEXT,
    manufacturer TEXT,
    image_url TEXT,

    excellent_review_percent DECIMAL DEFAULT 0,
    average_review_percent DECIMAL DEFAULT 0,
    poor_review_percent DECIMAL DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- 3. Pharmacies Table
-- Stores pharmacy locations
-- =========================================

CREATE TABLE IF NOT EXISTS pharmacies (
    id SERIAL PRIMARY KEY,

    pharmacy_name TEXT NOT NULL,
    address TEXT,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    -- PostGIS geography column for distance queries
    location GEOGRAPHY(POINT, 4326),

    phone_number TEXT,

    opening_time TIME DEFAULT '08:00',
    closing_time TIME DEFAULT '22:00',

    rating DECIMAL CHECK (rating >= 0 AND rating <= 5),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- 4. Pharmacy Inventory Table
-- Connects pharmacies with medicines
-- =========================================

CREATE TABLE IF NOT EXISTS pharmacy_inventory (
    id SERIAL PRIMARY KEY,

    pharmacy_id INTEGER NOT NULL
        REFERENCES pharmacies(id)
        ON DELETE CASCADE,

    medicine_id INTEGER NOT NULL
        REFERENCES medicines(id)
        ON DELETE CASCADE,

    stock_quantity INTEGER DEFAULT 0,

    price DECIMAL,

    availability_status TEXT DEFAULT 'out_of_stock',

    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate medicine rows per pharmacy
    UNIQUE (pharmacy_id, medicine_id)
);

-- =========================================
-- 5. Performance Indexes
-- =========================================

-- Fast fuzzy medicine search
CREATE INDEX IF NOT EXISTS idx_medicines_name
ON medicines
USING GIN (medicine_name gin_trgm_ops);

-- Fast geospatial radius search
CREATE INDEX IF NOT EXISTS idx_pharmacies_location
ON pharmacies
USING GIST (location);

-- Fast inventory filtering by medicine
CREATE INDEX IF NOT EXISTS idx_inventory_medicine
ON pharmacy_inventory (medicine_id);

-- Fast join from pharmacy → inventory
CREATE INDEX IF NOT EXISTS idx_inventory_pharmacy
ON pharmacy_inventory (pharmacy_id);

-- Optional: faster filtering for available medicines
CREATE INDEX IF NOT EXISTS idx_inventory_stock
ON pharmacy_inventory (stock_quantity);

-- =========================================
-- 6. Trigger Function
-- Automatically convert lat/lon → PostGIS point
-- =========================================

CREATE OR REPLACE FUNCTION update_pharmacy_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location =
            ST_SetSRID(
                ST_MakePoint(NEW.longitude, NEW.latitude),
                4326
            );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- 7. Trigger
-- Runs whenever pharmacy coordinates change
-- =========================================

CREATE TRIGGER trg_update_pharmacy_location
BEFORE INSERT OR UPDATE ON pharmacies
FOR EACH ROW
EXECUTE FUNCTION update_pharmacy_location();