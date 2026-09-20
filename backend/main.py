"""
FarmShield - FastAPI Backend
Detect Early. Predict Spread. Protect Precisely.
"""
import datetime, math, random, string, os
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import (
    get_db, init_db, seed_data,
    Farmer, Farm, Field, Detection, Outbreak, SpreadPrediction,
    Agent, Mission, Treatment, Notification, EventLog, WeatherSnapshot, ExpertReview,
    generate_id, validate_mission_transition,
    DEMO_PEST, DEMO_CROP, DEMO_CONFIDENCE, DEMO_SEVERITY, DEMO_AFFECTED_ACRES,
    DEMO_LATITUDE, DEMO_LONGITUDE, DEMO_FIELD_ID, DEMO_PREDICTIONS
)

import plant_model
import aerial_scan

app = FastAPI(title="FarmShield API", version="1.0.0", description="Detect Early. Predict Spread. Protect Precisely.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── HEALTH CHECK ──────────────────────────────────────────
@app.get("/api/health")
def health_check():
    try:
        from database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "database": db_status, "mode": "demo", "version": "1.0.0", "name": "FarmShield"}


@app.get("/api/model/status")
def vision_model_status():
    """Real vision-model status (loads the model on first call — warms it up)."""
    return plant_model.status()

# ─── PYDANTIC SCHEMAS ──────────────────────────────────────
class FarmerCreate(BaseModel):
    name: str
    mobile: str
    village: str = ""
    district: str = "Tiruchirappalli"
    state: str = "Tamil Nadu"
    language: str = "en"
    main_crop: str = "Cotton"
    farm_size_acres: float = 42.0
    latitude: float = 10.7905
    longitude: float = 78.7047

class FarmerOut(BaseModel):
    id: int; name: str; mobile: str; village: str; district: str; state: str
    language: str; main_crop: str; farm_size_acres: float; latitude: float; longitude: float
    class Config: from_attributes = True

class DetectionRequest(BaseModel):
    field_id: Optional[int] = None
    crop: str = "Cotton"
    photo_path: Optional[str] = None

class DetectionOut(BaseModel):
    id: int; crop: str; possible_pest: str; confidence: float; severity: str
    affected_area_acres: float; latitude: float; longitude: float; status: str
    created_at: datetime.datetime
    class Config: from_attributes = True

class AgentOut(BaseModel):
    id: int; name: str; agent_type: str; status: str; battery_percent: float
    payload_capacity_l: float; latitude: float; longitude: float
    base_latitude: float; base_longitude: float; speed_kmh: float
    treatment_compatibility: list; missions_completed: int
    class Config: from_attributes = True

class MissionCreate(BaseModel):
    outbreak_id: int
    agent_id: int

class EventLogOut(BaseModel):
    id: int; agent_name: str; message: str; event_type: str; severity: str
    created_at: datetime.datetime
    class Config: from_attributes = True

class DispatchSelect(BaseModel):
    outbreak_id: int

# ─── STARTUP ───────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()

# ─── FARMERS ───────────────────────────────────────────────
@app.get("/api/farmers", response_model=List[FarmerOut])
def list_farmers(db: Session = Depends(get_db)):
    return db.query(Farmer).all()

@app.post("/api/farmers", response_model=FarmerOut)
def create_farmer(data: FarmerCreate, db: Session = Depends(get_db)):
    if not data.name.strip():
        raise HTTPException(400, "Name is required")
    if not data.mobile.strip() or len(data.mobile.strip()) < 10:
        raise HTTPException(400, "Valid mobile number is required")
    if data.farm_size_acres <= 0:
        raise HTTPException(400, "Farm size must be positive")
    f = Farmer(**data.model_dump())
    db.add(f); db.commit(); db.refresh(f)
    farm = Farm(farmer_id=f.id, name=f"{f.name}'s Farm", total_area_acres=f.farm_size_acres, latitude=f.latitude, longitude=f.longitude)
    db.add(farm); db.commit()
    db.add(EventLog(agent_name="System", message=f"New farmer registered: {f.name} from {f.village}", event_type="registration", severity="info"))
    db.commit()
    return f

@app.get("/api/farmers/{farmer_id}", response_model=FarmerOut)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    f = db.query(Farmer).get(farmer_id)
    if not f: raise HTTPException(404, "Farmer not found")
    return f

@app.put("/api/farmers/{farmer_id}/language")
def update_language(farmer_id: int, language: str, db: Session = Depends(get_db)):
    f = db.query(Farmer).get(farmer_id)
    if not f: raise HTTPException(404, "Farmer not found")
    f.language = language; db.commit()
    return {"ok": True, "language": language}

# ─── FIELDS ────────────────────────────────────────────────
@app.get("/api/fields")
def list_fields(db: Session = Depends(get_db)):
    fields = db.query(Field).all()
    result = []
    for f in fields:
        farm = db.query(Farm).get(f.farm_id)
        farmer = db.query(Farmer).get(farm.farmer_id) if farm else None
        result.append({
            "id": f.id, "name": f.name, "crop": f.crop, "area_acres": f.area_acres,
            "growth_stage": f.growth_stage, "health_status": f.health_status,
            "latitude": f.latitude, "longitude": f.longitude, "polygon": f.polygon,
            "farm_name": farm.name if farm else "", "farmer_name": farmer.name if farmer else "",
            "farm_id": f.farm_id
        })
    return result

