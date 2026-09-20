# -*- coding: utf-8 -*-
"""Render designed diagram PNGs for the FarmShield deck (transparent, high-res)."""
import os, math
from PIL import Image, ImageDraw, ImageFont

SC = 3  # supersample scale (~300 dpi at slide size)
OUT = "viz"
os.makedirs(OUT, exist_ok=True)

# palette (matches FarmShield app)
GREEN   = (46, 93, 56)
GREEN_D = (28, 58, 36)
GREEN_XD= (16, 33, 20)
GREEN_L = (207, 227, 210)
AMBER   = (212, 130, 30)
RED     = (179, 74, 62)
WHITE   = (255, 255, 255)
PALE    = (207, 227, 210)
MUTED   = (155, 161, 154)
CARD_D  = (30, 30, 30)

def F(bold=False, size=18):
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    try:
        return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
    except Exception:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)

PANEL   = (24, 24, 24)
PANEL_LN= (58, 58, 58)

def canvas(w, h):
    # opaque dark panel (matches template cards); RGBA-mode draw enables real alpha blending
    img = Image.new("RGB", (w * SC, h * SC), PANEL)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((SC, SC, w * SC - SC, h * SC - SC), radius=14 * SC, outline=PANEL_LN, width=SC)
    return img, d

def save(img, name):
    img.save(f"{OUT}/{name}.png")
    print("wrote", f"{OUT}/{name}.png", img.size)

def arrow_h(d, x0, y, x1, color, w=3, head=14):
    d.line([(x0, y), (x1 - head, y)], fill=color, width=w)
    d.polygon([(x1, y), (x1 - head, y - head * 0.55), (x1 - head, y + head * 0.55)], fill=color)

def arrow_v(d, x, y0, y1, color, w=3, head=14):
    d.line([(x, y0), (x, y1 - head)], fill=color, width=w)
    d.polygon([(x, y1), (x - head * 0.55, y1 - head), (x + head * 0.55, y1 - head)], fill=color)

def rrect(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def text_c(d, cx, cy, s, font, color):
    bb = d.textbbox((0, 0), s, font=font)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), s, font=font, fill=color)

# ── simple icons (all geometric, drawn at unit size then placed) ──
def icon_phone(d, x, y, s, color):
    rrect(d, (x, y, x + s * 0.62, y + s), r=s * 0.12, outline=color, width=max(2, SC))
    d.line([(x + s * 0.24, y + s * 0.88), (x + s * 0.38, y + s * 0.88)], fill=color, width=max(2, SC))

def icon_camera(d, x, y, s, color):
    rrect(d, (x, y + s * 0.18, x + s, y + s * 0.9), r=s * 0.14, outline=color, width=max(2, SC))
    d.ellipse((x + s * 0.3, y + s * 0.36, x + s * 0.7, y + s * 0.74), outline=color, width=max(2, SC))
    rrect(d, (x + s * 0.28, y, x + s * 0.72, y + s * 0.2), r=s * 0.06, fill=color)

def icon_radar(d, x, y, s, color):
    for i, f in enumerate((1.0, 0.66, 0.33)):
        d.ellipse((x + s * (1 - f) / 2, y + s * (1 - f) / 2, x + s - s * (1 - f) / 2, y + s - s * (1 - f) / 2),
                  outline=color, width=max(2, SC - i))
    d.ellipse((x + s * 0.44, y + s * 0.44, x + s * 0.56, y + s * 0.56), fill=color)

def icon_chart(d, x, y, s, color):
    for i, hh in enumerate((0.4, 0.7, 1.0)):
        rrect(d, (x + s * (0.12 + i * 0.3), y + s * (1 - hh), x + s * (0.3 + i * 0.3), y + s),
              r=s * 0.04, fill=color)

