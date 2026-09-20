# FarmShield 🌾
## Autonomous Crop Pest & Disease Containment Network

> **Hackwell 2.0 — Problem AAA-09**  
> *Detect Early. Predict Spread. Protect Precisely.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![PlantVillage CNN](https://img.shields.io/badge/CNN-MobileNetV2-orange)](https://plantvillage.psu.edu/)

---

## What FarmShield Does

FarmShield is a **5-stage autonomous pipeline** that turns a farmer's leaf photo into a contained outbreak in under 5 minutes:

```
[Farmer reports] → [CNN detects pest] → [Spread predicted] → [Agent selected] → [Precision spray] → [Contained]
```

| Stage | What happens | Technology |
|---|---|---|
| **Detect** | Farmer takes leaf photo; aerial scan tiles field into 6×6 grid | PlantVillage MobileNetV2, OpenCV DNN |
| **Predict** | Logistic spread model using temp, humidity, wind speed | Degree-day growth model, ±15% uncertainty bands |
| **Dispatch** | Scores every agent: travel time × battery × payload | Weighted scoring algorithm |
| **Treat** | Drone delivers precision dose to GPS-bounded zone | Geofenced mission, IRAC chemical rotation |
| **Contain** | Outbreak marked contained, farmer notified | SMS + IVR in 7 Indian languages |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (index.html)                       │
│  Landing · LiveDemo · FarmerApp · ExpertConsole · AerialScan   │
│  React 18 · Tailwind · Leaflet · i18n (7 languages)            │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────────┐
│                   FastAPI Backend (main.py)                     │
│  43 REST endpoints · SQLite persistent state                    │
│  Mission state machine · Dispatch scoring engine               │
│  Spread prediction (logistic growth) · Chemical rotation       │
└──────┬─────────────────┬────────────────────────────────────────┘
       │                 │
┌──────▼──────┐  ┌───────▼───────────────────────────┐
│ SQLite DB   │  │ plant_model.py + aerial_scan.py   │
│ (farmshield │  │ PlantVillage MobileNetV2 ONNX     │
│  .db)       │  │ 38 classes · 14 crops · OpenCV   │
└─────────────┘  └────────────────────────────────────┘
```

---

## Key Features

### ✅ What's Real (not simulated)
- **CNN inference**: PlantVillage MobileNetV2 ONNX model runs on real leaf images
- **Aerial tile scan**: 6×6 grid, BFS cluster detection, confidence-weighted
- **Persistent backend**: Every detection, mission, and event stored in SQLite
- **Offline queue**: localStorage store-and-forward — works without network
- **Mission state machine**: created → dispatched → arrived → treating → completed
- **Dispatch scoring**: distance × battery × payload (DRONE-04 at 35% correctly skipped)

### ⚠ What's Labeled as Prototype Simulation
- Pest-spread predictions (logistic model, not field-validated)
- Demo detection flow (CNN model is real, but cotton/bollworm labels are demo-seeded)
- Pesticide/CO₂ savings numbers (computed formula, not A/B field trial)

---

## Quick Start

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full instructions.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend
cd backend
uvicorn main:app --reload --port 8000

# 3. Open frontend
# Navigate to http://localhost:8000 (served by FastAPI static files)
```

---

## API Endpoints (key)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health, model status |
| `GET` | `/api/analytics` | Full metrics incl. CO₂, yield protected |
| `GET` | `/api/weather` | Weather + pest risk level |
| `POST` | `/api/detection/analyze-image` | Real CNN on uploaded leaf image |
| `POST` | `/api/detection/scan-field` | Aerial 6×6 tile scan |
| `POST` | `/api/spread/calculate` | Dynamic logistic spread model |
| `POST` | `/api/dispatch/select` | Best-agent scoring |
| `POST` | `/api/missions/{id}/abort` | Emergency abort (human-in-loop) |
| `GET` | `/api/chemical-rotation` | IRAC resistance rotation advisor |
| `POST` | `/api/demo/reset` | Reset state for demo run |

---

## Farmer Accessibility

FarmShield works without a smartphone, literacy, English, or network signal:

| Constraint | How it's handled |
|---|---|
| No smartphone | SMS alert + IVR voice call in farmer's language |
| Illiterate | Voice guide reads every screen; icon-first UI |
| No English | 7 languages: Tamil, Hindi, Telugu, Kannada, Malayalam, Marathi, English |
| No network | Reports queue in localStorage, auto-sync on reconnect |
| No capex | Shared FPO fleet; farmer pays per treated acre |

---

## Honest Constraints

> *"Rule of the room: every claim maps to something visible in the working app."*

- Numbers labeled **"Prototype Estimate"** are model-computed, not field-validated
- Pesticide savings use published precision-vs-blanket benchmarks, not our own trials
- RL dispatch is weighted heuristics, clearly labeled — not trained reinforcement learning
- Carbon savings use published pesticide lifecycle data, not our own measurement

---

## Project Structure

```
divacoded/
├── backend/
│   ├── main.py              # FastAPI app, 43 endpoints
│   ├── database.py          # SQLAlchemy models, seed data
│   ├── plant_model.py       # PlantVillage CNN wrapper
│   ├── aerial_scan.py       # Tile-grid scan + BFS clustering
│   └── model_store/
│       ├── plantvillage_mobilenetv2.onnx
│       └── config.json
├── frontend/
│   └── index.html           # React 18 SPA (2235 lines)
├── divacoded/               # Judge documentation
│   ├── JUDGE_QA.md
│   └── JUDGE_QA_INCLUSION.md
├── requirements.txt
├── DEPLOYMENT.md
└── README.md
```

---

*FarmShield v2.0 · Hackwell 2.0 · AAA-09*