# ─── DETECTIONS ────────────────────────────────────────────
@app.get("/api/detections", response_model=List[DetectionOut])
def list_detections(db: Session = Depends(get_db)):
    return db.query(Detection).order_by(Detection.created_at.desc()).all()

@app.post("/api/detection/analyze")
def analyze_image(data: DetectionRequest, db: Session = Depends(get_db)):
    """Prototype AI pest detection — returns simulated detection results for demo."""
    field = db.query(Field).get(data.field_id) if data.field_id else None

    # For demo: use the consistent demo values from DEMO constants
    det = Detection(
        field_id=data.field_id, crop=data.crop or (field.crop if field else DEMO_CROP),
        possible_pest=DEMO_PEST, confidence=DEMO_CONFIDENCE, severity=DEMO_SEVERITY,
        affected_area_acres=DEMO_AFFECTED_ACRES,
        latitude=field.latitude if field else DEMO_LATITUDE,
        longitude=field.longitude if field else DEMO_LONGITUDE,
        mode="DEMO_SIMULATION", status="detected"
    )
    db.add(det); db.commit(); db.refresh(det)

    db.add(EventLog(agent_name="Detection Agent",
                     message=f"Image analyzed — possible {DEMO_PEST} detected ({DEMO_CONFIDENCE*100:.0f}% confidence) in {det.crop}",
                     event_type="detection", severity="warning"))
    db.commit()

    return {
        "detection_id": det.id, "crop": det.crop, "possible_pest": DEMO_PEST,
        "confidence": DEMO_CONFIDENCE, "severity": DEMO_SEVERITY, "affected_area_acres": DEMO_AFFECTED_ACRES,
        "latitude": det.latitude, "longitude": det.longitude, "mode": "DEMO_SIMULATION"
    }


@app.post("/api/detection/analyze-image")
async def analyze_image_upload(file: UploadFile = File(...), crop: str = Form("Cotton"),
                               field_id: Optional[int] = Form(None), db: Session = Depends(get_db)):
    """
    REAL vision-model detection: a farmer's actual leaf photo is classified by a
    MobileNetV2 CNN trained on PlantVillage (38 classes / 14 plants).

    Honest behavior:
    - confident disease  -> REAL_MODEL detection (client can confirm -> outbreak pipeline)
    - healthy leaf       -> healthy result, no outbreak
    - low confidence     -> VISUAL_CHECK: 'try a closer photo' (never invents a pest)
    - model unavailable  -> DEMO_SIMULATION fallback (demo never breaks)
    """
    field = db.query(Field).get(field_id) if field_id else None
    lat = field.latitude if field else DEMO_LATITUDE
    lon = field.longitude if field else DEMO_LONGITUDE
    area = field.area_acres if field else DEMO_AFFECTED_ACRES
    area_basis = "field_record" if field else "default_estimate"

    try:
        raw = await file.read()
        if not raw:
            raise ValueError("empty upload")
        label, conf = plant_model.classify(raw)
        desc = plant_model.describe(label, conf)
    except Exception:
        # Model failed (missing runtime, bad file, ...) — fall back honestly.
        det = Detection(field_id=field_id, crop=crop or DEMO_CROP, possible_pest=DEMO_PEST,
                        confidence=DEMO_CONFIDENCE, severity=DEMO_SEVERITY,
                        affected_area_acres=DEMO_AFFECTED_ACRES, latitude=lat, longitude=lon,
                        mode="DEMO_SIMULATION", status="detected")
        db.add(det); db.commit(); db.refresh(det)
        db.add(EventLog(agent_name="Detection Agent",
                        message=f"Vision model unavailable — simulated analysis used ({DEMO_PEST}, {DEMO_CONFIDENCE*100:.0f}%)",
                        event_type="detection", severity="info"))
        db.commit()
        return {"detection_id": det.id, "crop": det.crop, "possible_pest": DEMO_PEST,
                "confidence": DEMO_CONFIDENCE, "severity": DEMO_SEVERITY,
                "affected_area_acres": DEMO_AFFECTED_ACRES, "latitude": lat, "longitude": lon,
                "mode": "DEMO_SIMULATION", "healthy": False, "photo_analyzed": True}

    crop_name = desc["crop"]

    # ── confidence gates (product policy, honest by design):
    #    false alarms cost farmers money; false reassurance costs crops.
    #    - a 'healthy' verdict requires very high confidence (>= 0.85)
    #    - a disease alert requires solid confidence (>= 0.55)
    #    - anything in between: ask for a closer photo — never guess.
    gate = 0.85 if desc["healthy"] else 0.55
    if conf < gate:
        db.add(EventLog(agent_name="Detection Agent",
                        message=f"Vision model: photo inconclusive (best guess {label} at {conf*100:.0f}%) — closer photo requested",
                        event_type="detection", severity="info"))
        db.commit()
        return {"detection_id": None, "crop": crop_name, "possible_pest": None,
                "confidence": round(conf, 4), "severity": None, "affected_area_acres": 0.0,
                "latitude": lat, "longitude": lon, "mode": "VISUAL_CHECK",
                "healthy": None, "photo_analyzed": True}

    # ── healthy leaf: report honestly, raise nothing ──
    if desc["healthy"]:
        det = Detection(field_id=field_id, crop=crop_name, possible_pest="None detected",
                        confidence=round(conf, 4), severity="Low",
                        affected_area_acres=0.0, latitude=lat, longitude=lon,
                        mode="REAL_MODEL", status="healthy")
        db.add(det); db.commit(); db.refresh(det)
        db.add(EventLog(agent_name="Detection Agent",
                        message=f"Vision model: leaf looks healthy — {crop_name} ({conf*100:.0f}% confidence)",
                        event_type="detection", severity="info"))
        db.commit()
        return {"detection_id": det.id, "crop": crop_name, "possible_pest": None,
                "confidence": round(conf, 4), "severity": "Low", "affected_area_acres": 0.0,
                "latitude": lat, "longitude": lon, "mode": "REAL_MODEL",
                "healthy": True, "photo_analyzed": True}

    # ── confident disease: real detection, feeds the normal pipeline ──
    risk = desc["risk"]
    det = Detection(field_id=field_id, crop=crop_name, possible_pest=desc["possible_pest"],
                    confidence=round(conf, 4), severity=risk,
                    affected_area_acres=area, latitude=lat, longitude=lon,
                    mode="REAL_MODEL", status="detected")
    db.add(det); db.commit(); db.refresh(det)
    db.add(EventLog(agent_name="Detection Agent",
                    message=f"Vision model: {desc['possible_pest']} on {crop_name} ({conf*100:.0f}% confidence) — {risk} risk",
                    event_type="detection", severity="warning"))
    db.commit()
    return {"detection_id": det.id, "crop": crop_name, "possible_pest": desc["possible_pest"],
            "confidence": round(conf, 4), "severity": risk, "affected_area_acres": area,
            "area_basis": area_basis, "latitude": lat, "longitude": lon,
            "mode": "REAL_MODEL", "healthy": False, "photo_analyzed": True}