def icon_drone(d, x, y, s, color):
    c = s / 2
    d.line([(x + s * 0.2, y + s * 0.2), (x + s * 0.8, y + s * 0.8)], fill=color, width=max(2, SC))
    d.line([(x + s * 0.8, y + s * 0.2), (x + s * 0.2, y + s * 0.8)], fill=color, width=max(2, SC))
    d.ellipse((x + c - s * 0.14, y + c - s * 0.14, x + c + s * 0.14, y + c + s * 0.14), fill=color)
    for dx, dy in ((0.16, 0.16), (0.84, 0.16), (0.16, 0.84), (0.84, 0.84)):
        d.ellipse((x + s * dx - s * 0.09, y + s * dy - s * 0.09, x + s * dx + s * 0.09, y + s * dy + s * 0.09),
                  outline=color, width=max(2, SC))

def icon_shield(d, x, y, s, color):
    w = s * 0.86
    d.polygon([(x + s * 0.5, y), (x + w, y + s * 0.18), (x + w, y + s * 0.55),
               (x + s * 0.5, y + s), (x, y + s * 0.55), (x, y + s * 0.18)],
              outline=color, width=max(2, SC))
    d.line([(x + s * 0.3, y + s * 0.48), (x + s * 0.45, y + s * 0.64), (x + s * 0.72, y + s * 0.3)],
           fill=color, width=max(3, SC))

def icon_gear(d, x, y, s, color):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.34
    for i in range(8):
        a = i * math.pi / 4
        d.line([(cx + r * math.cos(a), cy + r * math.sin(a)),
                (cx + r * 1.5 * math.cos(a), cy + r * 1.5 * math.sin(a))], fill=color, width=max(3, SC))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=max(2, SC))
    d.ellipse((cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4), fill=color)

ICONS = {"phone": icon_phone, "camera": icon_camera, "radar": icon_radar,
         "chart": icon_chart, "drone": icon_drone, "shield": icon_shield, "gear": icon_gear}

# ═══════════ 1. SOLUTION PIPELINE (vertical, 6 stages, icons) ═══════════
def pipeline():
    W, H = 560, 980
    img, d = canvas(W, H)
    stages = [
        ("Farmer sends crop photo",        "photo · voice · SMS",          "camera", GREEN),
        ("Outbreak detected",              "confirmed · 2.1 acres",        "radar",  GREEN_D),
        ("Spread predicted",               "14.2 ac in 24 h · microclimate","chart", GREEN),
        ("Best agent dispatched",          "DRONE-03 · 2.3 km · ~3 min",   "gear",   GREEN_D),
        ("Precision spot treatment",       "1.8 L vs 8.4 L blanket",       "drone",  GREEN),
        ("Contained — farmer notified",    "app · SMS · voice call",       "shield", GREEN_XD),
    ]
    x0, bw, bh, gap = 40 * SC, 420 * SC, 118 * SC, 56 * SC
    y = 30 * SC
    cy = [None] * len(stages)
    for i, (t1, t2, ic, col) in enumerate(stages):
        rrect(d, (x0, y, x0 + bw, y + bh), 18 * SC, fill=col + (235,))
        # icon disc
        disc = 74 * SC
        cx = x0 + bw - disc / 2 - 14 * SC
        dcy = y + bh / 2
        d.ellipse((cx - disc / 2, dcy - disc / 2, cx + disc / 2, dcy + disc / 2), fill=(255, 255, 255, 40))
        ICONS[ic](d, cx - 22 * SC, dcy - 22 * SC, 44 * SC, WHITE)
        f1, f2 = F(True, 26 * SC), F(False, 19 * SC)
        d.text((x0 + 24 * SC, y + 22 * SC), t1, font=f1, fill=WHITE)
        d.text((x0 + 24 * SC, y + 62 * SC), t2, font=f2, fill=PALE)
        # number badge
        d.ellipse((x0 - 16 * SC, y + bh / 2 - 16 * SC, x0 + 16 * SC, y + bh / 2 + 16 * SC),
                  fill=AMBER if i in (4,) else WHITE)
        text_c(d, x0, y + bh / 2, str(i + 1), F(True, 20 * SC), GREEN_XD)
        cy[i] = y + bh / 2
        if i < len(stages) - 1:
            arrow_v(d, x0 + bw / 2, y + bh + 4 * SC, y + bh + gap - 4 * SC, PALE, w=4 * SC, head=16 * SC)
        y += bh + gap
    save(img, "pipeline")

