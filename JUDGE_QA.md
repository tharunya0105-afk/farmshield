# FarmShield — Judge Q&A Battle Card (AAA-09, HACKWELL 2.0)

**Rule of the room:** every claim maps to something visible in the working app. When in doubt, say
**"Prototype Estimate"** or **"Prototype Simulation"** and offer to show the code/screen. Never claim
field-validated accuracy, real pesticide savings, or trained RL — the app itself doesn't.

Golden move: answer in one sentence, then say *"let me show you"* and click. 9 of these answers are
visible on screen in under 20 seconds.

---

## A. PROBLEM STATEMENT — CRITICAL READING

### A1. Farmers already know blanket spraying is bad. Why hasn't the market solved it?
**One line:** The blocker isn't knowledge — it's that detection, decision, and action live in three
different places with no coordination layer between them.

**Backup:** Scouting labor doesn't scale on 1–2 acre smallholdings; multispectral drones are capex
farmers can't justify; agronomy advice arrives days late via extension officers. FarmShield is the
missing *coordination layer*: farmer's phone for detection, cloud engine for decisions, agent fleet
for treatment. We demonstrate the orchestration — the hard part nobody else demos end-to-end.

### A2. How early is "early," really? Pests aren't visible from the air before damage starts.
**One line:** Correct — we don't claim pre-infection detection; we claim *cluster-scale* detection:
2.1 acres while it's still 2.1 acres, instead of 14.2 acres a day later.

**Backup:** Spectral stress shows up in red-edge/NIR bands days before the naked eye sees symptoms,
and farmer photos catch chewing damage at the cluster stage. The value is the *response window*:
our prediction curve (2.1 → 5.5 → 8.7 → 14.2 acres in 24h) shows what waiting costs. Early enough
to contain a spot; too late once a human scout's weekly walk finds it.

### A3. If multispectral can see it, damage has already begun — isn't "early detection" a misnomer?
**One line:** Every detection system has a floor; ours is measured in acres, not fields.

**Backup:** The comparison that matters is against the status quo — human scouting finds outbreaks
when they're field-wide. Detecting a 2.1-acre cluster that would become a 14-acre loss tomorrow *is*
early in economic terms. We're careful to say "possible pest detected," never "pre-symptomatic."

---

## B. LOGICAL CONSISTENCY

### B1. Your pipeline is linear — why no feedback into spread prediction retraining?
**One line:** The event log is the feedback loop — every detection, prediction, treatment, and
containment outcome is stored with timestamps precisely so it can become training data.

**Backup:** In the demo, outcomes (contained, 2.1 acres treated, DRONE-03, actual spread) land in
the same database as the predictions they validate. Production loop: observed vs predicted spread
re-fits the local growth model per crop-pest pair; that's phase 2, and we're honest that the
prototype generates predictions from a fixed scenario model, not learned weights.

### B2. "Fully autonomous" — who's liable when a drone sprays the wrong field? Where's the kill switch?
**One line:** Autonomy operates inside a human-owned envelope: the farmer reports the problem, the
system treats only inside the registered field's geofence, and every stage is logged and reversible.

**Backup:** Three hard limits in the design: (1) treatment only on confirmed outbreaks within the
geofenced field boundary — no free-flight spraying; (2) dose capped per crop/pest from the chemical
label; (3) operator abort + return-to-home at any mission stage. On liability: India's DGCA already
requires certified operators for spray drones — autonomy assists a certified operator, it doesn't
replace the regulatory chain. Our demo is honest about this: it simulates the coordination, and it
says so on screen.

### B3. How do you define "confidence" for a spread prediction when outbreak data is sparse?
**One line:** We don't train on sparse outbreaks — we start from agronomic growth models (the same
degree-day and humidity-driven population models extension services publish) and update them with
local observations.

**Backup:** Rare-event strategy: physics/biology-based priors, Bayesian correction from each local
outbreak, and *intervals instead of point estimates* in production. The prototype runs a fixed
scenario curve and labels it "Prototype AI Simulation" — the honest version of this answer is on
the Outbreaks page right now.

### B4. Weather forecasts are uncertain 3–5 days out — aren't you stacking two error sources?
**One line:** We deliberately use short horizons — 2 to 24 hours — where hyper-local weather error
is small, and uncertainty *widens the buffer*, never shrinks it.

**Backup:** Our predictions are 2h/6h/12h/24h (visible on screen), driven by stored microclimate
(29°C, 78% RH, 11 kph) — not 5-day forecasts. Design rule: when forecast confidence drops, the
containment radius grows. Errors stack into safety margin, not false precision.

---

## C. TECHNICAL DEPTH — TRYING TO BREAK IT

