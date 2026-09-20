# FarmShield — Accessibility, Inclusion & Infrastructure Battle Card
### (Round 2: the "who gets left out" question batch)

**Core principle for every answer:** FarmShield's protection does not live inside the farmer's phone.
It lives in the backend pipeline. The phone is only one of several doors into that pipeline. Once the
judge accepts that framing, every "what if the farmer can't X" question collapses into "which door
does this farmer use?"

---

## A. ACCESSIBILITY & INCLUSION

### A1. Farmer is blind or has low vision — how do they use it at all?
**One line:** The app speaks — the voice guide reads every screen aloud in the farmer's language, and
alerts arrive as voice calls on any phone.

**Demo:** Tap the speaker icon in the Farmer App header → every screen announces itself
("Possible pest detected. Cotton. Risk: High. 2.1 acres. Get field assistance."). Toasts are
`aria-live`, all controls are labeled for TalkBack/VoiceOver. On a feature phone, the IVR call *is*
the interface — no screen needed at all.

### A2. Farmer is illiterate or has low digital literacy?
**One line:** The whole flow works without reading a word: icon-first buttons, one green primary
action, voice guide reads everything, and the diagnosis arrives as speech.

**Demo:** Voice guide ON → full flow (check crop → result → get help → confirmation) completes with
zero text input. The demo phone number is even entered for them. Nothing in the flow requires
typing except optional registration.

### A3. Farmer doesn't speak the interface language?
**One line:** Seven languages built in — Tamil, Hindi, Telugu, Kannada, Malayalam, Marathi, English —
with the Tamil experience fully translated, not partially.