# ═══════════ 2. SWIM-LANE ARCHITECTURE ═══════════
def architecture():
    W, H = 1180, 760
    img, d = canvas(W, H)
    lanes = [
        ("FARMER",        30,  "phone",  GREEN_L),
        ("FARMSHIELD BACKEND", 290, "gear", None),
        ("FIELD AGENTS",  550, "drone",  None),
    ]
    # lane bands
    lane_h = 170 * SC
    lane_y = [40 * SC, 270 * SC, 500 * SC]
    band_col = [(255, 255, 255, 26), (255, 255, 255, 14), (255, 255, 255, 26)]
    for (name, _, ic, _), ly, bc in zip(lanes, lane_y, band_col):
        rrect(d, (16 * SC, ly, W - 16 * SC, ly + lane_h), 20 * SC, fill=bc)
        f = F(True, 26 * SC)
        d.text((36 * SC, ly + 10 * SC), name, font=f, fill=PALE)
        ICONS[ic](d, W - 80 * SC, ly + 14 * SC, 34 * SC, PALE)
    def node(lx, ly, w, h, t1, t2, fill, tcol=WHITE, scol=PALE):
        rrect(d, (lx, ly, lx + w, ly + h), 14 * SC, fill=fill)
        text_c(d, lx + w / 2, ly + h * 0.36, t1, F(True, 24 * SC), tcol)
        text_c(d, lx + w / 2, ly + h * 0.72, t2, F(False, 17 * SC), scol)
        return lx + w / 2, ly + h / 2
    # lane 1 nodes
    n1 = node(200 * SC, 80 * SC, 300 * SC, 90 * SC, "Crop photo report", "photo · voice · SMS", GREEN)
    n2 = node(660 * SC, 80 * SC, 330 * SC, 90 * SC, "Advice & alerts", "app · SMS · IVR · 7 languages", GREEN)
    # lane 2 nodes
    n3 = node(150 * SC, 315 * SC, 280 * SC, 90 * SC, "Detection Agent", "possible outbreak confirmed", GREEN_D)
    n4 = node(460 * SC, 315 * SC, 280 * SC, 90 * SC, "Prediction Engine", "2.1 → 14.2 ac · microclimate", GREEN_D)
    n5 = node(770 * SC, 315 * SC, 260 * SC, 90 * SC, "Dispatch Engine", "travel × battery × payload", GREEN_D)
    # lane 3 nodes
    n6 = node(180 * SC, 545 * SC, 270 * SC, 90 * SC, "Spray Drone DR-03", "en-route → treat", GREEN)
    n7 = node(640 * SC, 545 * SC, 300 * SC, 90 * SC, "Mission Controller", "state machine · event log", GREEN)
    arrow_h(d, n1[0] + 150 * SC, 125 * SC, n2[0] - 165 * SC, PALE, w=3 * SC)
    arrow_v(d, n1[0], 170 * SC, 315 * SC, PALE, w=3 * SC, head=15 * SC)
    arrow_h(d, n3[0] + 140 * SC, 360 * SC, n4[0] - 140 * SC, PALE, w=3 * SC)
    arrow_h(d, n4[0] + 140 * SC, 360 * SC, n5[0] - 130 * SC, PALE, w=3 * SC)
    arrow_v(d, n5[0], 405 * SC, 545 * SC, PALE, w=3 * SC, head=15 * SC)
    arrow_h(d, n6[0] + 135 * SC, 590 * SC, n7[0] - 150 * SC, PALE, w=3 * SC)
    arrow_v(d, n7[0], 545 * SC, 405 * SC, AMBER, w=3 * SC, head=15 * SC)
    arrow_v(d, n2[0], 315 * SC, 170 * SC, PALE, w=3 * SC, head=15 * SC)
    # feedback loop label
    f = F(False, 17 * SC)
    d.text((n7[0] + 20 * SC, 458 * SC), "status back", font=f, fill=AMBER)
    d.text((n1[0] + 16 * SC, 238 * SC), "report up", font=f, fill=PALE)
    save(img, "architecture")

