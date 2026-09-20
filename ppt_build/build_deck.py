# -*- coding: utf-8 -*-
"""
Build FarmShield deck on the official HACKWELL 2.0 template — VISUAL FIRST.
Every template element preserved (text edited in place); overlays add flowcharts,
stat cards, comparison bars, timeline and a real app screenshot.
Output: C:\\Users\\USER\\Downloads\\FarmShield_AAA09_Hackwell2_0.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import struct

TMPL = r"C:\Users\USER\Downloads\H20_PPT_Template (1).pptx"
OUT  = r"C:\Users\USER\Downloads\FarmShield_AAA09_Hackwell2_0_v3.pptx"

# FarmShield agri palette (matches the app)
GREEN   = RGBColor(0x2E, 0x5D, 0x38)
GREEN_D = RGBColor(0x1C, 0x3A, 0x24)
GREEN_XD= RGBColor(0x14, 0x2A, 0x1A)
AMBER   = RGBColor(0xB4, 0x5F, 0x06)
RED_BAR = RGBColor(0x9E, 0x3B, 0x3B)
INK     = RGBColor(0x2A, 0x2E, 0x28)
GRAY    = RGBColor(0x6B, 0x71, 0x69)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
# dark-template text colors (template cards are dark — body text must be light)
LIGHT   = RGBColor(0xE8, 0xE8, 0xE0)
PALE    = RGBColor(0xCF, 0xE3, 0xD2)
DIM     = RGBColor(0x9B, 0xA1, 0x9A)
LINE    = RGBColor(0xD6, 0xD6, 0xCB)
DIV     = RGBColor(0x9A, 0x4A, 0x4A)   # divider inside maroon card

prs = Presentation(TMPL)
S = prs.slides

def set_text(shape, text, size=None, color=None, bold=None, align=None):
    """Replace all text of a shape, keeping its first run's formatting when possible."""
    tf = shape.text_frame
    p0 = tf.paragraphs[0]
    f = None
    if p0.runs:
        r0 = p0.runs[0]
        try:
            rgb = r0.font.color.rgb if r0.font.color and r0.font.color.type is not None else None
        except AttributeError:
            rgb = None
        f = (r0.font.name, r0.font.size, rgb, r0.font.bold)
    tf.clear()
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    if f and f[0]: run.font.name = f[0]
    if size: run.font.size = Pt(size)
    if f and f[2] and not color: run.font.color.rgb = f[2]
    if color: run.font.color.rgb = color
    if bold is not None: run.font.bold = bold
    elif f and f[3] is not None: run.font.bold = f[3]
    if align: p.alignment = align
    return run

def find(slide, contains):
    for sh in slide.shapes:
        if sh.has_text_frame and contains in sh.text_frame.text:
            return sh
    return None

def add_box(slide, l, t, w, h, text, size=12, color=INK, bold=False, fill=None,
            line=None, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=None, dash=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.01)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = bold
    r.font.name = font or "Inter"
    if fill is not None:
        tb.fill.solid(); tb.fill.fore_color.rgb = fill
    else:
        tb.fill.background()
    if line is not None:
        tb.line.color.rgb = line; tb.line.width = Pt(1)
        if dash:
            try:
                from pptx.enum.line import MSO_LINE
                tb.line.dash_style = MSO_LINE.DASH
            except Exception:
                pass
    else:
        tb.line.fill.background()
    return tb

def add_rect(slide, l, t, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is not None:
        sh.line.color.rgb = line; sh.line.width = Pt(0.75)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh

def add_chip(slide, l, t, w, h, text, fill, txt_color=WHITE, size=11, bold=True):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.adjustments[0] = 0.28
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.005)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = txt_color
    r.font.name = "Inter"
    return sh

def add_arrow(slide, l, t, w=0.22, h=0.16):
    sh = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = GREEN
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh

def add_arrow_down(slide, l, t, w=0.16, h=0.13):
    sh = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = GREEN
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh

def add_line_h(slide, l, t, w, color=GREEN, weight=2.2):
    from pptx.enum.shapes import MSO_CONNECTOR
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(l), Inches(t), Inches(l + w), Inches(t))
    ln.line.color.rgb = color; ln.line.width = Pt(weight)
    ln.shadow.inherit = False
    return ln

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    w, h = struct.unpack(">II", head[16:24])
    return w, h