**Demo:** Switch to தமிழ் on the home screen — every visible string changes (verified zero English
leakage). Text-to-speech follows the language (`ta-IN`). Adding language #8 is a string file, not a
code change; priority goes by demo-state crop belts (TN → Tamil first, which is why it's complete).

### A4. Elderly farmer uncomfortable with smartphones — non-app pathway?
**One line:** Yes: the same alerts go out as **SMS** and as a **voice call in the farmer's language**
— and the farmer can even report by voice call through the IVR.

**Demo:** The Alerts tab shows the SMS/IVR preview cards — the literal message text a feature phone
would receive ("FARMSHIELD: Possible pest in your cotton (2.1 acres)…"). One notification pipeline,
three delivery surfaces: push (app), SMS, IVR call.

### A5. Motor disability — can't operate manual overrides in an emergency?
**One line:** Overrides are a single tap or a spoken word, never a joystick.

**Demo:** Mission control accepts one-button abort (STOP → agent returns home), and voice guide
means commands can be spoken. Treatment parameters are label-capped by the backend, so an
accidental double-tap can't over-dose. For farmers who can't operate anything in the field, the
system's whole point is that field action is dispatched *to* them, not operated *by* them.

### A6. Alert step assumes smartphone + data? Feature-phone fallback?
**One line:** No — push notification if app, SMS if feature phone, voice call if illiterate; the
backend picks the channel from the farmer's registered profile.

**Demo:** Profile → Network toggle shows offline queuing; Alerts tab shows the SMS/IVR previews.
The farmer profile model already stores language + mobile number — that's the routing table.

---

## B. HUMAN-CENTERED "WHAT IF" SCENARIOS

### B1. Farmer doesn't trust the AI and wants to override?
**One line:** The farmer initiates every treatment today — nothing is sprayed without a report from
the field, so the human already holds the trigger; overrides are explicit, not implicit.

**Deeper:** Design reserves an "I disagree" action on the result screen → routes to a human
agronomist callback instead of autonomous dispatch. Trust is built by the system *explaining*:
the dispatch reason is written in plain words ("closest available agent, 2.3 km, ~3 min") and the
farmer's own photo stays the primary evidence.

### B2. Spray drifts into a neighbor's non-participating farm — who's liable?
**One line:** Treatment zones are geofenced to the registered field boundary and dose-capped; drift
liability sits with the certified drone operator under existing DGCA/label rules — same as any
contract sprayer today.

**Honest note:** Wind-speed gating is in the data model (dispatch won't fly above label wind
limits) and boundary buffers are a production requirement we flag rather than claim as finished.

### B3. Farmer can't afford drone/robot hardware?
**One line:** That's the operating model: farmer co-operative / FPO owns the fleet; FarmShield is
the coordination layer — the farmer's cost is a service fee per treated acre, not capex.

**Deeper:** Mirrors how India actually scaled machinery access (Custom Hiring Centres). Our demo
fleet of 5 agents is explicitly a shared pool — one dispatch engine, many farms.

### B4. Farmer's traditional knowledge contradicts the diagnosis?
**One line:** The system never says "you're wrong" — it says "possible pest detected" and asks for a
ground confirmation, putting the farmer's eyes and the model's eyes on equal footing.

**Deeper:** Wording throughout is deliberately probabilistic ("Possible Bollworm", risk levels, no
percentages on farmer screens). Confidence builds when the prediction timeline matches what the
farmer then observes — the event log becomes the shared record both sides can check.

---

## C. CONNECTIVITY & INFRASTRUCTURE

### C1. No internet/cellular in the field — does the pipeline stop?
**One line:** The farmer's phone queues the report offline and auto-sends when signal returns —
already built and demoable.

**Demo:** Profile → Network (demo simulation) → OFF → Check Crop → "Saved on your phone" →
toggle ON → the queued report replays into the real backend (detection + outbreak created, queue
empties). SMS/IVR paths bypass the app entirely — a 2G feature phone in a no-data zone still
receives alerts and can report by call.

### C2. Power outage at the charging station?
**One line:** Fleet view exposes battery honestly; dispatch scoring already refuses low-battery
agents (we demo it: DRONE-04 at 35% gets skipped), and degraded coverage explicitly raises the
alert level instead of failing silently.

**Deeper:** Solar canopies are the standard fix for rural stations; the honest prototype answer is
that power resilience is a deployment concern, not an app concern — but the system will never
*pretend* an agent is available when it isn't.

### C3. Hilly/wooded terrain, unreliable GPS?
**One line:** Field boundaries are registered polygons; treatment targets the polygon centroid and
uses visual/RTK positioning near the crop, with the farmer's phone as the low-precision fallback
marker.

**Honest note:** Consumer-GPS drift is meters; field polygons are tens of meters wide — error is
absorbed by the geofence, and a human-in-the-loop confirmation step covers the residual.

---

## D. EXTREME OPERATING CONDITIONS

### D1. Monsoon: drones grounded for two weeks — silent degradation?
**One line:** No silent failure — data freshness is displayed, and the prediction model carries an
explicit "no new data" state that widens uncertainty instead of confidently extrapolating.

**Honest note:** In the prototype, extended outages would show as stale predictions labeled
"Prototype AI Simulation" — the design principle (stale data is flagged, never disguised) is what
we demonstrate.

### D2. Outbreak at night?
**One line:** Detection waits for light (or switches to the farmer's report — pests don't schedule
themselves around camera limits), but *treatment* runs at night by design: that's when spray drift
and bee activity are lowest.

**Deeper:** Many ag drones are already specified for night ops (GPS-guided, obstacle lights). The
demo fleet dispatches whenever the pipeline triggers — the timestamps in the event log are real.

### D3. Animal/people wander into the spray zone?
**One line:** Standard ag-drone safety stack: geofenced no-fly boundaries, obstacle sensors with
auto-abort, and a one-tap STOP that recalls the agent immediately.

**Honest note:** In production this is the drone OEM's certified collision-avoidance layer; the
mission controller's contribution is the abort path and keeping people out of the loop's danger
zone by treating at scheduled low-activity windows.

---

## E. TRUST, ERROR & LIABILITY

### E1. AI sprays the wrong chemical onto a neighboring organic farm?
**One line:** Liability chain = certified operator + label compliance + geofence, exactly as with a
human contract sprayer — the system logs every decision so fault is attributable rather than
disappearing into "the AI did it."

**Deeper:** The event log is the legal artifact: who reported, what was detected, what was
dispatched, where, when, at what dose. FarmShield's job is to make that record complete.

### E2. System misses an outbreak and the farmer loses the crop — recourse?
**One line:** We present FarmShield as a risk-reduction layer inside existing crop-insurance
frameworks (PMFBY), not as a guaranteed protector — and the honest labels in the UI are part of
that honesty.

**Deeper:** Business-model hook: bundled insurance partnerships where FarmShield's event log
serves as claim evidence. We do not claim field-validated loss prevention — the app says
"Prototype" everywhere a judge looks.

### E3. GPS spoofing redirects spray drones?
**One line:** Treatments are bounded by registered field polygons, dose caps, and label rules — a
spoofed coordinate can at worst waste a mission inside the geofence, not spray an arbitrary
target.

**Deeper:** Production hardening: multi-GNSS + visual odometry, operator confirmation for
out-of-boundary destinations. The prototype doesn't simulate spoofing, and we say so if asked.

---

## F. EQUITY — WHO GETS LEFT OUT

### F1. Only large farms can afford this — does it widen the gap?
**One line:** The economics are inverted on purpose: 2.1-acre smallholdings are the *primary* demo
scenario, and the shared-fleet/FPO model means the farmer's cost scales with acres treated, not
with hardware owned.

**Deeper:** Smallholders benefit most per acre — they can't amortize blanket-spray waste the way
large farms can. The 78.6% input reduction (Prototype Estimate) matters most where the budget is
tightest.

### F2. Farmer speaks a language we don't support yet?
**One line:** Languages are string files + TTS voice packs — a new language is days of translation,
not months of engineering, and the queue is decided by crop-belt data, not by team convenience.

**Deeper:** The i18n architecture (one translation table, `tr()` fallback to English only as a
last resort) is already in the codebase; Tamil was completed end-to-end to prove the pattern.

---

## G. THE SLIDE ADDENDUM (one slide, five lines)

**FarmShield works without a smartphone, without literacy, without English, and without signal.**

1. **Any phone:** alerts by SMS or voice call (IVR) in the farmer's language — previews in the app.
2. **No reading needed:** voice guide reads every screen; icons + one green button.
3. **No network needed:** reports queue on the phone and auto-sync — demoable via the network toggle.
4. **No capex:** shared FPO fleet; farmer pays per treated acre.
5. **Human in command:** farmer reports, farmer can disagree, agronomist callback path.

*Everything above is either implemented in the prototype or explicitly labeled as design intent —
we keep the distinction on screen.*

---

## H. 30-SECOND DEFLECTION MAP (round 2)

- "What if no smartphone?" → Alerts tab: SMS + IVR preview cards.
- "What if illiterate?" → Toggle voice guide, run one flow hands-free.
- "What if no network?" → Profile → network toggle OFF → Check Crop → "Saved on your phone" → ON → sync.
- "How does dispatch choose?" → Event log line: DRONE-03 · 2.3 km · ~3 min · battery/payload gating.
- "Is this honest?" → Every numeric surface carries a Prototype label; never-say list in JUDGE_QA.md.
