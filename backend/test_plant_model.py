# -*- coding: utf-8 -*-
"""Validate the real classifier against genuine PlantVillage photos (5 per class)."""
import json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plant_model

BASE = "https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color/"
HEAD = {"User-Agent": "farmshield-test"}

CASES = [
    ("Tomato___Late_blight", "Late Blight", "Tomato"),
    ("Tomato___healthy", None, "Tomato"),          # None pest = expect healthy
    ("Potato___Early_blight", "Early Blight", "Potato"),
    ("Corn___Common_rust_", "Common Rust", "Corn"),
    ("Apple___Apple_scab", "Apple Scab", "Apple"),
    ("Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Yellow Leaf Curl Virus", "Tomato"),
]


def gh_files(folder, n=5):
    url = BASE + folder
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return [it["download_url"] for it in data if it["name"].lower().endswith((".jpg", ".png"))][:n]


total_ok = total_n = 0
for folder, want_pest, want_crop in CASES:
    try:
        urls = gh_files(folder)
    except Exception as e:
        print(f"{folder}: FETCH ERROR {e}")
        continue
    ok = 0
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=HEAD)
            with urllib.request.urlopen(req, timeout=30) as r:
                img = r.read()
            label, conf = plant_model.classify(img)
            desc = plant_model.describe(label, conf)
            if want_pest is None:
                hit = desc["healthy"]
            else:
                hit = (desc["possible_pest"] == want_pest)
            ok += bool(hit)
            total_ok += bool(hit)
            total_n += 1
            mark = "OK " if hit else "MISS"
            print(f"  [{mark}] {u.rsplit('/',1)[-1][:38]:40s} -> {label:38s} {conf*100:5.1f}%  pest={desc['possible_pest']}")
        except Exception as e:
            print(f"  [ERR] {u.rsplit('/',1)[-1][:38]:40s} {e}")
            total_n += 1
    print(f"{folder}: {ok}/{len(urls)}\n")

print(f"TOTAL: {total_ok}/{total_n} correct ({(total_ok/total_n*100 if total_n else 0):.0f}%)")
print("model status:", plant_model.status())