# ═══════════ 3. OUTBREAK GROWTH CURVE (untreated vs treated) ═══════════
def growth():
    W, H = 760, 560
    img, d = canvas(W, H)
    L, R, T, B = 90 * SC, 700 * SC, 60 * SC, 470 * SC
    # axes
    d.line([(L, T), (L, B), (R, B)], fill=MUTED, width=2 * SC)
    fy = F(False, 24 * SC)
    for acres, frac in ((0, 0), (5, .5), (10, 1.0), (15, 1.5)):
        yy = B - (B - T) * frac / 1.5
        d.line([(L, yy), (R, yy)], fill=(120, 120, 120, 60), width=SC)
        d.text((L - 74 * SC, yy - 14 * SC), f"{acres}", font=fy, fill=MUTED)
    d.text((L - 78 * SC, T - 40 * SC), "acres", font=fy, fill=MUTED)
    for i, hlab in enumerate(("now", "6 h", "12 h", "18 h", "24 h")):
        xx = L + (R - L) * i / 4
        d.text((xx - 24 * SC, B + 16 * SC), hlab, font=fy, fill=MUTED)
    pts_u = [(0, 2.1), (0.25, 5.5), (0.5, 8.7), (0.75, 11.4), (1, 14.2)]
    pts_t = [(0, 2.1), (0.25, 2.3), (0.5, 2.4), (0.75, 2.5), (1, 2.6)]
    def plot(pts, col, wpx, dash=False):
        prev = None
        for i, (fx, ay) in enumerate(pts):
            x = L + (R - L) * fx
            y = B - (B - T) * ay / 15.0
            if prev:
                if dash:
                    steps = 12
                    for s_ in range(steps):
                        if s_ % 2:
                            continue
                        xa = prev[0] + (x - prev[0]) * s_ / steps
                        ya = prev[1] + (y - prev[1]) * s_ / steps
                        xb = prev[0] + (x - prev[0]) * (s_ + 1) / steps
                        yb = prev[1] + (y - prev[1]) * (s_ + 1) / steps
                        d.line([(xa, ya), (xb, yb)], fill=col, width=wpx)
                else:
                    d.line([(prev[0], prev[1]), (x, y)], fill=col, width=wpx)
            prev = (x, y)
    plot(pts_u, RED, 6 * SC)
    plot(pts_t, GREEN_L, 5 * SC, dash=True)
    # endpoint dots + labels
    ye = B - (B - T) * 14.2 / 15.0
    yt = B - (B - T) * 2.6 / 15.0
    d.ellipse((R - 11 * SC, ye - 11 * SC, R + 11 * SC, ye + 11 * SC), fill=RED)
    d.text((R - 200 * SC, ye - 62 * SC), "14.2 ac untreated", font=F(True, 26 * SC), fill=RED)
    d.ellipse((R - 11 * SC, yt - 11 * SC, R + 11 * SC, yt + 11 * SC), fill=GREEN_L)
    d.text((R - 268 * SC, yt - 64 * SC), "2.6 ac with FarmShield", font=F(True, 26 * SC), fill=GREEN_L)
    # outbreak start marker
    ys = B - (B - T) * 2.1 / 15.0
    d.text((L + 6 * SC, ys - 52 * SC), "detected at 2.1 ac", font=F(True, 22 * SC), fill=PALE)
    save(img, "growth")