def fit_pic(slide, path, l, t, max_w, max_h):
    """Place picture fitted inside the box (aspect preserved, centered)."""
    w, h = png_size(path)
    ar = w / h
    tw, th = max_w, max_w / ar
    if th > max_h:
        th, tw = max_h, max_h * ar
    px = l + (max_w - tw) / 2
    py = t + (max_h - th) / 2
    slide.shapes.add_picture(path, Inches(px), Inches(py), width=Inches(tw), height=Inches(th))

def set_row(slide, prefix, text, size=10.5):
    """Set a TECH STACK row (right card only: left > 6.9in) by its original label prefix."""
    for sh in slide.shapes:
        if (sh.has_text_frame and sh.left is not None and Emu(sh.left).inches > 6.9
                and sh.text_frame.text.strip().startswith(prefix)):
            set_text(sh, text, size=size, color=WHITE, align=PP_ALIGN.LEFT)
            return
    raise RuntimeError(f"row not found: {prefix}")

# ══════════════════════════════════ SLIDE 1 — TITLE ══════════════════════════════════
s = S[0]
set_text(find(s, "PROJECT SUBMISSION TEMPLATE"), "FarmShield — Autonomous Crop Pest & Disease Containment", size=25, color=WHITE, bold=True)
set_text(find(s, "TEAM NAME "), "Team Divacoded", size=14, color=WHITE, bold=True)
set_text(find(s, "TEAM ID"), "H2O-150", size=14, color=WHITE, bold=True)
set_text(find(s, "PROBLEM STATEMENT NUMBER"), "AAA-09", size=14, color=WHITE, bold=True)
set_text(find(s, "DOMAIN"), "Precision Farming", size=14, color=WHITE, bold=True)
set_text(find(s, "1. Team Lead"), "1. Tharunya (Lead)", size=13, color=WHITE)
set_text(find(s, "2. Member"), "2. S. Shri Varshini", size=13, color=WHITE)
set_text(find(s, "3. Member"), "3. Terencia Mary J", size=13, color=WHITE)
set_text(find(s, "4. Member"), "4. Deepika K", size=13, color=WHITE)
add_box(s, 1.70, 6.86, 10.0, 0.3, "Detect Early · Predict Spread · Protect Precisely — an AI-assisted working prototype",
        size=12, color=PALE, align=PP_ALIGN.LEFT)

# ══════════════════════════════════ SLIDE 2 — PROBLEM ═════════════════════════════════
s = S[1]
# short one-line answers under the template's prompts
add_box(s, 1.60, 3.22, 5.55, 0.80,
        "Whole-field, calendar-based spraying wastes chemicals on healthy crop — high cost, runoff, residues, pollinator loss.",
        size=10.5, color=LIGHT)
add_box(s, 1.58, 4.40, 5.55, 0.80,
        "Cotton & rice smallholders and their FPOs — Tamil Nadu's bollworm belt first.",
        size=10.5, color=LIGHT)
add_box(s, 1.58, 5.62, 5.55, 0.80,
        "Manual scouting is slow and partial; blanket spraying is uniform. Nothing joins detection → prediction → precision treatment.",
        size=10.5, color=LIGHT)
# right card → OUTBREAK GROWTH CHART (visual)
set_text(find(s, "Who is most affected?"), "")
fit_pic(s, "viz/growth.png", 7.95, 2.58, 4.30, 3.38)
add_box(s, 8.10, 6.06, 3.98, 0.50,
        "Catch it at 2.1 acres — or spray 14.2 acres tomorrow.", size=10.5, color=PALE)
# honesty + headline stat in free strip below cards
add_box(s, 0.95, 6.78, 11.4, 0.28,
        "15–25% of India's crop yield lost to pests & disease each year (ICAR est.) · FarmShield numbers: prototype estimates",
        size=9, color=DIM)

# ══════════════════════════════════ SLIDE 3 — SOLUTION ════════════════════════════════
s = S[2]
# short answers, left column
add_box(s, 1.65, 2.80, 5.25, 0.62,
        "A farmer's photo becomes a confirmed outbreak; a spread model forecasts its growth; the engine dispatches the best treatment agent — autonomously.",
        size=10.5, color=LIGHT)
add_box(s, 1.65, 3.85, 5.25, 0.62,
        "Farmer App (photo → result → Get Help · 7 languages · works offline) feeds the Expert console — one database, real handoff.",
        size=10.5, color=LIGHT)
add_box(s, 1.65, 4.92, 5.25, 0.62,
        "Simple for the farmer, powerful underneath — every step timestamped in a backend a judge can refresh and re-verify.",
        size=10.5, color=LIGHT)
