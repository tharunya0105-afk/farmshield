"""
FarmShield - Database Models & Setup
Detect Early. Predict Spread. Protect Precisely.
"""
import os, json, random, string, datetime
from datetime import timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

if os.getenv("RENDER"):
    DATABASE_URL = "sqlite:////var/data/farmshield.db"
elif os.getenv("VERCEL"):
    DATABASE_URL = "sqlite:////tmp/farmshield.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmshield.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── MODELS ────────────────────────────────────────────────
class Farmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(20), nullable=False)
    village = Column(String(100))
    district = Column(String(100), default="Tiruchirappalli")
    state = Column(String(50), default="Tamil Nadu")
    language = Column(String(10), default="en")
    main_crop = Column(String(50), default="Cotton")
    farm_size_acres = Column(Float, default=42.0)
    latitude = Column(Float, default=10.7905)
    longitude = Column(Float, default=78.7047)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    farms = relationship("Farm", back_populates="farmer")

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    name = Column(String(100))
    total_area_acres = Column(Float, default=42.0)
    latitude = Column(Float, default=10.7905)
    longitude = Column(Float, default=78.7047)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    farmer = relationship("Farmer", back_populates="farms")
    fields = relationship("Field", back_populates="farm")

class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    name = Column(String(100))
    crop = Column(String(50), default="Cotton")
    area_acres = Column(Float)
    growth_stage = Column(String(50), default="Flowering")
    health_status = Column(String(20), default="healthy")
    latitude = Column(Float)
    longitude = Column(Float)
    polygon = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    farm = relationship("Farm", back_populates="fields")
    detections = relationship("Detection", back_populates="field")

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True)
    crop = Column(String(50))
    possible_pest = Column(String(100))
    confidence = Column(Float)
    severity = Column(String(20), default="HIGH")
    affected_area_acres = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    photo_path = Column(String(255))
    mode = Column(String(50), default="DEMO_SIMULATION")
    status = Column(String(20), default="detected")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    field = relationship("Field", back_populates="detections")
    outbreak = relationship("Outbreak", back_populates="detection", uselist=False)

class Outbreak(Base):
    __tablename__ = "outbreaks"
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    crop = Column(String(50))
    pest = Column(String(100))
    severity = Column(String(20))
    affected_area_acres = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    risk_level = Column(String(10), default="HIGH")
    status = Column(String(30), default="active")
    containment_radius = Column(Float, default=6.2)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    detection = relationship("Detection", back_populates="outbreak")
    predictions = relationship("SpreadPrediction", back_populates="outbreak")
    missions = relationship("Mission", back_populates="outbreak")