# ═══════════ 4. RESPONSE TIMELINE (horizontal) ═══════════
def timeline():
    W, H = 1180, 300
    img, d = canvas(W, H)
    events = [
        ("0:00", "Photo sent",        "camera"),
        ("0:02", "Outbreak confirmed", "radar"),
        ("0:05", "Drone dispatched",  "gear"),
        ("0:08", "Treatment started", "drone"),
        ("0:19", "Contained",         "shield"),
    ]
    y = 120 * SC
    x0, x1 = 90 * SC, 1090 * SC
    # base line
    d.line([(x0, y), (x1, y)], fill=(255, 255, 255, 70), width=6 * SC)
    # progress overlay (green) to ~0:19 (full)
    d.line([(x0, y), (x1, y)], fill=GREEN, width=6 * SC)
    n = len(events)
    for i, (t, lab, ic) in enumerate(events):
        x = x0 + (x1 - x0) * i / (n - 1)
        d.ellipse((x - 34 * SC, y - 34 * SC, x + 34 * SC, y + 34 * SC),
                  fill=GREEN_XD if i == n - 1 else GREEN, outline=WHITE, width=2 * SC)
        ICONS[ic](d, x - 17 * SC, y - 17 * SC, 34 * SC, WHITE)
        f1 = F(True, 30 * SC)
        text_c(d, x, y - 84 * SC, t, f1, AMBER if i == n - 1 else WHITE)
        text_c(d, x, y + 70 * SC, lab, F(False, 24 * SC), PALE)
    text_c(d, (x0 + x1) / 2, 254 * SC, "end-to-end autonomous response — 19 seconds (prototype demo)",
           F(False, 20 * SC), MUTED)
    save(img, "timeline")

# ═══════════ 5. COMPARISON BARS (pesticide + response time) ═══════════
def compare():
    W, H = 1180, 360
    img, d = canvas(W, H)
    L = 250 * SC
    def bars(y, lab, old, new, unit, old_w, new_w, tag):
        f = F(True, 18 * SC)
        d.text((30 * SC, y + 14 * SC), lab, font=f, fill=WHITE)
        rrect(d, (L, y, L + old_w, y + 52 * SC), 10 * SC, fill=RED + (235,))
        d.text((L + old_w + 16 * SC, y + 12 * SC), old + unit, font=F(True, 17 * SC), fill=RED)
        rrect(d, (L, y + 72 * SC, L + new_w, y + 124 * SC), 10 * SC, fill=GREEN + (235,))
        d.text((L + new_w + 16 * SC, y + 84 * SC), new + unit, font=F(True, 17 * SC), fill=GREEN_L)
        text_c(d, L + old_w / 2, y + 26 * SC, "blanket spraying", F(True, 15 * SC), WHITE)
        text_c(d, L + new_w / 2, y + 98 * SC, "FarmShield", F(True, 15 * SC), WHITE)
        # tag chip on the right
        tw = 210 * SC
        tx = L + max(old_w, new_w) + 120 * SC
        rrect(d, (tx, y + 30 * SC, tx + tw, y + 88 * SC), 33 * SC, fill=AMBER + (235,))
        text_c(d, tx + tw / 2, y + 59 * SC, tag, F(True, 16 * SC), (20, 16, 8))
    bars(40 * SC,  "Pesticide",  "8.4 L", "1.8 L", "", 620 * SC, 133 * SC, "−78.6% *")
    bars(210 * SC, "Response",   "days",  "19 min", "", 620 * SC, 150 * SC, "days → minutes")
    d.text((30 * SC, 330 * SC), "* prototype estimate — same 2.1-acre outbreak, demo mission data",
           font=F(False, 13.5 * SC), fill=MUTED)
    save(img, "compare")

# ═══════════ 6. PHONE BEZELS (composite of 4 shots) ═══════════
def rounded(im, rad_frac=0.04):
    """Return the image with rounded corners (transparent outside)."""
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(w * rad_frac), fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out

def bezel(path):
    im = rounded(Image.open(path).convert("RGBA"), rad_frac=0.035)
    iw, ih = im.size
    # bezel margins
    m = int(iw * 0.035)
    W, H = iw + 2 * m, ih + 2 * m + int(m * 0.2)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(out, "RGBA")
    rrect(d, (0, 0, W - 1, H - 1), int(W * 0.06), fill=(24, 24, 24, 255), outline=(70, 70, 70, 255), width=SC)
    out.paste(im, (m, m + int(m * 0.2)), im)
    # speaker notch
    d.rounded_rectangle((W / 2 - m * 1.1, m + int(m * 0.35), W / 2 + m * 1.1, m + int(m * 0.9)),
                        radius=6 * SC, fill=(60, 60, 60, 255))
    return out

