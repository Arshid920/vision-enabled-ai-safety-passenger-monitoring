from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # 'admin' or 'driver'
    
    # Driver specific details
    full_name = Column(String, nullable=True)
    license_number = Column(String, unique=True, nullable=True)
    boat_number = Column(String, nullable=True)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = deactivated

    trips = relationship("Trip", back_populates="driver")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    safety_status = Column(String, default="Safe")  # Safe, Caution, Unsafe
    max_passenger_count = Column(Integer, default=0)
    alert_count = Column(Integer, default=0)

    driver = relationship("User", back_populates="trips")
    logs = relationship("SafetyLog", back_populates="trip")

class SafetyLog(Base):
    __tablename__ = "safety_logs"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    prediction = Column(String) # Safe, Caution, Unsafe
    passenger_count = Column(Integer)
    violations = Column(String) # JSON string or comma-separated list of violations

    trip = relationship("Trip", back_populates="logs")