class SpreadPrediction(Base):
    __tablename__ = "spread_predictions"
    id = Column(Integer, primary_key=True, index=True)
    outbreak_id = Column(Integer, ForeignKey("outbreaks.id"))
    hours = Column(Integer)
    predicted_area_acres = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    outbreak = relationship("Outbreak", back_populates="predictions")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    agent_type = Column(String(20), default="DRONE")
    status = Column(String(20), default="AVAILABLE")
    battery_percent = Column(Float, default=100.0)
    payload_capacity_l = Column(Float, default=5.0)
    latitude = Column(Float)
    longitude = Column(Float)
    base_latitude = Column(Float)
    base_longitude = Column(Float)
    speed_kmh = Column(Float, default=30.0)
    treatment_compatibility = Column(JSON, default=["Cotton","Rice","Wheat"])
    missions_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    missions = relationship("Mission", back_populates="agent")

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, index=True)
    mission_code = Column(String(20), unique=True)
    outbreak_id = Column(Integer, ForeignKey("outbreaks.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    target_area_acres = Column(Float)
    estimated_chemical_l = Column(Float)
    precision_chemical_l = Column(Float)
    status = Column(String(30), default="created")
    eta_minutes = Column(Float)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    outbreak = relationship("Outbreak", back_populates="missions")
    agent = relationship("Agent", back_populates="missions")
    treatments = relationship("Treatment", back_populates="mission")

class Treatment(Base):
    __tablename__ = "treatments"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    type = Column(String(30), default="precision_spray")
    target_area_acres = Column(Float)
    chemical_volume_l = Column(Float)
    estimated_conventional_l = Column(Float)
    savings_percent = Column(Float)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    mission = relationship("Mission", back_populates="treatments")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    title = Column(String(200))
    message = Column(Text)
    notification_type = Column(String(30), default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EventLog(Base):
    __tablename__ = "event_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100))
    message = Column(Text)
    event_type = Column(String(50))
    severity = Column(String(20), default="info")
    related_outbreak_id = Column(Integer, nullable=True)
    related_mission_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    temperature_c = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_kmh = Column(Float)
    rain_probability = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExpertReview(Base):
    __tablename__ = "expert_reviews"
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    status = Column(String(20), default="pending")
    reviewer_name = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ─── MISSION STATE MACHINE ─────────────────────────────────
MISSION_VALID_TRANSITIONS = {
    "created": ["dispatched"],
    "dispatched": ["arrived"],
    "arrived": ["treating"],
    "treating": ["completed"],
}

def validate_mission_transition(current: str, target: str) -> bool:
    """Returns True if the transition from current state to target state is valid."""
    allowed = MISSION_VALID_TRANSITIONS.get(current, [])
    return target in allowed

# ─── DEMO CONSTANTS (single source of truth) ───────────────
DEMO_PEST = "Bollworm"
DEMO_CROP = "Cotton"
DEMO_CONFIDENCE = 0.94
DEMO_SEVERITY = "HIGH"
DEMO_AFFECTED_ACRES = 2.1
DEMO_LATITUDE = 10.8790
DEMO_LONGITUDE = 78.710
DEMO_FIELD_ID = 3
DEMO_PREDICTIONS = [(0, 2.1), (2, 3.2), (6, 5.5), (12, 8.7), (24, 14.2)]

# ─── SEED DATA ─────────────────────────────────────────────
def generate_id(prefix=""):
    return f"{prefix}-{''.join(random.choices(string.digits, k=6))}"

def seed_data(db):
    if db.query(Farmer).count() > 0:
        return

    # Farmers
    farmers = [
        Farmer(name="Ramasamy K", mobile="9876543210", village="Lalgudi", district="Tiruchirappalli", state="Tamil Nadu", language="ta", main_crop="Cotton", farm_size_acres=42, latitude=10.8750, longitude=78.8250),
        Farmer(name="Suresh Babu", mobile="9876543211", village="Musiri", district="Tiruchirappalli", state="Tamil Nadu", language="ta", main_crop="Rice", farm_size_acres=28, latitude=10.8500, longitude=78.6200),
        Farmer(name="Lakshmi Devi", mobile="9876543212", village="Manapparai", district="Tiruchirappalli", state="Tamil Nadu", language="hi", main_crop="Chilli", farm_size_acres=15, latitude=10.6090, longitude=78.5290),
        Farmer(name="Murugan S", mobile="9876543213", village="Thuraiyur", district="Tiruchirappalli", state="Tamil Nadu", language="ta", main_crop="Groundnut", farm_size_acres=20, latitude=10.9250, longitude=78.6270),
        Farmer(name="Anand Raj", mobile="9876543214", village="Ariyalur", district="Ariyalur", state="Tamil Nadu", language="ta", main_crop="Sugarcane", farm_size_acres=35, latitude=11.1370, longitude=79.0720),
    ]
    db.add_all(farmers)
    db.flush()

    # Farms & Fields
    field_data = [
        ("FarmShield Demo Farm", 0, "North Cotton Block", "Cotton", 12, "Flowering", "healthy", 10.8790, 78.8230, [[10.8820, 78.8200], [10.8820, 78.8270], [10.8760, 78.8270], [10.8760, 78.8200]]),
        ("FarmShield Demo Farm", 0, "South Cotton Block", "Cotton", 15, "Flowering", "healthy", 10.8720, 78.8220, [[10.8750, 78.8190], [10.8750, 78.8260], [10.8690, 78.8260], [10.8690, 78.8190]]),
        ("FarmShield Demo Farm", 0, "East Mixed Plot", "Cotton", 15, "Boll Formation", "stressed", 10.8740, 78.8290, [[10.8770, 78.8260], [10.8770, 78.8330], [10.8710, 78.8330], [10.8710, 78.8260]]),
        ("Suresh Farm", 1, "Paddy Field North", "Rice", 14, "Grain Filling", "healthy", 10.850, 78.620, [[10.853,78.615],[10.853,78.625],[10.847,78.625],[10.847,78.615]]),
        ("Suresh Farm", 1, "Paddy Field South", "Rice", 14, "Grain Filling", "stressed", 10.845, 78.620, [[10.848,78.615],[10.848,78.625],[10.842,78.625],[10.842,78.615]]),
        ("Lakshmi Farm", 2, "Chilli Plot 1", "Chilli", 8, "Flowering", "healthy", 10.609, 78.529, [[10.611,78.527],[10.611,78.531],[10.607,78.531],[10.607,78.527]]),
        ("Lakshmi Farm", 2, "Chilli Plot 2", "Chilli", 7, "Fruiting", "healthy", 10.607, 78.532, [[10.609,78.530],[10.609,78.534],[10.605,78.534],[10.605,78.530]]),
        ("Murugan Farm", 3, "Groundnut Field", "Groundnut", 20, "Pod Formation", "healthy", 10.925, 78.627, [[10.927,78.624],[10.927,78.630],[10.923,78.630],[10.923,78.624]]),
        ("Anand Farm", 4, "Sugarcane Block A", "Sugarcane", 18, "Grand Growth", "healthy", 11.137, 79.072, [[11.139,79.069],[11.139,79.075],[11.135,79.075],[11.135,79.069]]),
        ("Anand Farm", 4, "Sugarcane Block B", "Sugarcane", 17, "Grand Growth", "healthy", 11.134, 79.072, [[11.136,79.069],[11.136,79.075],[11.132,79.075],[11.132,79.069]]),
    ]

    for fdata in field_data:
        farm = Farm(name=fdata[0], farmer_id=farmers[fdata[1]].id, total_area_acres=farmers[fdata[1]].farm_size_acres,
                    latitude=farmers[fdata[1]].latitude, longitude=farmers[fdata[1]].longitude)
        db.add(farm)
        db.flush()
        field = Field(farm_id=farm.id, name=fdata[2], crop=fdata[3], area_acres=fdata[4],
                      growth_stage=fdata[5], health_status=fdata[6], latitude=fdata[7], longitude=fdata[8], polygon=fdata[9])
        db.add(field)

    # Agents
    agents = [
        Agent(name="DRONE-01", agent_type="DRONE", status="AVAILABLE", battery_percent=92, payload_capacity_l=5.0, latitude=10.785, longitude=78.690, base_latitude=10.785, base_longitude=78.690, speed_kmh=30, treatment_compatibility=["Cotton","Rice","Wheat","Maize"]),
        Agent(name="DRONE-02", agent_type="DRONE", status="AVAILABLE", battery_percent=78, payload_capacity_l=4.0, latitude=10.785, longitude=78.690, base_latitude=10.785, base_longitude=78.690, speed_kmh=28, treatment_compatibility=["Cotton","Chilli","Groundnut"]),
        Agent(name="DRONE-03", agent_type="DRONE", status="AVAILABLE", battery_percent=100, payload_capacity_l=6.0, latitude=10.785, longitude=78.690, base_latitude=10.785, base_longitude=78.690, speed_kmh=35, treatment_compatibility=["Cotton","Rice","Wheat","Sugarcane","Chilli","Groundnut"]),
        Agent(name="DRONE-04", agent_type="DRONE", status="CHARGING", battery_percent=35, payload_capacity_l=5.0, latitude=10.785, longitude=78.690, base_latitude=10.785, base_longitude=78.690, speed_kmh=30, treatment_compatibility=["Cotton","Rice"]),
        Agent(name="ROBOT-01", agent_type="GROUND_ROBOT", status="AVAILABLE", battery_percent=88, payload_capacity_l=10.0, latitude=10.786, longitude=78.692, base_latitude=10.786, base_longitude=78.692, speed_kmh=5, treatment_compatibility=["Cotton","Rice","Wheat","Maize","Groundnut","Chilli","Sugarcane","Tomato","Potato","Onion"]),
    ]
    db.add_all(agents)
    db.flush()

    # Weather
    weather = WeatherSnapshot(latitude=10.7905, longitude=78.7047, temperature_c=29, humidity_percent=78, wind_speed_kmh=11, rain_probability=18)
    db.add(weather)

    # Demo outbreak — uses DEMO constants for consistency
    detection = Detection(
        field_id=DEMO_FIELD_ID, crop=DEMO_CROP, possible_pest=DEMO_PEST, confidence=DEMO_CONFIDENCE,
        severity=DEMO_SEVERITY, affected_area_acres=DEMO_AFFECTED_ACRES,
        latitude=DEMO_LATITUDE, longitude=DEMO_LONGITUDE, mode="DEMO_SIMULATION", status="confirmed"
    )
    db.add(detection)
    db.flush()

    outbreak = Outbreak(
        detection_id=detection.id, crop=DEMO_CROP, pest=DEMO_PEST, severity=DEMO_SEVERITY,
        affected_area_acres=DEMO_AFFECTED_ACRES, latitude=DEMO_LATITUDE, longitude=DEMO_LONGITUDE,
        risk_level=DEMO_SEVERITY, status="active", containment_radius=6.2
    )
    db.add(outbreak)
    db.flush()

    # Spread predictions using DEMO_PREDICTIONS
    for hours, area in DEMO_PREDICTIONS:
        db.add(SpreadPrediction(outbreak_id=outbreak.id, hours=hours, predicted_area_acres=area, temperature=29, humidity=78, wind_speed=11))

    # Historical contained outbreak
    old_detection = Detection(crop="Rice", possible_pest="Stem Borer", confidence=0.87, severity="MEDIUM", affected_area_acres=1.5, latitude=10.850, longitude=78.620, mode="DEMO_SIMULATION", status="resolved")
    db.add(old_detection)
    db.flush()
    old_outbreak = Outbreak(detection_id=old_detection.id, crop="Rice", pest="Stem Borer", severity="MEDIUM", affected_area_acres=1.5, latitude=10.850, longitude=78.620, risk_level="MEDIUM", status="contained", resolved_at=datetime.datetime.now(timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=3))
    db.add(old_outbreak)
    db.flush()
    mission = Mission(mission_code="MSN-2047", outbreak_id=old_outbreak.id, agent_id=agents[0].id, target_area_acres=1.5, estimated_chemical_l=6.0, precision_chemical_l=1.2, status="completed", eta_minutes=18, completed_at=datetime.datetime.now(timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=3))
    db.add(mission)
    db.flush()
    db.add(Treatment(mission_id=mission.id, target_area_acres=1.5, chemical_volume_l=1.2, estimated_conventional_l=6.0, savings_percent=80.0, status="completed", completed_at=datetime.datetime.now(timezone.utc).replace(tzinfo=None) - datetime.timedelta(days=3)))

    # Notifications
    db.add(Notification(farmer_id=farmers[0].id, title="Pest Detected", message="Bollworm detected in your cotton field. Precision treatment recommended.", notification_type="warning"))
    db.add(Notification(farmer_id=farmers[0].id, title="Crop Check", message="Your cotton crop looks healthy in North block.", notification_type="info"))

    # Event log seed entries
    events = [
        ("Detection Agent", f"Possible bollworm cluster detected in East Mixed Plot. {DEMO_AFFECTED_ACRES} acres affected.", "detection", "warning"),
        ("Prediction Agent", f"High spread risk calculated. {DEMO_AFFECTED_ACRES} → {DEMO_PREDICTIONS[-1][1]} acres in 24h.", "prediction", "warning"),
        ("Dispatch Agent", "Evaluating 5 agents for mission.", "dispatch", "info"),
        ("Mission Controller", "Mission MSN-2048 created.", "mission", "info"),
    ]
    for agent_name, msg, etype, sev in events:
        db.add(EventLog(agent_name=agent_name, message=msg, event_type=etype, severity=sev, related_outbreak_id=outbreak.id))

    db.commit()

# ─── INIT ──────────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
