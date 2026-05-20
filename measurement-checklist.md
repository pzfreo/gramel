# Measurement checklist — original purfling cutter

**Purpose:** capture every dimension marked `[TBM]` in `specification.md`, plus redundant measurements to sanity-check the parametric chain. Work in millimetres throughout.

**Tools:**
- Vernier or digital callipers (resolution 0.01 mm)
- Micrometer if you have one (blade thickness especially)
- Thread pitch gauge OR a set of known fasteners to match against
- Small engineer's square
- Pin gauges or a set of drill shanks (for measuring bores)
- Feeler gauges (for the convexity of the working face and any axial play)
- Camera/phone for the photos called out below
- A sheet of paper and a pencil for stamps and knurl rubbings

**Order matters** — earlier groups are upstream in the parametric chain.

---

## Phase 0 — Photos (before any disassembly)

Take these with a ruler in frame for scale.

- [ ] **P0.1** End view from the blade side, showing the blade slot and how the blades/spacer sit in it. Particularly how the blades are oriented and how the spacer sits relative to them.
- [ ] **P0.2** End view from the thumbwheel side, showing the drive plate, the captive screw head, and the gap (if any) between captive-screw head and drive plate.
- [ ] **P0.3** Top view of the whole assembly.
- [ ] **P0.4** Looking straight down the shaft from the blade end.
- [ ] **P0.5** Working face straight-on, showing the relief slot.
- [ ] **P0.6** End-on view of the working face — i.e. looking at one end of the shank to see the cross-section profile of the working face (convexity).
- [ ] **P0.7** Bottom of the shank, showing the depth-lock knob and how the bolt enters.
- [ ] **P0.8** Any maker's marks, stamps, or numbers — note location.

---

## Phase 1 — Blades and spacer (Tier 1)

If possible, slacken the grub screw and remove the blades and spacer. Mark each so they go back in the same orientation.

- [ ] **M1.1** Blade thickness `t_b` — across the wide flat. Three measurements along the blade; record min/max.
- [ ] **M1.2** Blade width `w_b` — the dimension that sits in the Z direction in the slot.
- [ ] **M1.3** Blade total length `l_b` including ground tip.
- [ ] **M1.4** Bevel — single or double? Bevel angle (estimate). Which side?
- [ ] **M1.5** Tip geometry — straight, angled, or curved? Sketch.
- [ ] **M1.6** Confirm both blades are identical (or note differences).
- [ ] **M1.7** Spacer thickness `t_s`.
- [ ] **M1.8** Spacer width and height — particularly: is the spacer's Z-height *less* than the blade width, so blades protrude below it? Sketch.
- [ ] **M1.9** Spacer material (magnet test: brass/non-ferrous vs steel).
- [ ] **M1.10** Are there other spacers stored on the tool or supplied with it? If yes, list thicknesses.

---

## Phase 2 — Shaft, blade slot, grub screw (Tier 2)

With blades and spacer removed, the slot is accessible.

- [ ] **M2.1** Shaft OD `d_shaft`. Round or has a flat? If a flat, measure its width, length, and angular position relative to the blade slot.
- [ ] **M2.2** Shaft total length `L_shaft`.
- [ ] **M2.3** Blade slot width (Y) `W_slot`.
- [ ] **M2.4** Blade slot length (Z) `L_slot`.
- [ ] **M2.5** Confirm slot passes fully through the shaft top-to-bottom (item 10 of spec).
- [ ] **M2.6** Distance from shaft right-end face to the **right wall** of the blade slot `pos_slot_right`.
- [ ] **M2.7** Distance from shaft right-end face to the **left wall** of the blade slot `pos_slot_left` (= `pos_slot_right + W_slot`).
- [ ] **M2.8** Grub screw thread — gauge or match to standard fasteners.
- [ ] **M2.9** Grub screw total length, head style, drive type (slotted/hex/knurled).
- [ ] **M2.10** Maximum grub-screw nose advance — with the screw fully home (no blades in slot), how far past the right wall of the slot does its nose extend? This tells you the tap depth and clamp range.
- [ ] **M2.11** Drive-plate mounting features on the shaft (left end) — soldered fillet, pinned, or tapped holes? If tapped, thread size, position, count. Sketch and photograph in close-up.

---

## Phase 3 — Shank (Tier 3)

Best done with the shaft removed if it comes out cleanly without forcing.

- [ ] **M3.1** Shank cross-section — width (Y) × depth (Z). Spot-check at top, middle, bottom.
- [ ] **M3.2** Shank total length `L_shank`.
- [ ] **M3.3** Shaft cross-bore diameter `D_xb` — pin gauges or largest drill shank that passes through with slip fit.
- [ ] **M3.4** Position of the shaft cross-bore from the top of the shank `pos_xb`.
- [ ] **M3.5** Shank tapped bore — diameter, position. Run a known thread into it to identify pitch and major diameter.
- [ ] **M3.6** Centre-to-centre distance from shank tapped bore to shaft cross-bore `gap_bores`. **Most easily measured by inserting tight-fitting pins/wires in both bores and measuring between them, then correcting for half each pin's diameter.**
- [ ] **M3.7** Working face profile — truly curved, or flat with chamfered edges? Hold a steel rule across; check for light gap at centre or corners.
- [ ] **M3.8** Convexity height (if curved) — rise at centre vs corners, measured with feeler gauges under a straightedge.
- [ ] **M3.9** Relief slot width (Y), depth (Z), length (X). Does it run full length of the shank?
- [ ] **M3.10** Contact corner width (Y) either side of relief slot. Should be symmetric.
- [ ] **M3.11** Depth-lock blind bore — diameter (from the depth-lock bolt) and depth (insert a thin rod from the bottom with the bolt removed, mark where the rod stops).
- [ ] **M3.12** Depth-lock thread — identify from the bolt itself.

