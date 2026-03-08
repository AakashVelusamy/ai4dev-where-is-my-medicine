from sqlalchemy.orm import Session
from models.medicine import Pharmacy, PharmacyInventory, Medicine
from sqlalchemy import text
from typing import List, Dict

class PharmacyService:
    def __init__(self, db: Session):
        self.db = db

    async def get_nearby_pharmacies(self, lat: float, lon: float, medicine_id: int, radius_km: int = 5):
        # Query using PostGIS for radial geospatial search
        # Join with inventory and medicine information
        
        # In this demo, we use a SQL query string to run the ST_DWithin search with PostGIS
        # Note: 4326 is WGS-84 coordinate system (lat/lon)
        
        query = text("""
            SELECT p.id, p.pharmacy_name, p.address, p.latitude, p.longitude, p.phone_number, p.rating, 
                   inv.stock_quantity, inv.price, 
                   ST_Distance(p.location, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) / 1000 as distance_km
            FROM pharmacies p
            JOIN pharmacy_inventory inv ON p.id = inv.pharmacy_id
            WHERE inv.medicine_id = :med_id
              AND inv.stock_quantity > 0
              AND ST_DWithin(p.location, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography, :radius_meters)
            ORDER BY distance_km ASC
            LIMIT 10;
        """)
        
        # radius_meters = radius_km * 1000
        result = self.db.execute(query, {
            "lat": lat, 
            "lon": lon, 
            "med_id": medicine_id, 
            "radius_meters": radius_km * 1000
        })
        
        pharmacies = []
        for row in result:
            pharmacies.append({
                "id": row.id,
                "name": row.pharmacy_name,
                "address": row.address,
                "lat": row.latitude,
                "lon": row.longitude,
                "phone": row.phone_number,
                "rating": float(row.rating),
                "stock": row.stock_quantity,
                "price": float(row.price),
                "distance_km": round(row.distance_km, 2)
            })
            
        return pharmacies

    async def get_substitutes(self, medicine_id: int):
        # Step 1: Get composition of original medicine
        original = self.db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if not original or not original.composition:
            return []
            
        # Step 2: Find all medicines with the same composition (excluding self)
        # We use strict equality for demo, in real life maybe fuzzy composition match?
        subs = self.db.query(Medicine).filter(
            Medicine.composition == original.composition,
            Medicine.id != medicine_id
        ).limit(5).all()
        
        results = []
        for s in subs:
            results.append({
                "id": s.id,
                "name": s.medicine_name,
                "composition": s.composition,
                "uses": s.uses,
                "manufacturer": s.manufacturer
            })
            
        return results