### C1. Which bands, which index, which pest?
**One line:** For cotton–bollworm: green/red/red-edge/NIR for vigor anomaly (NDVI/NDRE decline),
but aerial alone is insufficient — bollworm damage is often under the canopy — so confirmation comes
from the farmer's own photo.

**Backup:** That's not a dodge; it's the architecture. Aerial anomaly flags the zone → the farmer
walks that zone and sends a photo → confirmation combines both signals. Our prototype demonstrates
exactly this hybrid: farmer photo → detection → outbreak. The detection model itself is simulated
in the demo (deterministic scenario) — labeled as such.

### C2. Bollworm-in-cotton won't generalize to aphids-in-wheat. One model or a framework?
**One line:** FarmShield is a framework — detection, prediction, dispatch, and missions are
crop-agnostic services; each pest–crop pair contributes one detection model.

**Backup:** Seed data proves the point: the system already carries two completed scenarios across
two crops (Cotton–Bollworm and Rice–Stem Borer). Realistic coverage by demo day: the two demoed
pairs. Adding a pair = adding a model behind the same API — nothing else changes.

### C3. Ground robots are slow. If travel takes 2 hours, hasn't the golden window closed?
**One line:** That's exactly why dispatch is scored on estimated travel time — and in our scenario
the chosen drone covers 2.3 km in ~3 minutes against a 24-hour spread window.

**Backup:** Show the event log: "DRONE-03 selected — closest compatible available agent with
sufficient battery and treatment capacity (2.3 km, ~3 min travel, 100% battery, 6.0L)." Drones are
first responders for speed; ground robots (ROBOT-01, 10L payload) are the heavy-precision option.
The selector *skipped* DRONE-04 (35%, charging) — the fleet view shows that battery gating live.

### C4. Drones fly 20–30 minutes. How many sweeps cover a 50-acre farm, and how often?
**One line:** One ag drone images roughly 10–20 hectares per flight, so a 50-acre farm is one or
two flights per sweep, flown at dawn and dusk when pest activity peaks — plus event-triggered
re-flights of flagged zones.

**Backup:** We don't claim continuous surveillance — twice-daily scheduled sweeps plus farmer
photo checks in between. The farmer's phone is the densest sensor network on the farm, and it's
already in the product.

### C5. You use reinforcement learning for dispatch — where does the reward signal come from before harvest?
**One line (correct the premise):** It doesn't — and that's deliberate. Dispatch is a transparent
scoring function: travel time, battery, payload capacity, treatment compatibility.

**Backup:** Auditable heuristics work from day one and a judge can verify them in the event log.
RL would be a later optimization once logged outcomes accumulate — and our event log is designed
to produce exactly those labeled outcomes. We'd rather demo a system whose decisions you can
interrogate than a black box we can't explain.

---

## D. THE NUMBERS

### D1. "60–80% less pesticide" — source? Pilot? Literature? Projection?
**One line:** Prototype Estimate — computed from our own dose model and consistent with published
site-specific spraying results, never claimed as field-validated.

**Backup:** Show the math on screen: blanket = 4 L/acre → 8.4 L on 2.1 acres; precision = 1.8 L
spot-treated → **78.6% reduction**, computed live from stored mission data in the Analytics page.
Literature range for spot/variable spraying broadly overlaps 30–90%; we present our number as the
model's output with the "Prototype Estimate" label attached — same number, same label, everywhere.

### D2. What assumptions drive it, and how sensitive is it to detection accuracy?
**One line:** The saving scales with the *infested fraction* — at 25% coverage you save ~75%; if
half the field is already hit, savings fall toward 30–40%.

**Backup:** Sensitivity driver = detection earliness, which is the whole argument for the pipeline:
the earlier you catch it, the less you spray. We can state that trade plainly because our numbers
come from a formula, not a brochure.

### D3. And the yield-loss number?
**One line:** Assumption-based on regional extension data for untreated bollworm in cotton
(20–30%+ losses), with the model's claim limited to "loss confined to the treated cluster" —
labeled Prototype Estimate in the deck.

---

## E. EDGE CASES

### E1. Cloudy/foggy day — does the sweep just get missed?
**One line:** Imagery quality is gated; below threshold the system degrades to its second sensor —
the farmer's photo check — and re-flies when clear.

**Backup:** Our core detection flow never needed the drone in the first place: farmer photographs
crop → detection → outbreak. Clouds cost you the sweep, not the system.

### E2. Detection says outbreak, prediction says low risk — who wins?
**One line:** Neither is autonomous over the other: the policy is *verify when cheap before acting
when expensive* — a re-check flight or farmer confirmation within hours, not an immediate spray.

