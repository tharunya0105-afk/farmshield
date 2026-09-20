# FarmShield — Deployment Guide

## Prerequisites

- Python 3.10+ (tested on 3.12)
- pip
- A modern browser (Chrome / Edge / Firefox)

---

## Step 1 — Clone / Download

```bash
git clone https://github.com/<your-org>/farmshield.git
cd farmshield/divacoded
```

Or download and extract the ZIP, then `cd divacoded`.

---

## Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

> **Windows note**: Use `pip install opencv-python-headless` if the headless build fails on your platform.

---

## Step 3 — Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

On first run, the database (`farmshield.db`) is created and seeded automatically:
- 5 farmers, 3 farms, 10 fields (Tamil Nadu)
- 5 agents: DRONE-01 through DRONE-04 + ROBOT-01
- Demo outbreak (Bollworm, Cotton, 2.1 acres)
- Historical contained outbreak (Stem Borer, Rice)
- Seed weather snapshot

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
FarmShield DB initialized.
```

---

## Step 4 — Open the App

Navigate to: **http://localhost:8000**

The FastAPI server serves `frontend/index.html` as a static file.

---

## What to Demo (Judge Script)

### Landing Page
- Open `http://localhost:8000`
- Watch the animated stat counters load (72% pesticide reduction, 4.5 min response)
- Click **"Start Live Demo"**

### Live Demo (6-stage pipeline)
1. Click **"Start Demo"** — watch the timeline progress automatically
2. Map shows real GPS coordinates (Tiruchirappalli, Tamil Nadu)
3. Stage 2: spread chart appears with logistic model predictions
4. Stage 3: see DRONE-04 (35% battery) being skipped automatically
5. Stage 4: drone emoji animates across the map
6. Stage 5: chemical savings counter ticks up (8.4L → 1.8L)
7. Stage 6: green "Outbreak Contained!" banner appears

### Expert Console (after demo)
- Click **"View autonomous system →"**
- Toggle **dark mode** (☀/🌙 button, top right)
- Visit **Analytics** → see CO₂ saved, water saved, yield protected
- Visit **Chemical Rotation** → IRAC group advisor
- Visit **Event Log** → click **Export** to download audit trail
- Visit **Missions** → **Abort** button on active missions

### Farmer App
- From landing: click **"Explore Farmer App"**
- On desktop: shows phone frame with feature callout
- Switch language to **தமிழ்** — all strings update
- Toggle **Voice Guide** (speaker icon) → screen announces itself
- Go to **Profile** → toggle **Network** off → try Check Crop → "Saved on phone"
- Toggle Network back on → queued report auto-syncs

### Aerial Scan (Expert Console → Aerial Scan tab)
- Pick any sample field image
- CNN tiles the image (6×6 = 36 tiles), labels each tile
- Cluster bounding boxes overlay the original image
- Click **"Confirm → Outbreak"** to propagate to the backend

---

## API Verification

With the server running, open a new terminal:

```bash
# Health check
curl http://localhost:8000/api/health

# Analytics (incl. CO2, water, yield)
curl http://localhost:8000/api/analytics

# Weather + pest risk
curl http://localhost:8000/api/weather

# Spread model (dynamic)
curl -X POST "http://localhost:8000/api/spread/calculate?temperature=32&humidity=85&wind_speed=15&base_acres=2.1"

# Chemical rotation
curl http://localhost:8000/api/chemical-rotation
```

---

## Resetting the Demo State

```bash
curl -X POST http://localhost:8000/api/demo/reset
```

Or click **Reset** in the Live Demo UI.

To completely wipe and reseed the database:
```bash
cd backend
rm farmshield.db   # Windows: del farmshield.db
python -c "from database import init_db; init_db()"
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `uvicorn: command not found` | `pip install uvicorn` |
| `ModuleNotFoundError: cv2` | `pip install opencv-python-headless` |
| Map doesn't load | Check internet (Leaflet/OpenStreetMap tiles need internet) |
| CNN model missing | Ensure `backend/model_store/plantvillage_mobilenetv2.onnx` exists |
| Port 8000 in use | `uvicorn main:app --port 8001` — update `API` in `index.html` line 4 |

---

## Model Details

- **Model**: PlantVillage MobileNetV2 (ONNX format)
- **Classes**: 38 disease classes across 14 plant species
- **Runtime**: OpenCV DNN (no PyTorch / ONNX Runtime needed)
- **Input**: 224×224 RGB, normalized to [-1, 1]
- **Inference speed**: ~150–400ms on CPU depending on hardware

---

*FarmShield v2.0 · Hackwell 2.0 · AAA-09*
