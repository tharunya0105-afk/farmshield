"""
Download real crop field images from Wikimedia Commons for the aerial scan demo.
All images are public domain or CC-licensed.
"""
import os, urllib.request, json

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_fields")
os.makedirs(OUT, exist_ok=True)

# Real field images from Wikimedia Commons (public domain / CC)
SAMPLES = [
    {
        "name": "cotton_field_aerial.jpg",
        "description": "Aerial view of a cotton field in Tamil Nadu",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Cotton_field_in_Madhya_Pradesh.jpg/1280px-Cotton_field_in_Madhya_Pradesh.jpg",
    },
    {
        "name": "tomato_field_diseased.jpg",
        "description": "Tomato field showing late blight symptoms",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Tomato_late_blight_2.jpg/1280px-Tomato_late_blight_2.jpg",
    },
    {
        "name": "rice_field_green.jpg",
        "description": "Healthy rice paddy field, aerial view",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Paddy_field_in_Kuttanad.jpg/1280px-Paddy_field_in_Kuttanad.jpg",
    },
]

manifest = []
for s in SAMPLES:
    path = os.path.join(OUT, s["name"])
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        print(f"  [skip] {s['name']} already exists ({os.path.getsize(path)} bytes)")
        manifest.append({"name": s["name"], "description": s["description"], "size": os.path.getsize(path)})
        continue
    try:
        print(f"  [download] {s['name']}...")
        req = urllib.request.Request(s["url"], headers={"User-Agent": "FarmShield/1.0 (hackathon)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        print(f"    saved {len(data)} bytes")
        manifest.append({"name": s["name"], "description": s["description"], "size": len(data)})
    except Exception as e:
        print(f"    FAILED: {e}")

# save manifest
with open(os.path.join(OUT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print(f"\nmanifest: {len(manifest)} samples in {OUT}")