**Backup:** The UI language is deliberate: "Possible pest detected." Detection proposes,
prediction prices, policy decides. Spraying is the costliest action, so disagreement routes to the
cheap verification step first.

### E3. Pest resists the default chemical — does it keep re-spraying the same thing?
**One line:** Production design: treatment library per pest with mode-of-action rotation (IRAC
rules); a re-outbreak after treatment escalates to alternate chemistry and flags a human agronomist.

**Backup:** Honest caveat: the prototype doesn't simulate resistance. If asked, say so in one
sentence and show the mission state machine — completion → containment → notification — as the
hook where an escalation policy would slot in.

### E4. Doesn't the system confirm its own false positives over time (biased feedback loop)?
**One line:** Confirmation requires a second, independent signal — farmer photo or ground check —
and treatment outcomes are logged separately from detection labels, so the model never grades
its own homework.

**Backup:** Periodic re-audit against agronomist-labeled ground truth; confidence recalibration
checks. The prototype uses deterministic demo data (labeled), so this is a design answer, and
we say that plainly.

---

## F. "SO WHAT" — NON-TECHNICAL JUDGES

### F1. Why should a farmer trust an autonomous system over calling a human scout?
**One line:** The farmer never hands over control — they report the problem, watch the response,
and get the result message in their own language; the autonomy is in *coordination speed*, not in
silently deciding.

**Backup:** A scout visits a few farms a week; FarmShield watches continuously, responds in
minutes, and shows its reasoning (reason line in the dispatch log). Trust through transparency
and involvement, not through mystery.

### F2. Five "AI + drone + farm" pitches today — what's memorable about ours?
**One line:** In 20 seconds you watch one Tamil-speaking farmer's photo become a detected,
predicted, dispatched, treated, contained 2.1-acre outbreak — with every step timestamped in a
real backend you can refresh and re-verify.

**Backup:** Most demos are slides and promises; ours is one button and a database that persists
across refreshes. Simple for the farmer, powerful underneath, honest on every label. That's the
sentence to leave in the room.

---

## G. NEVER-SAY LIST (matches the app's on-screen labels)

| Never say | Say instead |
|---|---|
| "Field-validated accuracy" | "Prototype simulation, scenario-based" |
| "Real pesticide savings of 78.6%" | "Prototype Estimate: 78.6% model-computed reduction" |
| "Trained reinforcement learning" | "Transparent dispatch scoring: travel time × battery × payload" |
| "Real autonomous drones" | "Autonomous coordination workflow, simulated agents" |
| "Early detection before symptoms" | "Cluster-scale detection while it's still 2.1 acres" |
| "Our own trained pest model" | "Open PlantVillage CNN, running locally — 38 classes, 14 crops" |
| "It recognizes any pest" | "Confident on leaf diseases it knows; asks for a better photo when unsure" |

## H. 30-SECOND DEFLECTION MAP (question → screen)

- "Is it real?" → Hand the judge any leaf photo: Farmer App → Check Crop → real CNN verdict in seconds. Then refresh the browser: state persists. Open Event Log: real timestamps.
- "How does dispatch choose?" → Event Log line: DRONE-03, 2.3 km, ~3 min, battery/payload gating.
- "Microclimate?" → Outbreaks page: 2.1 → 14.2 acres with 29°C / 78% RH / 11 kph stored per prediction.
- "Farmer experience?" → Farmer App in Tamil: photo → result → Get Help → notification.
- "Numbers?" → Analytics: computed from stored mission data, labeled "Prototype estimates computed from stored demo data."
- "Is detection actually AI?" → Yes at two scales: leaf photos via real CNN (Farmer App → Check Crop) AND field imagery via aerial tile-scan (Expert Console → Aerial Scan). Both run the same real PlantVillage MobileNetV2. Demo Cotton outbreak stays scenario-based, labeled DEMO_SIMULATION.
- "Can it detect from drone/satellite images?" → Yes: Expert Console → Aerial Scan → pick the cotton field sample → real CNN runs on all 36 tiles → clusters disease hotspots with acreage. Try uploading your own field photo.
- "What if the photo is unclear?" → Show it: the app refuses to guess below confidence thresholds and asks for a closer photo — never fabricates a verdict.

---

## I. REAL IMAGE MODEL (wired behind /api/detection/analyze-image)

### I1. What is actually running?
**One line:** A genuine convolutional neural network — MobileNetV2 fine-tuned on PlantVillage
(38 disease classes across 14 crops: tomato, potato, corn, apple, grape, pepper and more),
converted to ONNX and executed locally by OpenCV DNN. No cloud call, no internet needed at
demo time — the 9 MB model file lives in `backend/model_store/`.

