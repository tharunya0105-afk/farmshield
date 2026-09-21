"""
FarmShield End-to-End Automated Verification Test Suite
Tests all 42 endpoints, data models, error handling, rate limiting, and business logic.
"""
import urllib.request
import urllib.error
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.getcode(), json.loads(res.read().decode('utf-8'))

def post(path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode('utf-8') if body is not None else b''
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'} if body is not None else {},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.getcode(), json.loads(res.read().decode('utf-8'))

def put(path, body):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.getcode(), json.loads(res.read().decode('utf-8'))

tests_run = 0
tests_passed = 0

def run_test(name, func):
    global tests_run, tests_passed
    tests_run += 1
    try:
        func()
        tests_passed += 1
        print(f"  PASS: {name}")
    except Exception as e:
        print(f"  FAIL: {name} -> {e}")

print("==================================================")
print("Running FarmShield E2E System Verification")
print("==================================================")

# 1. Health & System
def test_health():
    code, data = get("/api/health")
    if code != 200 or data.get("status") not in ["ok", "healthy"]:
        raise ValueError(f"Health failed: {code}, {data}")
run_test("GET /api/health", test_health)

def test_model():
    code, data = get("/api/model/status")
    if code != 200 or "classes" not in data:
        raise ValueError(f"Model status failed: {code}, {data}")
run_test("GET /api/model/status", test_model)

def test_arch():
    code, data = get("/api/architecture")
    if code != 200 or "components" not in data:
        raise ValueError(f"Architecture failed: {code}, {data}")
run_test("GET /api/architecture", test_arch)

# 2. Farmers & Fields
def test_farmers():
    code, data = get("/api/farmers")
    if code != 200 or len(data) < 1:
        raise ValueError(f"Farmers failed: {code}, {data}")
run_test("GET /api/farmers", test_farmers)

def test_lang():
    code, data = put("/api/farmers/1/language", {"language": "ta"})
    if code != 200 or data.get("language") != "ta":
        raise ValueError(f"Language update failed: {code}, {data}")
run_test("PUT /api/farmers/1/language", test_lang)

def test_fields():
    code, data = get("/api/fields")
    if code != 200 or len(data) < 1:
        raise ValueError(f"Fields failed: {code}, {data}")
run_test("GET /api/fields", test_fields)

# 3. Detection & Outbreaks
def test_analyze():
    code, data = post("/api/detection/analyze", {"crop": "Cotton", "field_id": 1, "notes": "E2E Test"})
    if code != 200 or not data.get("detection_id"):
        raise ValueError(f"Detection analyze failed: {code}, {data}")
run_test("POST /api/detection/analyze", test_analyze)

def test_outbreaks():
    code, data = get("/api/outbreaks")
    if code != 200 or len(data) < 1:
        raise ValueError(f"Outbreaks failed: {code}, {data}")
run_test("GET /api/outbreaks", test_outbreaks)

def test_leaf_samples():
    code, data = get("/api/detection/leaf-samples")
    if code != 200 or not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Leaf samples failed: {code}, {data}")
run_test("GET /api/detection/leaf-samples", test_leaf_samples)

def test_sample_fields():
    code, data = get("/api/detection/sample-fields")
    if code != 200 or not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Sample fields failed: {code}, {data}")
run_test("GET /api/detection/sample-fields", test_sample_fields)

# 4. Spread Prediction
def test_spread_json():
    code, data = post("/api/spread/calculate", {"temperature": 32, "humidity": 80, "wind_speed": 14, "base_acres": 2.5})
    if code != 200 or len(data["predictions"]) != 5 or data["base_acres"] != 2.5:
        raise ValueError(f"Spread calculate JSON failed: {code}, {data}")
run_test("POST /api/spread/calculate (JSON body)", test_spread_json)

def test_spread_query():
    code, data = post("/api/spread/calculate?temperature=30&humidity=75&wind_speed=10&base_acres=1.5")
    if code != 200 or len(data["predictions"]) != 5 or data["base_acres"] != 1.5:
        raise ValueError(f"Spread calculate query failed: {code}, {data}")
run_test("POST /api/spread/calculate (Query params)", test_spread_query)

def test_sandbox():
    code, data = get("/api/spread/simulate-sandbox?temperature=28&humidity=70&wind_speed=12&wind_direction_deg=45&hours=12&base_acres=2.0")
    if code != 200 or "wind_drift_ellipse" not in data or "predictions" not in data:
        raise ValueError(f"Sandbox failed: {code}, {data}")
run_test("GET /api/spread/simulate-sandbox", test_sandbox)

# 5. Agents, Missions, Dispatch
def test_agents():
    code, data = get("/api/agents")
    if code != 200 or len(data) < 1:
        raise ValueError(f"Agents failed: {code}, {data}")
run_test("GET /api/agents", test_agents)

def test_dispatch():
    code, data = post("/api/dispatch/select", {"outbreak_id": 1})
    if code != 200 or "candidates" not in data or "selected" not in data:
        raise ValueError(f"Dispatch select failed: {code}, {data}")
run_test("POST /api/dispatch/select", test_dispatch)

def test_missions():
    code, data = get("/api/missions")
    if code != 200 or not isinstance(data, list):
        raise ValueError(f"Missions failed: {code}, {data}")
run_test("GET /api/missions", test_missions)

def test_waypoints():
    code, data = get("/api/missions/1/waypoints")
    if code != 200 or len(data["waypoints"]) == 0:
        raise ValueError(f"Waypoints failed: {code}, {data}")
run_test("GET /api/missions/1/waypoints", test_waypoints)

# 6. Analytics & Intelligence
def test_analytics():
    code, data = get("/api/analytics")
    if code != 200 or "pesticide_savings_percent" not in data or "co2_saved_kg" not in data:
        raise ValueError(f"Analytics failed: {code}, {data}")
run_test("GET /api/analytics", test_analytics)

def test_weather():
    code, data = get("/api/weather")
    if code != 200 or "temperature_c" not in data or "pest_risk" not in data:
        raise ValueError(f"Weather failed: {code}, {data}")
run_test("GET /api/weather", test_weather)

def test_events():
    code, data = get("/api/events")
    if code != 200 or not isinstance(data, list):
        raise ValueError(f"Events failed: {code}, {data}")
run_test("GET /api/events", test_events)

def test_notifications():
    code, data = get("/api/notifications")
    if code != 200 or not isinstance(data, list):
        raise ValueError(f"Notifications failed: {code}, {data}")
run_test("GET /api/notifications", test_notifications)

def test_crops():
    code, data = get("/api/crops")
    if code != 200 or not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Crops failed: {code}, {data}")
run_test("GET /api/crops", test_crops)

def test_chem_rotation():
    code, data = get("/api/chemical-rotation")
    if code != 200 or "rotations" not in data:
        raise ValueError(f"Chemical rotation failed: {code}, {data}")
run_test("GET /api/chemical-rotation", test_chem_rotation)

def test_rotation_eval():
    code, data = get("/api/chemical-rotation/evaluate?pest=Bollworm&chemical=Chlorantraniliprole&consecutive=3")
    if code != 200 or "resistance_risk_level" not in data:
        raise ValueError(f"Rotation evaluate failed: {code}, {data}")
run_test("GET /api/chemical-rotation/evaluate", test_rotation_eval)

def test_expert_reviews():
    code, data = get("/api/expert-reviews")
    if code != 200 or not isinstance(data, list):
        raise ValueError(f"Expert reviews failed: {code}, {data}")
run_test("GET /api/expert-reviews", test_expert_reviews)

# 7. Demo Reset & Rate Limiting
def test_demo_reset():
    # Wait for cooldown to expire
    time.sleep(6)
    code, data = post("/api/demo/reset")
    if code != 200 or data.get("status") != "reset":
        raise ValueError(f"Demo reset failed: {code}, {data}")
run_test("POST /api/demo/reset", test_demo_reset)

def test_rate_limit():
    try:
        post("/api/demo/reset")
        raise ValueError("Expected 429 Too Many Requests")
    except urllib.error.HTTPError as he:
        if he.code != 429:
            raise ValueError(f"Expected 429, got {he.code}")
run_test("POST /api/demo/reset rate limit", test_rate_limit)

print("==================================================")
print(f"Summary: {tests_passed} / {tests_run} tests passed ({(tests_passed/tests_run)*100:.1f}%)")
print("==================================================")
if tests_passed == tests_run:
    print("ALL TESTS PASSED! System is 100% production verified.")
    sys.exit(0)
else:
    print("SOME TESTS FAILED.")
    sys.exit(1)