def phones():
    shots = ["shots/farmer_home.png", "shots/farmer_tamil.png", "shots/farmer_result.png", "shots/farmer_alerts.png"]
    caps  = ["Home · alert card", "Tamil interface", "Scan result", "Alerts + SMS/IVR"]
    bzs = [bezel(p) for p in shots]
    bw = max(b.width for b in bzs)
    bh = max(b.height for b in bzs)
    gap = 46 * SC
    W = len(bzs) * bw + (len(bzs) - 1) * gap + 20 * SC
    H = bh + 70 * SC
    img = Image.new("RGB", (W, H), PANEL)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((SC, SC, W * SC - SC, H * SC - SC), radius=14 * SC, outline=PANEL_LN, width=SC)
    x = 10 * SC
    for b, cap in zip(bzs, caps):
        img.paste(b, (x, 0), b)
        text_c(d, x + b.width / 2, bh + 32 * SC, cap, F(False, 18 * SC), PALE)
        x += bw + gap
    save(img, "phones")

# ═══════════ 7. FIELD MAP SCHEMATIC (for title slide) ═══════════
def fieldmap():
    W, H = 640, 480
    img, d = canvas(W, H)
    # field boundary
    rrect(d, (40 * SC, 40 * SC, 600 * SC, 440 * SC), 18 * SC, outline=GREEN_L, width=3 * SC)
    # plot polygons (green healthy, one red-ish with outbreak)
    plots = [
        ([(70, 70), (250, 70), (230, 200), (70, 220)], GREEN_D + (200,)),
        ([(280, 70), (460, 70), (470, 190), (270, 205)], GREEN + (200,)),
        ([(490, 70), (590, 80), (580, 210), (500, 195)], GREEN + (200,)),
        ([(70, 250), (230, 235), (240, 400), (70, 410)], GREEN + (200,)),
        ([(270, 240), (460, 225), (450, 410), (280, 415)], (120, 60, 50, 220)),
        ([(490, 240), (580, 245), (585, 415), (480, 410)], GREEN + (200,)),
    ]
    for pts, col in plots:
        d.polygon([(x * SC, y * SC) for x, y in pts], fill=col, outline=(0, 0, 0, 0))
    # outbreak marker + spread rings
    cx, cy = 365, 320
    for r, a in ((52, 90), (36, 130), (22, 180)):
        d.ellipse(((cx - r) * SC, (cy - r) * SC, (cx + r) * SC, (cy + r) * SC), outline=RED + (a,), width=3 * SC)
    d.ellipse(((cx - 8) * SC, (cy - 8) * SC, (cx + 8) * SC, (cy + 8) * SC), fill=RED + (255,))
    # drone en-route
    dx, dy = 150, 380
    d.line([(dx * SC, dy * SC), (cx * SC, cy * SC)], fill=AMBER + (200,), width=3 * SC)
    icon_drone(d, (dx - 16) * SC, (dy - 16) * SC, 32 * SC, AMBER)
    # legend
    lx, ly = 462, 60
    d.ellipse((lx * SC, ly * SC, (lx + 12) * SC, (ly + 12) * SC), fill=GREEN + (230,))
    d.text(((lx + 20) * SC, (ly - 4) * SC), "healthy", font=F(False, 14 * SC), fill=PALE)
    d.ellipse((lx * SC, (ly + 26) * SC, (lx + 12) * SC, (ly + 38) * SC), fill=(120, 60, 50, 230))
    d.text(((lx + 20) * SC, (ly + 22) * SC), "outbreak", font=F(False, 14 * SC), fill=PALE)
    d.ellipse((lx * SC, (ly + 52) * SC, (lx + 12) * SC, (ly + 64) * SC), outline=RED + (180,), width=2 * SC)
    d.text(((lx + 20) * SC, (ly + 48) * SC), "predicted spread", font=F(False, 14 * SC), fill=PALE)
    save(img, "fieldmap")

pipeline()
architecture()
growth()
timeline()
compare()
try:
    phones()
except Exception as e:
    print("PHONES FAILED:", e)
fieldmap()
print("all diagrams rendered")