---

## Phase 4 — Drive train (Tier 4)

Remove the captive screw (carefully — it's small) and the drive screw assembly comes free.

- [ ] **M4.1** Drive screw thread — pitch and major diameter. **Critical:** the pitch is the edge-margin resolution.
- [ ] **M4.2** Drive screw total length.
- [ ] **M4.3** Tap on the **left end face of the thumbwheel** — diameter and depth of the tap that the captive screw goes into. Use the captive screw itself to identify thread.
- [ ] **M4.4** Thumbwheel left end-face geometry — flat? Stepped boss with a recessed area for the drive plate to bear on? This is the surface the drive plate floats against on its inboard side.
- [ ] **M4.5** Sanity check on pitch — reassemble enough to turn the thumbwheel 10 full turns, measure shaft translation, divide by 10. Compare to M4.1.
- [ ] **M4.6** Thumbwheel OD and thickness.
- [ ] **M4.7** Thumbwheel knurl style — straight or diamond? Pitch (lines per 5 mm).
- [ ] **M4.8** Confirm thumbwheel + drive screw is integral (one piece) or a joined assembly. Try to wiggle/twist them relative to each other — there should be no movement.

---

## Phase 5 — Drive plate and captive-screw bearing (Tier 5)

- [ ] **M5.1** Drive plate dimensions — height (Z), width (X), thickness (Y).
- [ ] **M5.2** Drive plate clearance hole diameter.
- [ ] **M5.3** Drive plate clearance-hole position — distance from the bottom of the plate (the shaft) to the centre of the clearance hole. **Must equal `gap_bores` from M3.6.** A useful sanity check.
- [ ] **M5.4** Position of drive plate along shaft — the drive plate is mounted on the **outboard (left) end face of the shaft**. Confirm this and measure the distance from the shank's left face to the drive plate's inboard face when the shaft is at its mid-Y-travel position.
- [ ] **M5.5** Captive screw — overall length, thread length, head diameter and thickness, drive type (slotted, etc.).
- [ ] **M5.6** Captive screw tap engagement length when fully home — back the captive screw out a couple of turns, measure the screw's protrusion change. The "bottomed" position is when the screw stops turning before its head clamps.
- [ ] **M5.7** Axial play in the bearing — with the captive screw fully home, gently push and pull on the drive plate along the shaft axis; measure the total movement. Or use feeler gauges to find the larger of the two gaps (between drive plate and captive-screw head; between drive plate and thumbwheel left face). Should be small but non-zero. **This is the design feature.**

---

## Phase 6 — Depth lock

- [ ] **M6.1** Depth-lock bolt total length.
- [ ] **M6.2** Depth-lock bolt thread (should match M3.12).
- [ ] **M6.3** Depth-lock bolt tip geometry — flat, cone, cup, dog point.
- [ ] **M6.4** Does the shaft show a wear mark on its underside where the depth-lock bolt bears? Photograph.
- [ ] **M6.5** Depth-lock knob diameter and thickness; knurl style.

---

## Phase 7 — Travel and range checks (global sanity)

- [ ] **M7.1** Full shaft Y travel — from thumbwheel-rotated-all-one-way to all-the-other-way. **Don't force past either end stop.**
- [ ] **M7.2** Edge-margin range — measured as the distance from the working face to the centre of the *near* blade, at both extremes of Y travel.
- [ ] **M7.3** Spacer range supported — minimum and maximum spacer thickness the slot + grub-screw advance can accommodate.
- [ ] **M7.4** Blade projection range — how far the blades can sit below the bottom of the shaft before they bottom out somehow, or before the grub screw can no longer clamp them effectively.

---

## Phase 8 — Materials, finish, marks

- [ ] **M8.1** Material confirmation — magnet test on each part.
- [ ] **M8.2** Finish observations — overall texture, polish level, patina, any signs of original lacquer.
- [ ] **M8.3** Maker's marks, stamps, hallmarks — transcribe with location. Pencil rubbings for anything faint.
- [ ] **M8.4** Anything else clever or unusual that the spec and diagram don't already capture.

---

## After measurement — feeding back into the spec

Most measurements map directly to a symbol in §4 of the spec (`t_b`, `gap_bores`, etc.). Where the original is in imperial units, convert to mm and then round to a sensible metric value, flagging the rounding (e.g. "original 0.030 in. = 0.76 mm; specified as 0.80 mm to match standard ground blade stock"). Note any rounding decisions explicitly when filling in the spec, so the draftsman knows which numbers came straight off the original and which are interpretations.