# ─── AERIAL SCAN (tile-scan detection agent) ─────────────
@app.get("/api/detection/sample-fields")
def list_sample_fields():
    """List available sample field images for the aerial scan demo."""
    samples_dir = os.path.join(os.path.dirname(__file__), "sample_fields")
    if not os.path.isdir(samples_dir):
        return []
    results = []
    for f in sorted(os.listdir(samples_dir)):
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            results.append({
                "name": f,
                "path": f"/api/detection/sample-fields/{f}",
                "description": {
                    "cotton_field.jpg": "Real cotton field aerial photo — try scanning for stress zones",
                    "diseased_leaf.jpg": "Diseased tomato leaf (late blight) — close-range disease detection",
                    "healthy_leaf.jpg": "Healthy tomato leaf — should show minimal hot tiles",
                    "rice_paddy.jpg": "Rice paddy field — aerial view",
                }.get(f, f"Sample field image: {f}"),
                "size_bytes": os.path.getsize(os.path.join(samples_dir, f)),
            })
    return results


@app.get("/api/detection/sample-fields/{filename}")
def get_sample_field(filename: str):
    """Serve a sample field image for the aerial scan demo."""
    samples_dir = os.path.join(os.path.dirname(__file__), "sample_fields")
    path = os.path.join(samples_dir, filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "Sample not found")
    return FileResponse(path)


