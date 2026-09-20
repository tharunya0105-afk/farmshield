"""
FarmShield — Aerial Scan Detection Agent

Runs the real PlantVillage CNN on a field image split into tiles.
Clusters hot tiles (disease detections) into infection zones with
coordinates, confidence, and estimated acreage.

This is REAL inference — the same MobileNetV2 that classifies farmer
leaf photos, applied per-tile over field/drone imagery. The honest
framing: "real CNN per-tile; accuracy improves with closer imagery
and multispectral input."

For hackathon demo: works with any crop/drone/aerial photo.
For production: swap CNN for a multispectral-trained model.
"""
import io, os, math, numpy as np
from typing import Optional

# grid size for tile scanning (6x6 = 36 tiles per image)
GRID = 6
DISEASE_CONF_THRESHOLD = 0.45   # tile is "hot" if disease confidence >= this
HEALTHY_CONF_THRESHOLD = 0.60   # tile is "definitely healthy" if confidence >= this


def _tile_bytes_to_cv2(img_bytes: bytes):
    """Decode image bytes to cv2 array."""
    import cv2
    arr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _crop_grid(img, grid: int):
    """Split a cv2 image into grid×grid tiles. Returns list of (tile_cv2, row, col)."""
    h, w = img.shape[:2]
    tw, th = w // grid, h // grid
    tiles = []
    for r in range(grid):
        for c in range(grid):
            tile = img[r*th:(r+1)*th, c*tw:(c+1)*tw]
            tiles.append((tile, r, c))
    return tiles, tw, th


def scan_field(img_bytes: bytes, field_area_acres: float = 42.0,
               field_bbox: Optional[dict] = None):
    """
    Run the real CNN tile-scan on a field image.

    Args:
        img_bytes: raw image bytes (jpg/png)
        field_area_acres: total field area for acreage estimation
        field_bbox: optional {lat_min, lat_max, lon_min, lon_max} for GPS mapping

    Returns:
        {
            mode: "REAL_MODEL_AERIAL",
            grid: int,
            tiles: [{row, col, label, confidence, healthy, hot}],
            clusters: [{id, center_row, center_col, tiles, avg_confidence,
                         label, est_acres, lat, lon, bbox_px}],
            hot_count: int,
            total_tiles: int,
            healthy_fraction: float,
            detection_summary: str
        }
    """
    import plant_model, cv2

    img = _tile_bytes_to_cv2(img_bytes)
    if img is None:
        raise ValueError("unreadable image")

    tiles_data, tw, th = _crop_grid(img, GRID)
    h, w = img.shape[:2]

    tile_results = []
    hot_set = set()

    for cv2_tile, r, c in tiles_data:
        # convert tile to bytes for the classifier
        _, buf = cv2.imencode('.jpg', cv2_tile)
        raw = buf.tobytes()

        label, conf = plant_model.classify(raw)
        healthy = plant_model.is_healthy(label)

        # A tile is "hot" (disease detected) if:
        # - it's not healthy AND confidence >= threshold
        hot = (not healthy and conf >= DISEASE_CONF_THRESHOLD)
        if hot:
            hot_set.add((r, c))

        desc = plant_model.describe(label, conf)

        tile_results.append({
            "row": r, "col": c,
            "label": label,
            "confidence": round(conf, 4),
            "healthy": healthy,
            "hot": hot,
            "possible_pest": desc["possible_pest"],
            "risk": desc["risk"],
        })

    # ── cluster adjacent hot tiles (4-connected BFS) ──
    visited = set()
    clusters = []
    cluster_id = 0

    for r, c in hot_set:
        if (r, c) in visited:
            continue
        # BFS
        queue = [(r, c)]
        component = []
        while queue:
            cr, cc = queue.pop(0)
            if (cr, cc) in visited or (cr, cc) not in hot_set:
                continue
            visited.add((cr, cc))
            component.append((cr, cc))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < GRID and 0 <= nc < GRID and (nr, nc) in hot_set:
                    queue.append((nr, nc))

        if not component:
            continue

        # cluster geometry
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        center_r = sum(rows) / len(rows)
        center_c = sum(cols) / len(cols)

        # average confidence and most common pest
        cluster_tiles = [t for t in tile_results if (t["row"], t["col"]) in set(component)]
        avg_conf = sum(t["confidence"] for t in cluster_tiles) / len(cluster_tiles)
        pests = [t["possible_pest"] for t in cluster_tiles if t["possible_pest"]]
        main_pest = max(set(pests), key=pests.count) if pests else "Stress detected"

        # acreage: cluster tiles / total tiles × field area
        tile_frac = len(component) / (GRID * GRID)
        est_acres = round(tile_frac * field_area_acres, 2)

        # GPS mapping (linear interpolation across field bbox)
        lat = lon = None
        if field_bbox:
            lat = field_bbox["lat_min"] + (center_r / GRID) * (field_bbox["lat_max"] - field_bbox["lat_min"])
            lon = field_bbox["lon_min"] + (center_c / GRID) * (field_bbox["lon_max"] - field_bbox["lon_min"])

        # pixel bbox (for frontend overlay)
        bbox_px = {
            "x": min(c for _, c in component) * tw,
            "y": min(r for r, _ in component) * th,
            "w": (max(c for _, c in component) - min(c for _, c in component) + 1) * tw,
            "h": (max(r for r, _ in component) - min(r for r, _ in component) + 1) * th,
        }

        cluster_id += 1
        clusters.append({
            "id": cluster_id,
            "center_row": round(center_r, 1),
            "center_col": round(center_c, 1),
            "tile_count": len(component),
            "avg_confidence": round(avg_conf, 4),
            "main_pest": main_pest,
            "est_acres": est_acres,
            "lat": round(lat, 6) if lat else None,
            "lon": round(lon, 6) if lon else None,
            "bbox_px": bbox_px,
        })

    # sort clusters by severity (most tiles = worst)
    clusters.sort(key=lambda x: x["tile_count"], reverse=True)

    healthy_count = sum(1 for t in tile_results if t["healthy"])
    total = GRID * GRID

    summary = (
        f"{len(clusters)} infection zone{'s' if len(clusters) != 1 else ''} detected "
        f"({len(hot_set)} of {total} tiles hot, "
        f"{round(healthy_count/total*100)}% healthy)"
    ) if clusters else (
        f"No infection zones — {round(healthy_count/total*100)}% of {total} tiles classified as healthy"
    )

    return {
        "mode": "REAL_MODEL_AERIAL",
        "grid": GRID,
        "tiles": tile_results,
        "clusters": clusters,
        "hot_count": len(hot_set),
        "total_tiles": total,
        "healthy_fraction": round(healthy_count / total, 3),
        "est_total_disease_acres": round(sum(c["est_acres"] for c in clusters), 2),
        "detection_summary": summary,
        "image_width": w,
        "image_height": h,
    }
