"""
FarmShield — real leaf-image classifier (PlantVillage MobileNetV2, ONNX graph).

Runs on OpenCV's DNN module (no torch / onnxruntime needed on Windows Store Python).
38 classes across 14 plants (tomato, potato, corn, apple, grape, ...).
Loaded lazily so server startup and the autonomous demo never depend on it.
Falls back gracefully: caller decides what to do on any failure.
"""
import json, os, threading
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "model_store", "plantvillage_mobilenetv2.onnx")
CONFIG_PATH = os.path.join(BASE, "model_store", "config.json")

_lock = threading.Lock()
_net = None
_labels = None
_cv2 = None

# MobileNetV2 image processor: resize shortest->256, center-crop 224,
# normalize to (x/255 - 0.5)/0.5  ==  x/127.5 - 1  (matches blobFromImage below)
INPUT_SIZE = 224


def _load():
    """Lazily build the DNN net and label list. Raises on failure."""
    global _net, _labels, _cv2
    if _net is not None:
        return
    with _lock:
        if _net is not None:
            return
        import cv2
        _cv2 = cv2
        _net = cv2.dnn.readNetFromONNX(MODEL_PATH)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        _labels = [cfg["id2label"][str(i)] for i in range(len(cfg["id2label"]))]


def available() -> bool:
    try:
        _load()
        return True
    except Exception:
        return False


def status() -> dict:
    """Model status for the health/UI surface — never raises."""
    ok = available()
    return {
        "model": "PlantVillage MobileNetV2 (CNN)" if ok else None,
        "classes": len(_labels) if ok else 0,
        "mode": "REAL_MODEL" if ok else "DEMO_SIMULATION",
    }


def classify(img_bytes: bytes):
    """
    Run the real model on a photo (jpg/png bytes).
    Returns (label, confidence). Raises on failure so the caller can fall back honestly.
    """
    _load()
    arr = np.frombuffer(img_bytes, np.uint8)
    img = _cv2.imdecode(arr, _cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("unreadable image")
    # scalefactor 1/127.5 + mean (1,1,1) => x/127.5 - 1 == (x/255 - .5)/.5 ; swapRB for RGB; crop=True
    blob = _cv2.dnn.blobFromImage(img, scalefactor=1 / 127.5, size=(INPUT_SIZE, INPUT_SIZE),
                                  mean=(1, 1, 1), swapRB=True, crop=True)
    _net.setInput(blob)
    logits = _net.forward()[0]
    return _labels[int(logits.argmax())], float(_softmax(logits)[int(logits.argmax())])


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# ─── label → FarmShield result mapping ───────────────────────────────────────
_PLANT_ALIASES = {
    "Apple": "Apple", "Blueberry": "Blueberry", "Cherry": "Cherry", "Corn": "Corn",
    "Maize": "Corn", "Grape": "Grape", "Orange": "Citrus", "Citrus": "Citrus",
    "Peach": "Peach", "Pepper": "Bell Pepper", "Bell": "Bell Pepper",
    "Potato": "Potato", "Raspberry": "Raspberry", "Soybean": "Soybean",
    "Squash": "Squash", "Strawberry": "Strawberry", "Tomato": "Tomato",
}

# friendly pest names for the classes farmers actually bring
_FRIENDLY_PEST = {
    "Tomato with Late Blight": "Late Blight",
    "Tomato with Early Blight": "Early Blight",
    "Tomato with Bacterial Spot": "Bacterial Spot",
    "Tomato with Leaf Mold": "Leaf Mold",
    "Tomato with Septoria Leaf Spot": "Septoria Leaf Spot",
    "Tomato with Target Spot": "Target Spot",
    "Tomato Yellow Leaf Curl Virus": "Yellow Leaf Curl Virus",
    "Tomato Mosaic Virus": "Mosaic Virus",
    "Tomato with Spider Mites or Two-spotted Spider Mite": "Spider Mite damage",
    "Potato with Late Blight": "Late Blight",
    "Potato with Early Blight": "Early Blight",
    "Corn (Maize) with Common Rust": "Common Rust",
    "Corn (Maize) with Northern Leaf Blight": "Northern Leaf Blight",
    "Corn (Maize) with Cercospora and Gray Leaf Spot": "Gray Leaf Spot",
    "Apple Scab": "Apple Scab",
    "Apple with Black Rot": "Black Rot",
    "Grape with Black Rot": "Black Rot",
    "Grape with Esca (Black Measles)": "Esca (Black Measles)",
    "Grape with Isariopsis Leaf Spot": "Leaf Spot",
    "Orange with Citrus Greening": "Citrus Greening (HLB)",
    "Peach with Bacterial Spot": "Bacterial Spot",
    "Bell Pepper with Bacterial Spot": "Bacterial Spot",
    "Strawberry with Leaf Scorch": "Leaf Scorch",
    "Squash with Powdery Mildew": "Powdery Mildew",
    "Cherry with Powdery Mildew": "Powdery Mildew",
}


def _plant_of(label: str):
    for token, plant in _PLANT_ALIASES.items():
        if token.lower() in label.lower():
            return plant
    return None


def is_healthy(label: str) -> bool:
    return "healthy" in label.lower()


def severity_for(conf: float) -> str:
    """High for confident disease, medium for moderate, else low."""
    if conf >= 0.80:
        return "High"
    if conf >= 0.55:
        return "Medium"
    return "Low"


def describe(label: str, conf: float) -> dict:
    """
    Map a raw model label + confidence into the FarmShield result shape.
    {healthy: bool, crop, possible_pest, risk}
    """
    if is_healthy(label):
        return {"healthy": True, "crop": _plant_of(label) or "Crop",
                "possible_pest": None, "risk": "Low"}
    plant = _plant_of(label)
    pest = _FRIENDLY_PEST.get(label, label)
    return {"healthy": False, "crop": plant or "Crop",
            "possible_pest": pest, "risk": severity_for(conf)}
