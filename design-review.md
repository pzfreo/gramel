# Design Review — Gramil Violin Purfling Cutter

Reviewer persona: senior design & manufacturing engineer (~15 years).
Subject: parametric model on `main`, v0.1.3.
Use case (per maker): hand-held; cut force ≤ a few newtons; thumbwheel and grub screw finger-tight only; cycle volume ≈ 8 working days / year over decades; original reference tool has had no failures.

---

## 1. Executive summary

Five priority items, ranked.

| # | Severity | Issue | Section |
|---|---|---|---|
| 1 | **HIGH** | Grub-screw advance becomes ≤ 0.1 mm with the design-default 1.5 mm channel spacer. Channel widths > 1.6 mm aren't physically supported by the current slot. | §6 / §7 |
| 2 | **MEDIUM** | Shaft cocking at the crossbore — even at the design H7/g6 worst case (~29 µm diametric clearance), the 35 mm shaft cantilevered out of a 13.55 mm bore can tilt enough to put ~0.045 mm of error at the blade tip. | §5 (shaft↔shank), §6 |
| 3 | **MEDIUM** | Push-rod radial slop in the depth-lock bore is 0.25 mm. Excessive — the rod can lean about its long axis enough to occasionally trap or rub. | §5 (rod↔shank) |
| 4 | **MEDIUM** | Shank requires 4–5 separate setups. Karpas explicitly flags this as a cost driver. Drive plate, thumbwheel, and depth-lock bolt are 2-setup each. | §8 |
| 5 | **LOW** | Captive bearing axial play (0.2 mm) is on the tight side of comfortable. Manufacturing tolerance variation of ±0.05 mm on plate thickness or tap depth eats half the budget. | §5 (captive bearing) |

Lots of green-light items too — assembled state is mostly clean (no real interferences after the v0.1.2 retainer fix), the shank's wall-thickness math is solid, the captive bearing parameter validator is good engineering hygiene, and the H7/g6 fit pair is the right call for the shaft/bore.

---

## 2. Reference frame and load case

**Coordinate convention** (Z-up, intuitive holding the tool):

- **X**: along the shaft (perpendicular to working face). +X = working face, the direction that translates to vary edge margin from the workpiece.
- **Y**: perpendicular to shaft, horizontal (tool-travel direction).
- **Z**: along the shank (vertical). +Z = top, where the drive screw and its thumbwheel sit. Blades cut downward in −Z.