# HERO: rendered pipeline diagram, right side (clear of the template's bottom boxes)
fit_pic(s, "viz/pipeline.png", 9.98, 2.06, 2.28, 3.50)
# HERO 2: real app screenshot — cropped to content, enlarged, backing rect hugging the image
# (starts at 7.32 so the template's first prompt text, which ends ~7.3in, stays readable)
add_rect(s, 7.44, 2.36, 2.42, 3.02, WHITE)
fit_pic(s, "shots/farmer_result_crop.png", 7.48, 2.40, 2.34, 2.94)
add_box(s, 7.40, 5.42, 2.50, 0.25, "actual prototype screen", size=8, color=PALE, align=PP_ALIGN.CENTER)
# bottom template boxes: short labels
set_text(find(s, "CORE FEATURE"), "CORE FEATURE — autonomous detect→dispatch handoff + live event log", size=10, color=LIGHT)
set_text(find(s, "KEY BENEFITS"), "KEY BENEFITS — cluster-scale containment · ~79% less pesticide", size=10, color=LIGHT)
set_text(find(s, "TARGET USER"), "TARGET USER — cotton/rice smallholders via FPOs · Tamil Nadu first", size=10, color=LIGHT)
# HERO 3: to-scale pesticide comparison bar (free strip below the card)
add_box(s, 0.95, 6.76, 1.40, 0.28, "Blanket spray", size=9, color=LIGHT)
add_rect(s, 2.40, 6.79, 4.30, 0.20, RED_BAR)
add_box(s, 6.76, 6.76, 0.55, 0.28, "8.4 L", size=9, color=LIGHT)
add_box(s, 7.36, 6.76, 0.35, 0.28, "vs", size=9, color=DIM)
add_box(s, 7.76, 6.76, 1.30, 0.28, "FarmShield", size=9, color=PALE)
add_rect(s, 9.10, 6.79, 0.92, 0.20, GREEN)
add_box(s, 10.08, 6.76, 0.55, 0.28, "1.8 L", size=9, color=PALE)
add_chip(s, 10.53, 6.74, 1.87, 0.30, "−78.6% pesticide (prototype est.)", AMBER, size=7)

# ══════════════════════════════════ SLIDE 4 — METHODOLOGY & TECH ═══════════════════════
s = S[3]
add_box(s, 1.60, 3.28, 4.60, 0.60,
        "① Photo → outbreak (2.1 ac)  ② Forecast → 14.2 ac / 24 h  ③ Score & dispatch  ④ Treat → contain",
        size=9.5, color=LIGHT)
add_box(s, 1.60, 4.62, 4.60, 0.42,
        "FastAPI · SQLite (WAL) · React + Leaflet · Web Speech (7 languages) · Playwright-verified. Detection: prototype sim — YOLOv8-ready API.",
        size=9, color=LIGHT)
add_box(s, 1.60, 5.77, 4.60, 0.50,
        "Demo-first: reset → run → refresh → verify persistence. Honest Prototype / Simulation labels on every number.",
        size=9, color=LIGHT)
# mini flow strip inside the left card
mini = ["Report", "Detect", "Forecast", "Dispatch", "Contain"]
x = 1.05
for i, lab in enumerate(mini):
    add_chip(s, x, 6.32, 0.88, 0.32, lab, GREEN if i % 2 == 0 else GREEN_D, size=8.5)
    x += 0.88
    if i < len(mini) - 1:
        add_arrow(s, x + 0.03, 6.40, w=0.20, h=0.14)
        x += 0.26
# tech stack rows (right card — targeted by position so left prompts are never touched)
set_row(s, "UI", "UI — React web app (mobile-first farmer app + ops console), Leaflet maps")
set_row(s, "Backend", "Backend — FastAPI microservices, mission state machine, Swagger docs")
set_row(s, "Database", "Database — SQLite (WAL) + SQLAlchemy ORM, seed-state reset for demos")
set_row(s, "Core Logic", "Core Logic — multi-agent coordination (detect → predict → dispatch → treat); transparent scoring", size=10)

# ══════════════════════════════════ SLIDE 5 — ARCHITECTURE ════════════════════════════
s = S[4]
set_text(find(s, "INSERT YOUR ARCHITECTURE"), "")
# rendered swim-lane architecture diagram fills the big card
fit_pic(s, "viz/architecture.png", 1.15, 2.42, 7.15, 4.15)
# KEEP IN MIND side items
set_text(find(s, "Basic workflow or system flow"), "Farmer → agents → farmer: one loop, one database", size=10, color=LIGHT)
set_text(find(s, "Data flow between components"), "REST APIs + persistent event log; state survives refresh", size=10, color=LIGHT)
set_text(find(s, "Feasibility at student / prototype level"),
         "Runs on one laptop: FastAPI + SQLite + React; every claim labeled Prototype", size=10, color=LIGHT)