**Backup:** Endpoint: `POST /api/detection/analyze-image` (multipart photo). Result modes:
`REAL_MODEL` (confident verdict → can confirm into the outbreak pipeline), `HEALTHY`
(high-confidence healthy), `VISUAL_CHECK` (stress signs but below threshold — honest
"get a closer photo"), `DEMO_SIMULATION` (model unavailable — same shape as the classic
endpoint, so nothing downstream breaks).

### I2. Why did you choose PlantVillage over training your own?
It's the canonical public crop-disease dataset (~54k labeled leaf images, 38 classes) —
auditable, reproducible, and honest. Training our own on one laptop overnight would give a
model nobody can verify. We picked an open, documented checkpoint and wired it behind a
clean API so a custom Indian-crop model (cotton bollworm leaf damage, rice blast…) drops in
later without touching the product.

### I3. What are its limits? (say this before the judge asks)
- **Cotton isn't in the 38 classes** — bollworm damage is a pest *symptom*, not a leaf
  disease class, so cotton photos route to the honest `VISUAL_CHECK` path rather than a
  fake verdict. The demo Cotton outbreak remains scenario-based (`DEMO_SIMULATION`),
  clearly labeled.
- **Confidence gating:** >55% ⇒ named disease; >90% healthy ⇒ "looks healthy"; otherwise
  the app refuses to guess and asks for a closer photo. Verified in the UI with real
  dataset photos: diseased tomato → "Late Blight, High risk"; healthy tomato → "looks
  healthy"; off-distribution photo → "Photo not clear enough · Retake".
- **Accuracy varies per class** (tomato classes test at 74–96% on sampled dataset photos;
  some crops are weaker) — hence the threshold policy rather than blind trust.

### I4. The 30-second judge moment
Hand the judge their own phone photo of any plant. If it's one of the 14 crops with a
visible disease, they get a real named verdict in ~2 seconds. If it's not, FarmShield
says so honestly instead of inventing a pest. Either outcome demonstrates the claim
"detection is real AI" better than any slide.

### I5. Path to production
Swap the ONNX file for a model fine-tuned on Indian field imagery (cotton, rice, groundnut
— ICAR/Plantix-style datasets). The API contract (`analyze-image` → mode/confidence/pest)
stays identical; the frontend, confirm→outbreak pipeline, dispatch, and treatment flow are
already model-agnostic and tested against both modes.

---

## J. AERIAL SCAN DETECTION AGENT (field-scale detection, not just leaf photos)

### J1. What is the aerial scan?
**One line:** The same real PlantVillage CNN, applied per-tile over a field/drone image,
clustering disease hotspots into infection zones with coordinates, confidence, and
estimated acreage.

**How it works:** The field image is split into a 6×6 grid (36 tiles). Each tile is
classified independently by the real CNN. Tiles with disease confidence ≥45% are marked
"hot". Adjacent hot tiles are clustered (4-connected BFS) into infection zones. Each zone
reports: pest type, average confidence, estimated acreage (hot tiles / total tiles × field
area), GPS coordinates (if field bbox is provided), and pixel bounding box for overlay.

**Endpoint:** `POST /api/detection/scan-field` (multipart image + field_area_acres).
Returns `mode: REAL_MODEL_AERIAL` — not a simulation.

### J2. What does the demo show?
1. Open Expert Console → Aerial Scan
2. Click one of 4 sample images (real cotton field, diseased leaf, healthy leaf, rice paddy)
   or upload your own photo
3. The real CNN runs on all 36 tiles in ~2 seconds
4. Results show: per-tile heatmap (red = hot, green = healthy), cluster bounding boxes
   overlaid on the image, infection zone list with confidence + acreage
5. Click "Confirm → Outbreak" to feed the worst cluster into the full outbreak pipeline
   (predict → dispatch → treat → contain)

### J3. Honest limitations
- The CNN was trained on **leaf-level** PlantVillage images, not aerial/multispectral.
  At altitude, accuracy degrades — the tile scan is a legitimate proxy but not equivalent
  to a purpose-trained aerial detector.
- **38 classes, 14 crops** — cotton, rice, and other Indian staples are not in the training
  set. The model detects *visual stress patterns* it recognizes from other crops.
- For production: swap the CNN for a multispectral-trained model (NDVI + RGB bands)
  without changing the API contract or frontend.

### J4. Why this answers the problem statement
AAA-09 asks for "aerial detection of localized infection clusters." The tile-scan
agent does exactly that: it takes field imagery, finds clusters of disease signals,
estimates their area, and feeds them into the autonomous response pipeline. The model
is real, the inference is real, the clusters are real — it's not a simulation.

The honest framing: "real CNN per-tile detection now; multispectral aerial model
is the production path." This is defensible because the architecture is already
in place — only the model file changes.