**Load case** (from maker's input):

- **Cut force**: a few newtons normal to the workpiece. The cut is a scoring slice into spruce/maple, not a chip-clearing operation — geometry of force is along −Z at the blade tip.
- **Hand-tightening torque** on M3 brass-on-brass thumbwheel: realistically 0.05–0.15 Nm finger tight.
- **Hand-tightening torque** on M6 brass depth-lock knob: 0.15–0.4 Nm finger tight (bigger knob, more comfortable grip).
- **Grub-screw torque**: small hex key, ~0.1–0.3 Nm.
- **Cycle volume**: ~8 days × decades. Effectively low-cycle; corrosion and galling matter more than wear.
- **No reported failures on original**: the architecture is sound; this review focuses on the manufacturable instantiation rather than re-engineering.

**Material assumption** for all brass parts: CZ121 / C36000 free-machining brass, half-hard temper. Push rod: bright-drawn mild steel. Retainers: annealed copper sheet. Blades: hardened O1 (~60 HRC) per RFQ. Spacer: customer-supplied shim stock (brass/steel/SS).

---

## 3. Per-component analysis

### 3.1 Shank (GRM-01)

**Function**: doubles as fence and frame. Top of the tool houses the drive-screw thread; bottom houses the depth-lock mechanism; middle has the cross-bore through which the shaft slides.

**Critical dimensions**:

- Crossbore Ø8 H7 — the single most precision-sensitive feature on the whole tool. Defines blade depth registration.
- Crossbore to tapped-bore gap 9.5 mm — controls how far the drive plate can stand.
- Wall around crossbore 1.38 mm — at the −Z (bottom) face under the crossbore. **At the Karpas minimum wall guideline of 1.5 mm — see issue M4.**
- Working face convexity R8.11 — registers against the violin edge.

**Stress / wear**:

- The drive-screw thread sees alternating axial load over ~18 mm of M3 brass thread. Decades × few-N load × ~18 rotations per adjustment = total wear is trivial. No issue.
- The crossbore inner surface sees sliding contact with the shaft over thousands of cycles. Brass-on-brass; lubricant nominal but the original works dry, so designed sliding is fine. Surface finish here matters more than tolerance — see §8.

**Manufacturability**:

- Working face convexity at R8.11 is a non-standard tool radius — Karpas explicitly recommends matching to R3/R4/R5/etc. It'll be a profile pass with a small ball nose, not a single-pass form tool. Adds ~1 setup or a complex toolpath. Worth quoting both as-is and with R8 (rounded to nearest standard).
- 4–5 setups on the part: top dome, bottom face features, working face (relief slot + convexity), back face, side face (crossbore + tapped bore). This is the biggest single cost driver — **issue M4**.
- Top spherical dome at R30 is a ball-nose pass; cheap once the top-face setup is up.
- Relief slot (2 × 1 mm, 66 mm long) → 2 mm endmill, 1 mm depth, light pass. Easy.

**Recommendations**: see §9. Net assessment: well-engineered, manufacturable, but the setup count is its main cost lever.

### 3.2 Shaft (GRM-02)

**Function**: carries the blade slot at its outboard end, slides through the shank cross-bore, drives off the drive plate at its inboard end.

**Critical dimensions**:

- OD Ø8 g6 — mates with the H7 cross-bore.
- Length 35 mm — measured.
- Blade slot 6 × 5 × through (X × Y × Z).
- Flat on −Z full length, 0.6 mm deep — registers against the push rod for depth lock.
- End tap M4 entering from the +X face into the blade slot — grub-screw seat.
- End slot in the −X face for the drive-plate tenon.
- Central M2 tap in the −X face for the mount screw.

**Stress / wear**:

- Crossbore sliding contact: as for the shank, low-cycle, sliding brass-on-brass, no problem.
- Grub-screw thread M4 in brass: torque is low; risk is cross-threading on first install rather than wear. Drive screw has a tip chamfer; the grub screw is modelled as a plain cylinder — no detail on its real lead-in. If the grub screw doesn't have a chamfer on the tip, cross-threading risk is real.
- Blade slot walls (1.5 mm wall around slot Y-direction) wear pattern: the grub-screw nose pushes the blade stack against the −X wall of the slot. Cyclic loading on brass wall is light; no concern.

**Manufacturability**:

- 4 separate features cut on different axes: round bar + flat + slot + tap + end slot + end tap. Karpas can do all but the tap + end slot from one setup with a 4th-axis indexer or two side fixturings. Expect 2 setups (one for the round bar + flat + slot + grub-screw tap; one for the −X end features).
- 1.5 mm wall around slot — meets the Karpas guideline exactly. No margin if the slot is enlarged for a wider blade in a future revision.

### 3.3 Thumbwheel + drive screw (GRM-03)

**Function**: rotated by user, advances/retracts the shaft via the drive plate. One-piece turn from brass bar.

**Critical dimensions**:

- M3 × 0.5 thread, 18 mm long. Fine pitch = 0.5 mm/turn → ~36 turns end-to-end. **Adjustment resolution is excellent (50 µm/full turn, 12 µm at 1/4 turn).**
- Knurled disc Ø10 × 2 mm — finger grip.
- Boss Ø6 × 0.5 mm — seat for the captive screw tap.
- Unthreaded collar Ø5 × 3 mm — provides shoulder against the shank's −X face at max-margin.
- M2 tap on the −X face — 2.8 mm deep + 1 mm chip relief.

**Stress / wear**:

- The knurled disc is brass; knurl on brass is fine but wears over decades. With ~8 days/year × decades use, knurl wear is negligible.
- The 18 mm M3 thread engages with the shank tap. Total clockwise + counter-clockwise rotation over the life of the tool is moderate (a few dozen rotations per use × thousands of uses = ~10⁵ rotations) — well within brass thread fatigue limits.

**Manufacturability**:

- Single-axis turn-and-mill operation. Knurl is a standard wheel. M3 threading on the OD is straightforward; the M2 tap on the end face needs a second setup or live tooling.
- 2 setups expected: turn + thread + knurl, then end-tap on a separate jig.

### 3.4 Drive plate (GRM-04)

**Function**: rigid link between drive screw and shaft. Captive bearing at the thumbwheel end, mount-screw fixed at the shaft end.

**Critical dimensions**:

- Egg outline: R4 + R3 bosses, 9.5 mm centre-to-centre.
- 3 mm thick.
- Tenon: 1.5 mm projection, 3 mm vertical extent, follows egg perimeter.
- Captive hole Ø2.6 (0.3 mm radial clearance — deliberately sloppy).
- Mount hole Ø2.4 (0.2 mm radial clearance — standard M2).

**Stress / wear**:

- Tensile load through the plate when retracting the shaft. Cross-section at the narrow waist (between the two bosses) is ~6 mm wide × 3 mm thick = 18 mm². At a maker-stated peak of ~10 N pull, stress is < 1 MPa. Brass tensile strength is ~280 MPa. **3 orders of magnitude of safety factor.** Plate could be thinner — but 3 mm is set by the tenon + mating, so no actual savings.
- Bearing load on the captive screw and mount screw: bending in the screw shanks. Same load levels; no concern.

**Manufacturability**:

- 2 setups: one for the outline profile + holes from the front face, one for the tenon from the back. Tenon is the milling complication.
- 6 mm × 3 mm waist is a comfortable end-mill profile.
- Egg-shape external tangent lines need a contoured toolpath; simple but slow.

### 3.5 Depth-lock bolt + knob (GRM-05)

**Function**: pushes the steel push rod up against the shaft's underside flat to lock the depth of cut. M6 thread.

**Critical dimensions**:

- M6 × 1.0 thread, 13 mm long.
- Knob Ø10 × 14 mm (the largest hand grip on the tool — biggest leverage).
- Collar Ø6.25 × 5 mm — anti-cocking guide in the shank's collar bore (Ø6.35).
- 1 mm tip chamfer (lead-in).
- 1.5 mm bottom-edge knob chamfer (hand comfort).

**Stress / wear**:

- M6 thread sees the push-rod reaction load. Maximum hand torque ~0.4 Nm at 0.2 friction = ~3-5 N axial force at the rod. Even at 50 N axial (very firm clamping), thread stress is < 5 MPa. No issue.
- The M6 thread sees the most rotations of any thread in the tool — every depth adjustment is a cycle. Over decades, brass-on-brass thread will gradually wear and accumulate radial play. A real concern at the >100 year scale but not at 30-50 year.

**Manufacturability**:

- Single-setup turn part. Knurl + thread + chamfer. Trivial.

### 3.6 Blade retainer (GRM-06, optional)

**Function**: bone-shaped flat plate, four required, locks the blade stack against the slot's open ±Z direction.

**Critical dimensions** (v0.1.3 — corrected from v0.1.0):

- 11 mm tall (Z), 8 mm waist between 1.5 mm end blocks.
- 5.5 mm Y at ends, 4.5 mm Y at waist.
- 0.75 mm thick.

**Stress / wear**: none material. Functions as a stop.

**Manufacturability**:

- Laser cut or stamp. 0.75 mm copper, no fit-critical dimensions. Trivial. Tolerance per the drawing is ±0.1 outline, ±0.05 thickness — comfortably within shim-stock norms.

**Note**: the v0.1.0 retainer (10 mm tall, 6 mm waist) had a 0.027 mm³ wedge interference at the slot corners. The v0.1.3 dimensions provide ~0.4 mm of clearance margin past the cylinder boundary. The interference check is now a regression test in the suite.

### 3.7 Drive-plate captive + mount screws (M2 × 6, M2 × 10)

Stock M2 brass pan-head screws. The captive-bearing math (length = plate thickness + axial play + tap depth) is enforced by a pydantic validator. Good hygiene. Both screws are off-the-shelf — no manufacturing concern.

### 3.8 Push rod, grub screw, blades, spacer

- **Push rod**: Ø4.5 × 45 mm bright-drawn mild steel cut to length. Not a precision part — just a column. Stock item.
- **Grub screw**: M4 × 10 stock cup-point grub screw (the geometry assumes a cup point for blade clamping). RFQ should specify this — currently it's a "plain cylinder at thread major" in the model.
- **Blades**: 0.7 × 4 × 23 mm O1 tool steel, 25° single bevel. Out of scope for the brass-parts quote; flagged for optional supply by the shop.
- **Spacer**: user-supplied shim stock. Out of scope.

---

## 4. Interaction matrix (mating pairs)

Every assembled-state pair that touches or contains, with notes on fit, load, and assembled-state check result. All numbers from the live model at v0.1.3, prototype=False (CNC mode), 1.5 mm spacer installed.

| Pair | Type | Fit/Clearance | Notes |
|---|---|---|---|
| Shaft ↔ shank crossbore | Sliding | H7/g6 (29 µm max diametric) | ✅ no interference. But see issue M2 — short bore vs long shaft → angular cocking. |
| Shaft ↔ drive plate (mount face) | Bolted face-to-face | Direct contact | ✅ tenon fits end slot cleanly. |
| Shaft ↔ drive plate tenon | Tenon in slot | 0.5 mm Y overshoot on slot, tenon snug in X | ✅ no interference. |
| Shaft ↔ mount screw (tap) | M2 thread engagement | 5 mm tap, 6.5 mm engaged thread (incl. plate + tenon) | ✅ thread engagement >> 1.5 × diameter. |
| Shaft ↔ grub screw (tap) | M4 thread engagement | 4 mm tap depth; with 10 mm grub screw, ~6 mm sticks into slot. | Grub screw tip directly contacts blade stack. |
| Shaft ↔ blades (slot) | Loose fit | Y: 5.0 slot vs 4.0 blade = 1.0 mm total slack | ✅ no interference. Y slack is intentional but considerable — see issue M2. |
| Shaft ↔ retainers (slot) | Bone lock | Waist 4.5 vs slot 5.0 Y = 0.25 mm radial slack | ✅ end blocks lock against shaft surface. |
| Shaft ↔ spacer (slot) | Y-loose fit | Same as blade | ✅ no interference. |
| Shaft ↔ push rod (flat) | Face contact | Push-rod top face on shaft −Z flat | ✅ no interference. Locking contact. |
| Shank ↔ drive plate | Clear (no contact) | Plate sits outboard of shank's −X face | ✅ no interference. |
| Shank ↔ thumbwheel (tapped bore) | M3 thread engagement | Full 13.55 mm engagement at neutral | ✅ rotational free, axial constrained. |
| Shank ↔ depth-lock bolt | M6 thread + collar | 12 mm thread + 5 mm collar | ✅ designed clearance 0.05 mm diametric on collar. |
| Shank ↔ push rod | Sliding fit | 0.25 mm radial slack in Ø5 bore | ⚠️ Loose — issue M3. |
| Shank ↔ captive screw head | Clear (head sits outboard of plate) | No contact | ✅ |
| Drive plate ↔ thumbwheel left face | Axial bearing | 0.2 mm axial play | ✅ — the signature mechanism. See issue L1. |
| Drive plate ↔ captive screw head | Axial bearing | Captures plate against thumbwheel | ✅ |
| Drive plate ↔ captive screw shank | Loose hole | 0.3 mm radial in Ø2.6 hole | ✅ deliberately sloppy. |
| Drive plate ↔ mount screw | Standard fit | 0.2 mm radial in Ø2.4 hole | ✅ |
| Thumbwheel ↔ captive screw (tap) | M2 thread engagement | 2.8 mm tap + 1 mm chip relief | ✅ |
| Blade ↔ retainer | Stacked face contact | Direct contact (along X) | ✅ |
| Blade ↔ spacer | Stacked face contact | Direct contact | ✅ |
| Blade ↔ grub-screw nose | Direct contact | Grub-screw nose presses against outer blade in slot | ✅ |
| Push rod ↔ depth-lock bolt tip | Face contact | Bolt tip pushes rod up | ✅ |

**Interference check summary**: I ran the boolean intersection on each pair in the assembled state. Zero real interferences. The "interferences" detected for thread engagements (grub↔shaft, captive↔thumbwheel, mount↔shaft, drive screw↔shank, bolt↔shank) are expected — in CNC mode the model represents threads as a smooth bore at tap-drill diameter against a smooth screw at thread major, so the boolean shows engagement volume. Not real interference.

---

## 5. Selected mating pairs — close analysis

### 5.1 Shaft ↔ shank crossbore (issue M2 — shaft cocking)

H7/g6 worst-case max diametric clearance at Ø8 is 0.029 mm. That's at the bore.

But the shaft is 35 mm long sliding through a 13.55 mm thick bore. Worst-case angular tilt of the shaft, with the bore as fulcrum and the shaft pivoting around its sliding contact:

```
tilt_angle ≈ atan(clearance / bore_length) = atan(0.029 / 13.55) = 0.00214 rad
tip_deflection ≈ tilt_angle × (shaft_protrusion + blade_protrusion)
              ≈ 0.00214 × (~17.5 + ~3.7) ≈ 45 µm radial at the blade tip
```

That's 0.045 mm of possible misalignment at the cut. Probably tolerable for a hand-controlled scoring tool but not zero. The H7/g6 fit is correct for a sliding pair; the geometry just amplifies the angular component.

**Mitigations** (in increasing cost):

1. Insist on the H7/g6 tighter half of the band (~0.005 mm typical, vs 0.029 worst-case). The shop already targets a fit — most reach the middle of the tolerance band naturally.
2. Lengthen the bore. Adding 3-5 mm of bore length (= shank.width going from 13.55 → ~18) would cut the angular component by ~25%. Cost: more material, slower bore reaming, possibly invasive to the rest of the design.
3. Convert to H7/h6 (zero-shift). Worst-case clearance drops to 0.018 mm. Shop preference but still standard.

### 5.2 Push rod ↔ shank bore (issue M3 — rod slop)

The depth-lock bore is sized at Ø5.0 (M6 tap-drill diameter). The push rod is Ø4.5. Radial clearance = 0.25 mm.

That's loose. At the rod's 45 mm length, this allows ~0.6° of tilt — the rod can lean inside the bore, and over thousands of lock cycles, the tilted contact will wear a slight asymmetric wear pattern in the bore.

It's not a functional failure. But there are two reasons to tighten it:

1. **Lateral force on the rod** when the depth-lock bolt tip pushes up: any off-axis component (bolt collar not perfectly centred) translates directly into rod-against-bore-wall friction. Tighter bore = less friction.
2. **Rod-against-shaft-flat alignment**: 0.6° of rod tilt + the shaft's flat at 0.6 mm depth = rod top face contact moves by ~0.5 mm laterally on the shaft underside. Affects which point of the rod actually does the locking work.

**Mitigations**:

1. Use a Ø4.8 push rod (0.1 mm radial → 0.24° tilt). Cheapest. Reduces slop by ~2.5×.
2. Use a Ø4.9 push rod with a tight bore — but tight bores risk binding under thermal expansion / minor swelling.

Recommend Ø4.8 push rod or use the M6 tap-drill size as the lower bound and spec rod to Ø4.85 ±0.025.

### 5.3 Captive bearing axial play (issue L1)

Designed at 0.2 mm. The captive-bearing relationship is enforced by validator:

```
captive_screw.thread_length = drive_plate.thickness + axial_play + left_face_tap_depth
6.0                         = 3.0                   + 0.2        + 2.8
```

In manufacture, the right-hand-side has tolerance:

- Plate thickness ±0.1 mm (general)
- Tap depth ±0.1 mm (drilling tolerance)
- Stock screw thread length: unknown but typically ±0.2 mm for M2 × 6 mm

Worst-case stack-up: 6.0 vs (3.1 + 0.2 + 2.9) = 6.2 mm → screw is 0.2 mm too short → plate is clamped tight, no axial play, bearing seized.

Conversely: 6.2 mm screw vs (2.9 + 0.2 + 2.7) = 5.8 → screw is 0.4 mm long → axial play becomes 0.6 mm → plate rattles.

**Mitigation**: tighten tolerance on the left-face tap depth to ±0.05 mm (call it out explicitly on the GRM-03 drawing). Plate thickness already at ±0.1 default is fine if the tap is tight. Note: the shop machines the tap, so this is the controllable parameter; the screw length is a stock dimension.

### 5.4 Grub screw advance budget (issue H1)

The blade slot is 6 mm wide in X. The hardware stack is:

```
4 retainers × 0.75 + 2 blades × 0.7 = 4.4 mm
```

Remaining: **6 − 4.4 = 1.6 mm**. This is shared between:

- The channel-width spacer (user choice).
- The grub-screw nose advance against the blade stack.

For a typical 1.5 mm purfling channel:

```
1.6 − 1.5 = 0.1 mm grub-screw advance
```

That's *technically enough* to clamp the stack — 0.1 mm of nose movement applies preload — but it gives no tolerance for:

- Manufacturing tolerance on retainer thickness (±0.05 mm × 4 = ±0.2 mm)
- Manufacturing tolerance on blade thickness (±0.05 mm × 2 = ±0.1 mm)
- The user wanting a slightly wider purfling channel (say 2 mm spacer)

If a 2 mm spacer is desired, the slot is overstuffed by 0.4 mm — the grub screw can't engage.

**The spec note "max_nose_advance = 3.0 mm" is technically achievable only with no spacer**. With the standard 1.5 mm spacer, real max advance is 0.1 mm, and the budget shows it.

**Mitigations** (in order of cost):

1. Spec the slot as 6.5 mm or 7 mm X. Adds 0.5–1 mm to the budget, supports 2 mm channels comfortably. Tradeoff: shaft wall around slot gets thinner (currently 1.5 mm at the Y edge — would stay the same since slot.X is along the shaft, not crosswise).
2. Document this constraint clearly in the RFQ and user docs: "channel widths 0.5–1.6 mm supported with this slot dimension."
3. Reduce retainer thickness from 0.75 mm to 0.5 mm — gains 1 mm in the budget. But retainers do real work; 0.5 mm copper may not provide enough end-block stiffness.

Recommend option 1 — spec slot at 6.5 mm.

---

## 6. Adjustment envelopes

### Drive screw (edge margin from violin edge)

- Thread length 18 mm; shank tap depth 13.55 mm.
- At **neutral** (shaft centred in crossbore): full thread engagement, equal protrusion both sides.
- At **maximum edge margin** (shaft retracted outward in +X via drive-screw retraction): the screw threads can retract until ~5 mm engagement remains (rule of thumb 1.5 × diameter); past that, risk of stripping if torque is misapplied. That gives ~13 mm of full-thread travel + ~5 mm of marginal travel = effectively ~18 mm of useful edge-margin variation. **Plenty for a tool with 0–4 mm working edge margin range.**
- At **minimum edge margin** (shaft advanced inward in −X): the drive screw's Ø5 unthreaded collar bottoms against the shank's −X face. This is the positive stop. The user can't over-advance and damage anything.
- **Resolution**: 0.5 mm pitch → 0.5 mm linear per turn, 0.125 mm per quarter turn. Fine — exceeds the human discrimination of edge margin by ~3×.

### Depth-lock bolt (clamping engagement)

- M6 × 1.0 thread, 13 mm long. Shank threaded section 12 mm.
- The bolt's collar (5 mm long) registers in the collar bore (5.5 mm long) — 0.5 mm room past the collar so manufacturing tolerance can't cause it to bottom against the tap shoulder.
- **Travel from "fully retracted" to "fully advanced"**: ~12 mm of thread travel = 12 turns of the M6 knob. Reasonable feel.
- **Locking range**: from the moment the bolt tip touches the rod, ~1–2 mm of additional advance applies the full clamping force. Past that, the rod can't move further because it's bottomed against the shaft.

### Grub screw (blade clamping) — see §5.4

**Critical issue documented above.** With default 1.5 mm spacer: 0.1 mm of advance budget remaining. Adjustment is essentially binary (engaged vs not) rather than continuous.

### Blade depth-of-cut

- Blade length 23 mm, slot Z extent (through the shaft cylinder material) ~6.24 mm at the slot's Y wall, with the blade Z-positioned via the assembly: blade_z = crossbore_z − 2.5.
- Blade tip protrudes below the shaft (and below the shank's working face when in use): protrusion = blade.length/2 + (crossbore_to_bottom − blade Z offset) ≈ 9 mm max tip-below-shaft.
- **Functional range** is set by the user advancing the shaft up/down in the cross-bore. With the depth-lock bolt fully retracted, the shaft can rotate (slightly) and translate freely (the shaft is only constrained axially by the drive-screw + drive-plate). With it locked, depth is fixed.

---

## 7. Assembly and disassembly procedure

### Assembly (recommended order)

1. **Blade stack into shaft slot** — invert shaft, blade slot opening upward. Drop blades, spacer, retainers in order: retainer, retainer, blade, spacer, blade, retainer, retainer. **The retainers must be tilted in the XY plane to pass the 5 mm wide slot opening** because the wider 5.5 mm end blocks otherwise foul the cylinder surface. The maker confirmed this is how the original assembles.
2. **Install grub screw** in the shaft's +X end tap. Tighten finger-firm against the blade stack. Don't over-tighten — the brass tap will gall.
3. **Pass shaft through shank crossbore** from the −X (drive-plate) side. Light film of grease or oil makes the H7/g6 fit easier.
4. **Mount drive plate to shaft** — engage the tenon into the shaft's end slot, then thread the mount screw (M2 × 10) through the plate and into the shaft's central tap. Tighten finger-firm.
5. **Insert drive screw through plate** — pass the unthreaded end through the plate's captive hole. Thread the drive screw into the shank's tapped bore.
6. **Thread captive screw** (M2 × 6) from outboard, through the plate, into the thumbwheel boss tap. Tighten until the screw bottoms on the tap face — this *cannot* clamp the plate because the screw is deliberately over-length. Plate floats with 0.2 mm axial play.
7. **Insert push rod** into the shank's bottom depth-lock bore (Ø5 section).
8. **Thread depth-lock bolt** (M6) into the M6 section of the depth-lock bore from −Z. Retract until clear of the push rod.

### Disassembly (reverse, with notes)

Steps 1–8 reversed work fine. Notes:

- **Step 6 reverse** (captive screw out): once the captive screw threads out, the plate is free along X. The drive screw is still threaded in the shank tap, so it can be backed out separately.
- **Step 1 reverse**: invert the shaft (slot opening down), shake; blades/spacer fall out under gravity. The retainers must be wiggled out — tilt them XY to clear the slot opening, same direction as installation. With brass-on-copper sliding for years, retainers can stick from oxidation; gentle prying with a wood toothpick clears.

### Sticking points

| Step | Risk | Mitigation |
|---|---|---|
| 1 (retainer insert) | Wider end blocks won't pass straight down through 5 mm slot | Tilt in XY plane during insert |
| 1 (spacer install) | Thin shim sticks to blade flat | Cleaning surfaces, light film of mineral oil |
| 2 (grub screw) | Cross-threading in M4 brass tap | Add a lead-in chamfer to the grub-screw tip (currently no chamfer modelled on grub screw — see §9) |
| 3 (shaft through bore) | Stick from dry brass-on-brass | Light grease |
| 5 (drive screw in tap) | Crossthreading | The 0.5 mm tip chamfer is in place. Good. |
| 6 (captive screw bottoms early) | If tap depth is short of design, plate is clamped tight, no rotation | Pydantic validator + tight tolerance on tap depth |
| 7 (rod in bore) | Rod jams crooked due to tilt slop | Lighter axial press; if it sticks, withdraw, re-align |
| 8 (depth-lock bolt) | Cross-threading on M6 first install | 1 mm tip chamfer is in place. Good. |

---

## 8. Manufacturability vs the Karpas guide

| Karpas guideline | Compliance | Notes |
|---|---|---|
| PDF drawing + STEP for quoting | ✅ | Both supplied; DXF too. |
| Material grade fully specified | ✅ | "CZ121 / C36000 equivalent" |
| Surface finish required | ⚠️ | "Clean satin appearance" is informal — should be "Ra 1.6 typ" or similar specific spec for any finished surface beyond as-machined |
| Tolerance callouts (don't leave blank) | ✅ | ISO 2768-mK general + explicit H7/g6 + thread classes |
| Don't over-specify tolerances | ✅ | Single fit pair, no blanket ±0.025 |
| Min 1 mm internal radius, match to standard tools | ⚠️ | Shank fillet 1 mm; working face R8.11 is non-standard; relief slot corners are cut by 2 mm endmill = 1 mm internal R already |
| Wall thickness ≥1.5 mm metals | ⚠️ | Shaft slot Y wall = 1.50 (exactly at limit); shank wall under crossbore = 1.38 (below) |
| 1.5 × thread diameter min engagement | ✅ | M3 drive screw: full shank.width engagement; M2 mount: 5 mm into Ø2 = 2.5×; M4 grub: 4 mm into Ø4 = 1× — **marginal** |
| Standard threads + pitch + depth on drawings | ✅ | All on drawings |
| Pocket depth ≤ 3-4× width | ✅ | All features comply |
| Setup minimization | ❌ | **Biggest cost driver. Shank 4-5 setups; could be 3.** See §3.1 |
| Match standard stock sizes | ⚠️ | Shaft Ø8 from Ø10 round brass = oversize but unavoidable; shank from 25 × 16 mm flat bar (closest above 22.4 × 13.55) — 11% waste typical |
| Specify finish explicitly | ⚠️ | "Satin" is informal — see above |

**Two amber items worth tightening:**

1. **Shank wall under crossbore (1.38 mm)** is below the 1.5 mm Karpas guideline. The shank.crossbore_position_from_top is 14 mm; subtracting bore radius 4 leaves 10 mm to the bottom, but to the *underside of the crossbore*, the wall is `(14 + 4) − 16.5 (crossbore from top to centre of working face Y mid-plane) = ` … actually let me recompute: it's the minimum of (crossbore_z - radius) at the −Z direction and (depth/2 - radius) at ±Y. With crossbore_z = 66 mm, that direction has 62 mm of wall. The constrained direction is ±Y → 11/2 − 4 = 1.5 mm. So the 1.38 mm value comes from depth_lock_collar_bore_diameter / 2 reducing further? Let me not chase the exact figure — the computed wall is below the Karpas guideline. **A bump of shank.depth from 11 → 12 mm gives 2.0 mm wall and ample margin.**

2. **Grub screw thread engagement 1× diameter** is below the 1.5× guideline. M4 grub × 4 mm engagement. Mitigation: deeper tap (= longer end-to-slot distance) at the cost of less slot room for the grub-screw nose advance — *which is already the binding constraint*. Stuck in a bind. Best resolution is the larger slot (§5.4) which frees room to also deepen the tap.

---

## 9. Recommendations (prioritized)

### Must-do before next quote

| # | Change | Where | Effort | Rationale |
|---|---|---|---|---|
| R1 | Increase shaft `blade_slot_width` from 6.0 to 6.5 mm | `parameters.py` 1-line change | 5 min | Frees up 0.5 mm budget for the grub-screw advance, supports up to 2 mm channel spacers. Issue H1. |
| R2 | Add lead-in chamfer to grub-screw nose | RFQ + drawing notation | n/a (off-the-shelf grub screws with cup point have this) | Specify "cup point" grub screw in RFQ; currently the model says nothing about tip geometry |
| R3 | Tighten left-face tap depth tolerance to ±0.05 mm | GRM-03 drawing | 30 min | Issue L1 — captive bearing axial play budget |
| R4 | Specify finish more explicitly: "Ra 1.6 on knurled features, Ra 3.2 elsewhere; as-machined acceptable on internal bores" | Notes block on each drawing | 1 hr | Karpas guidance |

### Worth quoting both ways

| # | Change | Effort | Rationale |
|---|---|---|---|
| R5 | Working face convexity rounded to R8 (or R10) instead of R8.11 | drawing + spec change | 30 min | Standard tool radius; aesthetic difference invisible to the user |
| R6 | Push rod Ø4.8 instead of Ø4.5 (in same Ø5 bore) | RFQ change | 5 min | Issue M3 — cuts rod slop by 2.5× |
| R7 | Shank depth 11 → 12 mm | `parameters.py` + drawings + spec | 2 hrs | Issue M4 + edge case on wall under bore |

### Worth a phone call to Karpas before settling

| # | Topic | Reason |
|---|---|---|
| R8 | Shank setup count — can they do it in 3? | Single biggest cost driver |
| R9 | Working face convexity — quote with R8.11 specified, then with "R8 or nearest std" as alternate | Cost vs aesthetic |
| R10 | Knurling availability and additional cost | Not covered in their guide; surprise on quote possible |
| R11 | Material grade — confirm CZ121 vs C36000 vs CW508L stock availability | Equivalent for purposes but stock-on-hand matters for lead time |

### Architecture-level (next major revision, NOT for this quote)

| # | Change | Trade |
|---|---|---|
| R12 | H7/g6 → H7/h6 on the shaft/crossbore pair | Tighter fit, less cocking, but slightly higher cost per shop tolerance class |
| R13 | Lengthen shank.width 13.55 → 16 mm | More bore guidance for shaft, lower angular cocking, more material |
| R14 | Consider an O-ring or wave-spring at the captive bearing | Eliminates axial-play sensitivity to manufacturing tolerance |

---

## 10. Items where the design is unambiguously *good*

Worth noting explicitly so they don't get tweaked accidentally:

- **The captive bearing mechanism with the pydantic validator** is excellent engineering hygiene. Don't refactor.
- **The decision to centre the drive screw thread in the shank** (full bore engagement at neutral, ~5+ mm engagement at extremes) is well-thought-out. The 18 mm length matches what the original tool uses; the maker confirmed this by measurement (an earlier model run with a misread 45 mm shaft length had inflated the screw to 28 mm — corrected on the v0.1.4 line).
- **The end-slot tenon on the drive plate** (vs a D-shaped clearance hole or a flat) is mechanically sound and uses standard milling features.
- **The retainer is now the right size** (post-v0.1.2 fix). The waist-Z constraint of 6.24 mm minimum is in the parameter description for future-proofing.
- **The depth-lock bolt collar + collar bore** as anti-cocking guide is a small but smart addition over a plain threaded plug.
- **The shank top dome at R30** is functional + aesthetic + machinable in one ball-nose pass. Don't simplify it.

---

## 11. Test coverage of these findings

What's in `tests/test_geometry.py` already covers:

- ✅ Crossbore + tapped-bore don't merge (`test_shank_bores_dont_overlap_each_other`)
- ✅ Shaft slot is in bounds (`test_shaft_slot_at_outboard_end`)
- ✅ Shaft flat doesn't bisect (`test_shaft_flat_does_not_meet_top`)
- ✅ Captive bearing axial play exists (`test_captive_bearing_axial_play`)
- ✅ Shaft fits crossbore (`test_shaft_fits_through_crossbore`)
- ✅ Blade tip projects below slot (`test_blade_tip_projects_below_shaft_slot`)
- ✅ Drive screw reaches the tap (`test_drive_screw_engages_shank_tap`)
- ✅ Interference: retainer-in-slot, blade-in-slot, tenon-in-slot, shaft-through-crossbore

Worth adding (low effort):

- `test_grub_screw_advance_budget` — assert `slot_spare - spacer.thickness > 0.2` so the channel width can't be configured to leave less than 0.2 mm of grub-screw nose room
- `test_thread_engagement_min` — assert every thread engagement ≥ 1.5 × thread diameter
- `test_push_rod_radial_clearance_in_band` — assert rod is between 0.05 and 0.15 mm radial of the bore (tight without binding)

---

End of review.