# ══════════════════════════════════ SLIDE 6 — IMPACT ══════════════════════════════════
s = S[5]
# one-line impact statements — set INTO the template's bullet prompt shapes (no ghosting)
set_text(find(s, "Who will benefit from this solution"),
         "Smallholder cotton/rice farmers via FPOs — protection without capex; pay per treated acre.", size=10.5, color=LIGHT)
set_text(find(s, "Social / economic / environmental impact"),
         "Less runoff & residue — faster containment protects neighbouring fields and pollinators.", size=10.5, color=LIGHT)
set_text(find(s, "Measurable outcomes you expect"),
         "1.8 L vs 8.4 L blanket (−78.6%, prototype est.) — response in minutes, not days.", size=10.5, color=LIGHT)
# clear the three card placeholder bodies
for key in ("Describe a concrete", "Describe how the solution scales", "Describe how the solution is practical"):
    sh = find(s, key)
    if sh: set_text(sh, "")
# USE CASE → rendered response-timeline visual
fit_pic(s, "viz/timeline.png", 1.02, 5.16, 3.42, 1.00)
add_box(s, 1.20, 6.24, 3.10, 0.20, "prototype demo — 19 seconds", size=7.5, color=DIM)
# SCALABILITY → 3 chips
sc = ["+1 field → +1 data row", "+1 language → +1 string file", "+1 agent → +1 fleet record"]
t = 5.13
for i, row in enumerate(sc):
    add_chip(s, 5.15, t, 3.05, 0.30, row, GREEN if i % 2 == 0 else GREEN_D, size=9)
    t += 0.37
add_box(s, 5.15, 6.26, 3.10, 0.20, "coordination engine unchanged", size=7.5, color=DIM)
# FEASIBILITY → checklist
fe = ["✓ full loop runs on one laptop", "✓ 7 languages · voice + offline",
      "✓ SMS / IVR for feature phones", "✓ every number honestly labeled"]
t = 5.13
for row in fe:
    add_box(s, 9.09, t, 3.15, 0.22, row, size=8.5, color=LIGHT)
    t += 0.235
add_box(s, 9.09, 6.26, 3.10, 0.20, "working prototype, today", size=7.5, color=DIM)

# ══════════════════════════════════ SLIDE 7 — THANK YOU ═══════════════════════════════
s = S[6]
add_box(s, 2.67, 6.35, 8.0, 0.55,
        "FarmShield — Detect Early. Predict Spread. Protect Precisely.\nTeam Divacoded · AAA-09 · Working prototype: farmer → agents → containment",
        size=11, color=PALE, align=PP_ALIGN.CENTER)

# ══════════════════════════════════ SCREENSHOTS APPENDIX (slides 8-9) ═════════════════
def add_screenshot_slide(title, subtitle, images, page_tag):
    sl = prs.slides.add_slide(prs.slide_layouts[0])
    band = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05))
    band.fill.solid(); band.fill.fore_color.rgb = GREEN_D; band.line.fill.background(); band.shadow.inherit = False
    add_box(sl, 0.55, 0.16, 9.5, 0.5, title, size=24, color=WHITE, bold=True)
    add_box(sl, 0.57, 0.66, 11.0, 0.3, subtitle, size=12, color=PALE)
    add_box(sl, 11.3, 0.32, 1.6, 0.3, page_tag, size=11, color=PALE, align=PP_ALIGN.RIGHT)
    for (path, l, t, w) in images:
        sl.shapes.add_picture(path, Inches(l), Inches(t), width=Inches(w))
    return sl

add_screenshot_slide(
    "FarmShield — Working Prototype",
    "Farmer App (English & Tamil · 7 languages) · Offline alerts by SMS/IVR · voice-guided, label-free UX",
    [("viz/phones.png", 1.17, 1.52, 11.0),
     ], "08 / 09")

add_screenshot_slide(
    "Autonomous Response — Live Demo",
    "20-second demo: detect → predict → dispatch → treat → contain · ops console + field map",
    [("shots/demo_done.png",   0.75, 1.55, 2.95),
     ("shots/expert_dash.png", 4.05, 1.55, 4.55),
     ("shots/expert_map.png",  8.95, 1.55, 3.60),
     ], "09 / 09")

prs.save(OUT)
print("saved", OUT)
