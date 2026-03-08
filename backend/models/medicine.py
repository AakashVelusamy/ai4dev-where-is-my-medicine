from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, DECIMAL, text
from db.database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, index=True, nullable=False)
    composition = Column(String)
    uses = Column(String)
    side_effects = Column(String)
    manufacturer = Column(String)
    image_url = Column(String)
    excellent_review_percent = Column(DECIMAL, default=0)
    average_review_percent = Column(DECIMAL, default=0)
    poor_review_percent = Column(DECIMAL, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    phone_number = Column(String)
    opening_time = Column(String, server_default='08:00')
    closing_time = Column(String, server_default='22:00')
    rating = Column(DECIMAL)

class PharmacyInventory(Base):
    __tablename__ = "pharmacy_inventory"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer)
    medicine_id = Column(Integer)
    stock_quantity = Column(Integer, default=0)
    price = Column(DECIMAL)
    availability_status = Column(String, default="out_of_stock")