@app.post("/api/detection/scan-field")
async def scan_field(
    file: UploadFile = File(...),
    field_area_acres: float = Form(42.0),
    field_id: Optional[int] = Form(None),
    create_detection: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    REAL aerial detection: runs the PlantVillage CNN per-tile over a field image,
    clusters hot tiles into infection zones, and returns real coordinates + acreage.

    This is NOT a simulation — every tile is classified by the same real CNN that
    handles farmer leaf photos. The detection agent runs autonomously over field
    imagery and outputs genuine threat assessments.
    """
    field = db.query(Field).get(field_id) if field_id else None
    lat = field.latitude if field else DEMO_LATITUDE
    lon = field.longitude if field else DEMO_LONGITUDE
    area = field.area_acres if field else field_area_acres

    field_bbox = None
    if field and field.polygon:
        # derive bbox from field polygon for GPS mapping
        try:
            lats = [p[0] for p in field.polygon]
            lons = [p[1] for p in field.polygon]
            field_bbox = {"lat_min": min(lats), "lat_max": max(lats),
                          "lon_min": min(lons), "lon_max": max(lons)}
        except Exception:
            pass
    if not field_bbox:
        # default bbox around field center
        field_bbox = {"lat_min": lat - 0.005, "lat_max": lat + 0.005,
                      "lon_min": lon - 0.005, "lon_max": lon + 0.005}

    try:
        raw = await file.read()
        if not raw:
            raise ValueError("empty upload")
        result = aerial_scan.scan_field(raw, field_area_acres=area, field_bbox=field_bbox)
    except Exception as e:
        return {"error": str(e), "mode": "SCAN_FAILED", "clusters": []}

    # Optionally create a Detection row for the worst cluster
    detection_id = None
    if create_detection and result["clusters"]:
        worst = result["clusters"][0]
        det = Detection(
            field_id=field_id, crop="Cotton",
            possible_pest=worst["main_pest"],
            confidence=worst["avg_confidence"],
            severity="High" if worst["avg_confidence"] >= 0.7 else "Medium",
            affected_area_acres=worst["est_acres"],
            latitude=worst["lat"] or lat,
            longitude=worst["lon"] or lon,
            mode="REAL_MODEL_AERIAL", status="detected",
        )
        db.add(det); db.commit(); db.refresh(det)
        detection_id = det.id

        db.add(EventLog(
            agent_name="Aerial Detection Agent",
            message=f"Aerial scan: {result['detection_summary']} — worst zone: {worst['main_pest']} ({worst['avg_confidence']*100:.0f}%, {worst['est_acres']} acres)",
            event_type="detection", severity="warning",
        ))
        db.commit()

    result["detection_id"] = detection_id
    return result


@app.post("/api/detections/{det_id}/confirm")
def confirm_detection(det_id: int, db: Session = Depends(get_db)):
    det = db.query(Detection).get(det_id)
    if not det: raise HTTPException(404, "Detection not found")
    if det.status == "confirmed":
        # Already confirmed — find existing outbreak
        existing = db.query(Outbreak).filter(Outbreak.detection_id == det.id).first()
        if existing:
            return {"outbreak_id": existing.id, "status": existing.status}
    det.status = "confirmed"

    outbreak = Outbreak(
        detection_id=det.id, crop=det.crop, pest=det.possible_pest, severity=det.severity,
        affected_area_acres=det.affected_area_acres, latitude=det.latitude, longitude=det.longitude,
        risk_level=det.severity, status="active", containment_radius=6.2
    )
    db.add(outbreak); db.commit(); db.refresh(outbreak)

    base = det.affected_area_acres
    for hrs, area in DEMO_PREDICTIONS:
        db.add(SpreadPrediction(outbreak_id=outbreak.id, hours=hrs, predicted_area_acres=area,
                                temperature=29, humidity=78, wind_speed=11))

    notif_msg = f"🔴 Crop problem detected: {det.possible_pest} in {det.crop}. Precision treatment recommended."
    db.add(Notification(farmer_id=1, title="Pest Alert", message=notif_msg, notification_type="warning"))
    db.add(EventLog(agent_name="Detection Agent", message=f"Outbreak OUT-{outbreak.id:04d} confirmed — {det.possible_pest}, {det.affected_area_acres} acres, {det.severity} risk", event_type="outbreak", severity="warning"))
    db.add(EventLog(agent_name="Prediction Agent", message="Spread prediction generated (2h, 6h, 12h, 24h)", event_type="prediction", severity="info"))
    db.commit()
    return {"outbreak_id": outbreak.id, "status": "active"}

# ─── OUTBREAKS ─────────────────────────────────────────────
@app.get("/api/outbreaks")
def list_outbreaks(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Outbreak)
    if status: q = q.filter(Outbreak.status == status)
    results = []
    for o in q.order_by(Outbreak.created_at.desc()).all():
        preds = [{"hours": p.hours, "area": p.predicted_area_acres, "temp_c": p.temperature,
                  "humidity_pct": p.humidity, "wind_kph": p.wind_speed} for p in db.query(SpreadPrediction).filter(SpreadPrediction.outbreak_id == o.id).order_by(SpreadPrediction.hours).all()]
        results.append({
            "id": o.id, "crop": o.crop, "pest": o.pest, "severity": o.severity,
            "affected_area_acres": o.affected_area_acres, "latitude": o.latitude, "longitude": o.longitude,
            "risk_level": o.risk_level, "status": o.status, "containment_radius": o.containment_radius,
            "predictions": preds, "created_at": o.created_at.isoformat()
        })
    return results

@app.post("/api/outbreaks/{outbreak_id}/contain")
def contain_outbreak(outbreak_id: int, db: Session = Depends(get_db)):
    o = db.query(Outbreak).get(outbreak_id)
    if not o: raise HTTPException(404)
    o.status = "contained"; o.resolved_at = datetime.datetime.utcnow()
    db.add(EventLog(agent_name="Mission Controller", message=f"Outbreak OUT-{o.id:04d} marked CONTAINED", event_type="containment", severity="success"))
    db.add(Notification(farmer_id=1, title="Treatment Complete", message=f"🟢 Your {o.crop} field has been treated. Outbreak contained.", notification_type="success"))
    db.commit()
    return {"status": "contained"}

# ─── AGENTS ────────────────────────────────────────────────
@app.get("/api/agents", response_model=List[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()

# ─── MISSIONS ──────────────────────────────────────────────
@app.get("/api/missions")
def list_missions(db: Session = Depends(get_db)):
    missions = db.query(Mission).order_by(Mission.created_at.desc()).all()
    result = []
    for m in missions:
        a = db.query(Agent).get(m.agent_id)
        o = db.query(Outbreak).get(m.outbreak_id)
        result.append({
            "id": m.id, "mission_code": m.mission_code, "outbreak_id": m.outbreak_id,
            "agent_id": m.agent_id, "agent_name": a.name if a else "",
            "outbreak_pest": o.pest if o else "", "outbreak_crop": o.crop if o else "",
            "target_area_acres": m.target_area_acres, "estimated_chemical_l": m.estimated_chemical_l,
            "precision_chemical_l": m.precision_chemical_l, "status": m.status,
            "eta_minutes": m.eta_minutes, "created_at": m.created_at.isoformat()
        })
    return result

@app.post("/api/missions")
def create_mission(data: MissionCreate, db: Session = Depends(get_db)):
    o = db.query(Outbreak).get(data.outbreak_id)
    a = db.query(Agent).get(data.agent_id)
    if not o or not a: raise HTTPException(404, "Outbreak or Agent not found")
    if o.status != "active": raise HTTPException(400, "Outbreak is not active")
    if a.status != "AVAILABLE": raise HTTPException(400, f"{a.name} is not available")

    # Idempotency: reuse an existing active mission for this outbreak instead of creating duplicates
    existing = db.query(Mission).filter(Mission.outbreak_id == o.id, Mission.status.notin_(["completed"])).first()
    if existing: return {"mission_id": existing.id, "mission_code": existing.mission_code, "eta_minutes": existing.eta_minutes}

    code = f"MSN-{random.randint(1000,9999)}"
    est_l = DEMO_AFFECTED_ACRES * 4.0
    prec_l = round(est_l * 0.214, 1)
    dist = math.sqrt((o.latitude - a.latitude)**2 + (o.longitude - a.longitude)**2) * 111
    eta = max(5, round(dist / a.speed_kmh * 60))

    m = Mission(mission_code=code, outbreak_id=o.id, agent_id=a.id, target_area_acres=o.affected_area_acres,
                estimated_chemical_l=est_l, precision_chemical_l=prec_l, status="created", eta_minutes=eta)
    db.add(m); db.commit(); db.refresh(m)

    db.add(Treatment(mission_id=m.id, target_area_acres=o.affected_area_acres, chemical_volume_l=prec_l,
                     estimated_conventional_l=est_l, savings_percent=round((1 - prec_l/est_l)*100, 1), status="pending"))
    db.add(EventLog(agent_name="Mission Controller", message=f"Mission {code} created — {a.name} → {o.pest} zone, ETA {eta} min", event_type="mission", severity="info", related_mission_id=m.id))
    db.commit()
    return {"mission_id": m.id, "mission_code": code, "eta_minutes": eta}

@app.post("/api/missions/{mission_id}/status")
def update_mission_status(mission_id: int, action: str, db: Session = Depends(get_db)):
    m = db.query(Mission).get(mission_id)
    if not m: raise HTTPException(404)
    treatments = db.query(Treatment).filter(Treatment.mission_id == mission_id).all()
    a = db.query(Agent).get(m.agent_id)

    # State machine: map action names to target states
    ACTION_TO_TARGET = {"dispatch": "dispatched", "arrive": "arrived", "treat": "treating", "complete": "completed"}
    target = ACTION_TO_TARGET.get(action)
    if not target or not validate_mission_transition(m.status, target):
        raise HTTPException(400, f"Invalid transition: {m.status} → {action}")

    if action == "dispatch":
        m.status = "dispatched"; m.started_at = datetime.datetime.utcnow()
        if a: a.status = "EN_ROUTE"
        db.add(EventLog(agent_name="Dispatch Agent", message=f"{a.name if a else 'Agent'} dispatched to zone", event_type="dispatch", severity="info", related_mission_id=m.id))
    elif action == "arrive":
        m.status = "arrived"
        if a: a.status = "TREATING"
        db.add(EventLog(agent_name="Drone Agent", message=f"{a.name if a else 'Agent'} arrived at treatment zone", event_type="drone", severity="info", related_mission_id=m.id))
    elif action == "treat":
        m.status = "treating"
        for t in treatments: t.status = "in_progress"; t.started_at = datetime.datetime.utcnow()
        db.add(EventLog(agent_name="Treatment Agent", message=f"Precise treatment started — {m.target_area_acres} acres target zone", event_type="treatment", severity="info", related_mission_id=m.id))
    elif action == "complete":
        m.status = "completed"; m.completed_at = datetime.datetime.utcnow()
        if a: a.status = "AVAILABLE"; a.missions_completed += 1; a.latitude = a.base_latitude; a.longitude = a.base_longitude
        for t in treatments: t.status = "completed"; t.completed_at = datetime.datetime.utcnow()
        o = db.query(Outbreak).get(m.outbreak_id)
        if o: o.status = "contained"; o.resolved_at = datetime.datetime.utcnow()
        db.add(EventLog(agent_name="Mission Controller", message=f"Mission {m.mission_code} COMPLETED — outbreak contained", event_type="containment", severity="success", related_mission_id=m.id))
        db.add(Notification(farmer_id=1, title="Treatment Complete", message=f"🟢 Your {o.crop if o else 'crop'} field has been treated successfully.", notification_type="success"))

    db.commit()
    return {"status": m.status}

# ─── WEATHER ───────────────────────────────────────────────
@app.get("/api/weather")
def get_weather(db: Session = Depends(get_db)):
    w = db.query(WeatherSnapshot).order_by(WeatherSnapshot.id.desc()).first()
    if not w:
        w = WeatherSnapshot(latitude=10.7905, longitude=78.7047, temperature_c=29, humidity_percent=78, wind_speed_kmh=11, rain_probability=18)
        db.add(w); db.commit(); db.refresh(w)
    risk = "HIGH" if w.temperature_c > 30 and w.humidity_percent > 70 else "MODERATE" if w.temperature_c > 25 else "LOW"
    return {
        "temperature_c": w.temperature_c, "humidity_percent": w.humidity_percent,
        "wind_speed_kmh": w.wind_speed_kmh, "rain_probability": w.rain_probability,
        "pest_risk": risk, "created_at": w.created_at.isoformat()
    }

# ─── EVENTS ────────────────────────────────────────────────
@app.get("/api/events", response_model=List[EventLogOut])
def list_events(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(EventLog).order_by(EventLog.created_at.desc()).limit(limit).all()

# ─── NOTIFICATIONS ─────────────────────────────────────────
@app.get("/api/notifications")
def list_notifications(farmer_id: int = 1, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.farmer_id == farmer_id).order_by(Notification.created_at.desc()).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "type": n.notification_type, "read": n.read, "created_at": n.created_at.isoformat()} for n in notifs]

@app.post("/api/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).get(notif_id)
    if n: n.read = True; db.commit()
    return {"ok": True}

# ─── ANALYTICS ─────────────────────────────────────────────
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_outbreaks = db.query(Outbreak).count()
    contained = db.query(Outbreak).filter(Outbreak.status == "contained").count()
    active = db.query(Outbreak).filter(Outbreak.status == "active").count()
    total_missions = db.query(Mission).count()
    completed_missions = db.query(Mission).filter(Mission.status == "completed").count()
    farmers_count = db.query(Farmer).count()
    fields_count = db.query(Field).count()
    total_area = db.query(func.sum(Field.area_acres)).scalar() or 0

    treatments = db.query(Treatment).all()
    total_precision = sum(t.chemical_volume_l for t in treatments)
    total_conventional = sum(t.estimated_conventional_l for t in treatments)
    pesticide_saved_l = round(total_conventional - total_precision, 1)
    pesticide_savings = round((1 - total_precision / total_conventional) * 100, 1) if total_conventional > 0 else 0

    avg_eta = 0
    completed = db.query(Mission).filter(Mission.status == "completed").all()
    if completed:
        avg_eta = round(sum(m.eta_minutes for m in completed) / len(completed), 1)

    # CO2 savings: pesticide transport + manufacturing baseline ~2.5 kg CO2 per litre saved
    # Chemical application by drone vs tractor: ~0.8 kg CO2/L tractor fuel equivalent saved
    co2_saved_kg = round(pesticide_saved_l * 2.5 + (total_conventional - total_precision) * 0.8, 1)

    # Yield protection estimate: avg 22% bollworm loss on 2.1 acres cotton @ INR 7000/quintal, 8 quintal/acre
    yield_protected_inr = round(contained * 2.1 * 8 * 7000 * 0.22, 0) if contained else 0

    # Water saved: blanket spraying requires 200L water/acre; precision uses 40L/acre
    water_saved_l = round((total_conventional - total_precision) * 160, 0) if total_conventional else 0

    return {
        "total_outbreaks": total_outbreaks, "contained_outbreaks": contained, "active_outbreaks": active,
        "total_missions": total_missions, "completed_missions": completed_missions,
        "farmers_protected": farmers_count, "fields_monitored": fields_count,
        "area_monitored_acres": round(total_area, 1),
        "pesticide_savings_percent": pesticide_savings,
        "avg_response_time_min": avg_eta,
        "estimated_pesticide_saved_l": pesticide_saved_l,
        "co2_saved_kg": co2_saved_kg,
        "yield_protected_inr": yield_protected_inr,
        "water_saved_l": water_saved_l,
    }

# ─── CROP DATA ─────────────────────────────────────────────
@app.get("/api/crops")
def list_crops():
    return [
        {"name": "Rice", "icon": "🌾"}, {"name": "Wheat", "icon": "🌾"}, {"name": "Cotton", "icon": "🌿"},
        {"name": "Sugarcane", "icon": "🎋"}, {"name": "Maize", "icon": "🌽"}, {"name": "Groundnut", "icon": "🥜"},
        {"name": "Chilli", "icon": "🌶️"}, {"name": "Tomato", "icon": "🍅"}, {"name": "Potato", "icon": "🥔"},
        {"name": "Onion", "icon": "🧅"}, {"name": "Banana", "icon": "🍌"}, {"name": "Coconut", "icon": "🥥"},
        {"name": "Pulses", "icon": "🌱"},
    ]

# ─── LOCATIONS ─────────────────────────────────────────────
@app.get("/api/locations/states")
def list_states():
    return ["Tamil Nadu", "Andhra Pradesh", "Telangana", "Karnataka", "Kerala", "Maharashtra", "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh"]

@app.get("/api/locations/districts")
def list_districts(state: str = "Tamil Nadu"):
    data = {
        "Tamil Nadu": ["Tiruchirappalli", "Chennai", "Coimbatore", "Madurai", "Salem", "Tirunelveli", "Erode", "Thanjavur", "Dindigul", "Ariyalur"],
        "Karnataka": ["Bangalore Rural", "Mysore", "Mandya", "Hassan", "Raichur"],
        "Andhra Pradesh": ["Guntur", "Prakasam", "Kurnool", "Anantapur"],
    }
    return data.get(state, ["District 1", "District 2"])

# ─── CHEMICAL ROTATION ADVISOR ────────────────────────────
@app.get("/api/chemical-rotation")
def get_chemical_rotation():
    """Returns IRAC-based chemical rotation recommendations per pest."""
    return {
        "rotations": [
            {
                "pest": "Bollworm", "crop": "Cotton",
                "irac_groups": ["Group 5 (Spinosyns)", "Group 28 (Diamides)", "Group 6 (Avermectins)"],
                "chemicals": ["Spinosad", "Chlorantraniliprole", "Abamectin"],
                "rotation_note": "Rotate groups every 2 sprays. Avoid consecutive Group 28.",
                "preharvest_interval_days": [3, 7, 3],
            },
            {
                "pest": "Stem Borer", "crop": "Rice",
                "irac_groups": ["Group 1A (Carbamates)", "Group 3A (Pyrethroids)", "Group 28 (Diamides)"],
                "chemicals": ["Carbofuran", "Lambda-cyhalothrin", "Flubendiamide"],
                "rotation_note": "Do not use Group 1A more than once per season.",
                "preharvest_interval_days": [60, 14, 14],
            },
            {
                "pest": "Aphid Cluster", "crop": "Chilli",
                "irac_groups": ["Group 4A (Neonicotinoids)", "Group 9D (Chordotonal)", "Group 25 (METI)"],
                "chemicals": ["Imidacloprid", "Flonicamid", "Fenpyroximate"],
                "rotation_note": "Restrict neonicotinoids to 2 applications per season due to bee risk.",
                "preharvest_interval_days": [7, 3, 7],
            },
        ],
        "resistance_warning": "Resistance confirmed if same outbreak re-emerges within 7 days of treatment. Escalate to agronomist.",
    }

# ─── AGENT TELEMETRY ───────────────────────────────────────
@app.post("/api/agents/{agent_id}/telemetry")
def update_agent_telemetry(agent_id: int, battery: Optional[float] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Simulate real-time agent telemetry update during a mission."""
    a = db.query(Agent).get(agent_id)
    if not a: raise HTTPException(404, "Agent not found")
    if battery is not None:
        a.battery_percent = max(0.0, min(100.0, battery))
    if status and status in ["AVAILABLE", "EN_ROUTE", "TREATING", "CHARGING", "MAINTENANCE"]:
        a.status = status
    db.add(EventLog(agent_name="Telemetry", message=f"{a.name} telemetry update — battery {a.battery_percent:.0f}%, status {a.status}", event_type="telemetry", severity="info"))
    db.commit()
    return {"id": a.id, "name": a.name, "battery_percent": a.battery_percent, "status": a.status}

# ─── DYNAMIC SPREAD PREDICTION ─────────────────────────────
@app.post("/api/spread/calculate")
def calculate_spread(temperature: float = 29, humidity: float = 78, wind_speed: float = 11, base_acres: float = 2.1):
    """
    Dynamic spread prediction formula based on microclimate.
    Growth model: logistic with temperature and humidity as rate drivers.
    Based on published degree-day / humidity pest growth models.
    """
    # Normalize factors (agronomic degree-day model)
    temp_factor = max(0, (temperature - 15) / 25)  # optimum 40°C, baseline 15°C
    humidity_factor = max(0, (humidity - 40) / 60)  # optimum 100%, threshold 40%
    wind_factor = 1 + (wind_speed / 40) * 0.3       # wind accelerates spread up to 30%
    growth_rate = 0.18 * (temp_factor * 0.6 + humidity_factor * 0.4) * wind_factor
    uncertainty = round(base_acres * 0.15, 2)  # ±15% uncertainty band

    predictions = []
    for hours in [0, 2, 6, 12, 24]:
        # Logistic growth: area = K / (1 + (K/A0 - 1) * exp(-r*t))
        K = base_acres * 8  # carrying capacity (field size)
        projected = K / (1 + (K / base_acres - 1) * math.exp(-growth_rate * hours))
        projected = round(projected, 1)
        predictions.append({
            "hours": hours,
            "area": projected,
            "range_min": round(max(base_acres, projected - uncertainty * (hours/24 + 0.5)), 1),
            "range_max": round(projected + uncertainty * (hours/24 + 0.5), 1),
            "temp_c": temperature, "humidity_pct": humidity, "wind_kph": wind_speed,
        })
    risk = "HIGH" if growth_rate > 0.12 else "MODERATE" if growth_rate > 0.06 else "LOW"
    return {
        "base_acres": base_acres, "growth_rate": round(growth_rate, 4), "risk_level": risk,
        "predictions": predictions,
        "note": "Prototype simulation — degree-day logistic growth model. Uncertainty band ±15%."
    }

# ─── MISSION ABORT ─────────────────────────────────────────
@app.post("/api/missions/{mission_id}/abort")
def abort_mission(mission_id: int, reason: str = "operator_abort", db: Session = Depends(get_db)):
    """Emergency mission abort — agent returns to base. Human-in-the-loop control."""
    m = db.query(Mission).get(mission_id)
    if not m: raise HTTPException(404, "Mission not found")
    if m.status in ["completed", "aborted"]:
        raise HTTPException(400, f"Cannot abort mission in state: {m.status}")
    prev_status = m.status
    m.status = "aborted"
    a = db.query(Agent).get(m.agent_id)
    if a:
        a.status = "AVAILABLE"
        a.latitude = a.base_latitude
        a.longitude = a.base_longitude
    db.add(EventLog(agent_name="Mission Controller",
                    message=f"⚠️ Mission {m.mission_code} ABORTED (from {prev_status}) — reason: {reason}. Agent returning to base.",
                    event_type="abort", severity="warning", related_mission_id=m.id))
    db.commit()
    return {"status": "aborted", "mission_code": m.mission_code, "reason": reason}

# ─── DISPATCH ALGORITHM ────────────────────────────────────
@app.post("/api/dispatch/select")
def select_agent(data: DispatchSelect, db: Session = Depends(get_db)):
    o = db.query(Outbreak).get(data.outbreak_id)
    if not o: raise HTTPException(404, "Outbreak not found")
    agents = db.query(Agent).filter(Agent.status == "AVAILABLE").all()
    scored = []
    for a in agents:
        compat = a.treatment_compatibility or []
        if o.crop not in compat: continue
        dist = math.sqrt((o.latitude - a.latitude)**2 + (o.longitude - a.longitude)**2) * 111
        travel_min = max(dist, 0.1) / a.speed_kmh * 60
        # Score by estimated travel time (fastest response wins), weighted by battery and payload
        score = (1 / max(travel_min, 0.5)) * (a.battery_percent / 100) * (a.payload_capacity_l / 10)
        scored.append({"agent": a, "score": score, "distance_km": round(dist, 1),
                       "reason": f"closest compatible available agent with sufficient battery and treatment capacity ({round(dist, 1)} km, ~{int(travel_min)} min travel, {a.battery_percent:.0f}% battery, {a.payload_capacity_l}L)"})
    scored.sort(key=lambda x: x["score"], reverse=True)

    db.add(EventLog(agent_name="Dispatch Engine", message=f"Evaluating {len(scored)} compatible agents for outbreak OUT-{o.id:04d}", event_type="dispatch", severity="info"))
    if scored:
        best = scored[0]
        db.add(EventLog(agent_name="Dispatch Engine", message=f"{best['agent'].name} selected — {best['reason']}", event_type="dispatch", severity="info"))
    db.commit()

    return {
        "candidates": [{"id": s["agent"].id, "name": s["agent"].name, "battery": s["agent"].battery_percent,
                        "distance_km": s["distance_km"], "score": round(s["score"], 3), "reason": s["reason"]}
                       for s in scored[:5]],
        "selected": scored[0]["agent"].id if scored else None
    }

# ─── DEMO RESET ────────────────────────────────────────────
@app.post("/api/demo/reset")
def reset_demo():
    from database import Base, engine, SessionLocal
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_new = SessionLocal()
    try:
        seed_data(db_new)
    finally:
        db_new.close()
    return {"status": "reset", "message": "FarmShield demo state restored"}

# ─── ARCHITECTURE INFO ─────────────────────────────────────
@app.get("/api/architecture")
def get_architecture():
    return {
        "name": "FarmShield",
        "version": "1.0.0",
        "description": "AI-Powered Precision Farming & Pest Response for Indian Farmers",
        "components": [
            {"name": "Image Ingestion", "type": "drone", "status": "active"},
            {"name": "Detection Agent", "type": "ai", "status": "active", "mode": "Real CNN (PlantVillage MobileNetV2) + Aerial Tile-Scan + Scenario Demo"},
            {"name": "FastAPI Backend", "type": "server", "status": "active"},
            {"name": "Prediction Engine", "type": "ai", "status": "active", "mode": "Prototype Simulation"},
            {"name": "Dispatch Decision Engine", "type": "ai", "status": "active"},
            {"name": "Mission Controller", "type": "system", "status": "active"},
            {"name": "Drone/Robot Fleet", "type": "hardware", "status": "5 agents"},
        ],
        "workflow": ["FARM → DETECT → PREDICT → DISPATCH → TREAT → CONTAIN"]
    }

# ─── EXPERT REVIEWS ────────────────────────────────────────
@app.get("/api/expert-reviews")
def list_reviews(db: Session = Depends(get_db)):
    return db.query(ExpertReview).order_by(ExpertReview.created_at.desc()).all()

# ─── SERVE FRONTEND ────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    file_path = os.path.join(frontend_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))
