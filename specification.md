# Purfling Cutter — Design Specification

**For:** CAD draftsman producing a fully-dimensioned parametric 3D model for CNC quotation
**Status:** Draft — measurements to be added (marked `[TBM]` throughout)
**Units:** Metric (mm). Original tool is likely imperial; convert and round to sensible metric values.
**Reference:** see `diagram.svg` / `diagram.png` for part naming and the X/Y/Z axes.

---

## 1. Purpose and design intent

A **double-blade purfling cutter** used in violin-family lutherie. The luthier presses the working face of the tool against the edge of an instrument plate and draws it around the perimeter. Two parallel **blades** simultaneously score two knife lines into the wood; the waste between is later chiselled out to form the channel into which the decorative purfling strip is glued.

The tool offers **three independent adjustments**:

| Adjustment | Sets | Set by | Locked by |
|---|---|---|---|
| **Blade spacing** | Width of the purfling channel | Choice and order of blades + spacer in the blade slot | Grub screw |
| **Blade projection** | Depth of cut into the plate | Vertical position of blades in the slot before tightening | Grub screw (same one) |
| **Edge margin** | Distance from plate edge to the cut lines | Thumbwheel (fine feed via drive screw) | Depth-lock knob (long bolt up inside shank) |

**Three features distinguish this tool from typical purfling cutters:**

1. **Fine-feed edge margin via integral thumbwheel + drive screw.** Turning the thumbwheel rotates a screw that runs in a tapped bore in the shank, parallel to and just above the shaft. The screw pulls the shaft along via a vertical drive plate. This gives smooth, repeatable adjustment instead of slide-and-clamp.

2. **Captive bearing made from two pieces only.** Reading from outboard inward, the order at the top of the shank is: silver-screw head → drive plate → small axial-play gap → thumbwheel → drive screw → shank. The silver screw threads rightward through a clearance hole in the drive plate and into a tapped hole on the left end face of the thumbwheel. It is deliberately over-length: it bottoms on the tap *before* its head clamps the drive plate. The plate therefore floats free in axial play between the silver-screw head (on its outboard face) and the thumbwheel's left end face (on its inboard face). No thrust washer, no shoulder, no circlip — just a deliberately over-length screw and a clearance hole.

3. **Convex working face with relief slot.** The face that bears on the plate edge is not flat. It carries a vertical relief slot down its full length, leaving two narrow contact corners that act as a two-point fence. This self-corrects against the violin's irregular edge and resists rocking.

These three features are the reason for the commission. The CAD model must preserve them.

---

## 2. Axes and naming convention

See accompanying diagram. These names are canonical — please use them in the CAD part tree and in any correspondence.

**Axes** (right-handed, origin at the centre of the working face at the height of the shaft):

- **X** — along the shank (vertical in diagram); tool-travel direction in use.
- **Y** — along the shaft AND normal to the working face. The shaft cross-bore and the shank tapped bore both run along Y and pass *through* the working face — the working face is the +Y face of the shank. Edge-margin adjustment translates the shaft along Y.
- **Z** — perpendicular to both X and Y; blade-projection (depth-of-cut) direction. The relief slot's width is in Z (across the working face) and the slot's length is along X.

**Parts:**

| Name | Description |
|---|---|
| **Shank** | Square-section brass body. Spine of the tool. Doubles as the fence. |
| **Working face** | Right-hand long face of the shank. Convex profile (~R 8 mm, ≈2 mm sagitta over the depth chord) with a vertical relief slot. Slot runs from the bottom of the shank up to the shaft cross-bore only — it does **not** continue above the shaft. |
| **Top dome** | The +X end of the shank (where the drive screw sits) is rounded into a spherical dome of similar radius to the working face. Bottom end (where the depth-lock knob sits) is flat. |
| **Contact corners** | Two narrow strips of the working face, one each side of the relief slot. The actual bearing surfaces on the workpiece. |
| **Relief slot** | Vertical slot down the centre of the working face. Runs from the bottom of the shank up to (but not above) the shaft cross-bore. |
| **Shaft cross-bore** | Plain horizontal through-hole near the top of the shank. Sliding fit on the shaft. |
| **Shank tapped bore** | Tapped horizontal through-hole, directly above and parallel to the shaft cross-bore. Carries the drive screw. Tapped along the full Y length of the shank. |
| **Depth-lock blind bore** | Long vertical bore running up inside the shank from the bottom, opening into the shaft cross-bore at the top. **Only the lower portion is tapped** (for the depth-lock bolt); above the tapped section is a smooth bore that holds the push rod. |
| **Depth-lock push rod** | Steel rod sitting in the smooth (upper) section of the depth-lock blind bore. Its lower end is pushed up by the depth-lock bolt; its upper end bears on the underside of the shaft to lock it. **Missing from earlier drafts of this spec.** |
| **Shaft** | Brass bar passing horizontally through the shaft cross-bore. Carries the blades at its right end. Translates in Y to set edge margin. |
| **Blade slot** | Vertical through-slot in the right end of the shaft. Open top and bottom (blades drop through). Wide enough to hold two blades plus a spacer side by side. |
| **Shaft end tap** | Tapped hole in the right end face of the shaft, along the shaft axis. Receives the grub screw. |
| **Grub screw** | Steel screw threaded into the shaft end tap from the right. Its inner end pushes the blade stack horizontally against the left wall of the blade slot, clamping blades and spacer together. |
| **Blades** | Two flat tool-steel blades. Replaceable. See §5 on blade strategy. |
| **Spacer** | Thin brass or steel shim between the two blades, setting the purfling channel width. Replaceable; different spacers give different channel widths. |
| **Drive plate** | Brass plate standing vertically up from the **outboard (left) end** of the shaft, fixed to it (originally soldered; in this build screwed). Has a clearance hole near its top through which the silver screw passes. **Sits outboard of the thumbwheel.** |
| **Thumbwheel** | Knurled disc **sitting between the drive plate (outboard) and the shank (inboard)**, on the left end of the drive screw. **Integral with the drive screw** — turned from one piece (or permanently joined). |
| **Drive screw** | Threaded shaft extending right (inboard) from the thumbwheel into the shank tapped bore. The thumbwheel's left end face carries a tapped hole along the drive-screw axis for the silver screw. |
| **Silver screw** | Small screw passing rightward from outboard through the drive plate's clearance hole, across a small axial-play gap, and threading into the tap on the thumbwheel's left end face. **Deliberately over-length** so it bottoms on the tap, leaving the drive plate floating in axial play between its head (outboard) and the thumbwheel's left face (inboard). |
| **Depth-lock bolt** | M6 bolt threaded into the lower (tapped) section of the depth-lock blind bore. Knurled knob at the bottom. Its upper end pushes the depth-lock push rod; the rod (not the bolt) is what bears on the underside of the shaft. |
| **Depth-lock knob** | Knurled knob at the bottom of the shank, integral with the depth-lock bolt. |

---

## 3. Mechanism summary

For the draftsman, so the CAD assembly mates are physically correct.

**Setting edge margin.** Turning the thumbwheel rotates the integral thumbwheel + drive screw assembly. The drive screw runs in the shank tapped bore, so its rotation translates it in Y relative to the shank. The thumbwheel translates with it. The drive plate (mounted to the outboard end of the shaft) is captured on the silver screw between the screw's head (outboard side of plate) and the thumbwheel's left end face (inboard side of plate), with a deliberate tiny axial play so the plate doesn't bind. As the thumbwheel-and-drive-screw assembly translates in Y, the drive plate is dragged along with it, and the shaft follows. The thumbwheel, drive screw, and silver screw all rotate together; the drive plate and shaft translate without rotating.

**Locking the setting.** The depth-lock knob, at the bottom of the shank, is on the end of an M6 bolt that engages the **lower (tapped) section** of the depth-lock blind bore. Above the tapped section the bore is smooth and contains a steel push rod. Tightening the knob advances the bolt up; the bolt's tip pushes the push rod; the push rod's upper end bears on the underside of the shaft (which crosses through the upper part of the shank). This pinches the shaft against the upper wall of the shaft cross-bore and locks it in Y. The push rod is a separate intermediary part — earlier drafts of this spec incorrectly described the bolt itself as bearing on the shaft.

**Setting blade spacing and projection.** With the grub screw loose, blades can be dropped into the blade slot from above and fall straight through (top and bottom of the slot are open). The luthier positions: blade — spacer — blade in the slot, sets the vertical position to give the desired blade projection (depth of cut), and tightens the grub screw. The grub screw threads into the shaft end tap from the right; its inner end advances along the shaft axis and pushes the rightmost blade leftward. This pinches the whole stack — blade, spacer, blade — against the left wall of the blade slot. Blade spacing equals the spacer thickness.

**Using the tool.** Working face of the shank rides on the plate edge; the two contact corners bear, the relief slot clears burrs and irregularities. The tool is drawn along the edge (X direction). Both blades cut simultaneously.

---

## 4. Driving dimensions and the parametric chain

The CAD model should be built **parametrically**: the dimensions in §4.1 drive everything else. Wall-thickness rules in later tiers depend on those. Changing a driving parameter (e.g. blade thickness if a different blade supply is found) must propagate cleanly through the model.

Each tier table below names the dimension by its full **field path** (`blade.thickness`, `shank.length`, etc.), replacing the original short symbols (`t_b`, `L_shank`). A few fields are owned by mate classes that span multiple parts (e.g. `captive_bearing.axial_play`) — noted in the relevant rows.

### 4.1 Tier 1 — Blades and spacer (decide first)

| # | Parameter | Code field | Value | Notes |
|---|---|---|---|---|
| 1 | Blade thickness | `blade.thickness` | `[TBM]` (likely 0.6–1.0 mm) | Across the wide flat. The face the grub screw pushes against. |
| 2 | Blade width | `blade.width` | `[TBM]` (likely 4–6 mm) | The Z dimension of the blade, sitting in the slot. |
| 3 | Blade length | `blade.length` | `[TBM]` (likely 18–28 mm) | Total length, including ground tip. Must be long enough that the blade can fall fully into the slot AND extend below for the cut. |
| 4 | Blade bevel | `blade.bevel_angle` | `[TBM]` | Single bevel; angle and side. |
| 5 | Spacer thickness range | `spacer.thickness` | `[TBM]` (target 1.0–3.0 mm in 0.2 mm steps) | Sets purfling channel width. Multiple spacers will be supplied. |
| 6 | Spacer height (Z) | `spacer.height` | Slightly less than `blade.width` | So the blades protrude below the spacer when set deep. `[TBM]` |
| 7 | Total clamped stack thickness | `stack_thickness` (derived) | `= 2 × blade.thickness + spacer.thickness` | Range determines blade slot width. |

### 4.2 Tier 2 — Shaft (driven by Tier 1 + wall-thickness rules)

| # | Parameter | Code field | Value rule | Notes |
|---|---|---|---|---|
| 8 | Blade slot width (Y) | `shaft.blade_slot_width` | `≥ max(stack_thickness) + grub_screw.max_nose_advance + clearance` | Must fit the widest expected stack plus enough room for the grub screw to advance and clamp. |
| 9 | Blade slot length (Z) | `shaft.blade_slot_length` | `≥ blade.width + clearance` | Just larger than blade width so blades sit cleanly. |
| 10 | Blade slot vertical extent | (through) | Open top and bottom | Blades fall freely through the shaft. Critical: the slot must NOT have a closed bottom. |
| 11 | Shaft cross-section | `shaft.cross_section` | Round | Recommended round; rotation of the shaft is prevented by the drive plate's screw connection and (if needed) by the depth lock bearing on a flat — see open question Q3. |
| 12 | Shaft OD | `shaft.outer_diameter` | Derived from items 8–9 with wall rules | Round to nearest 0.5 mm. |
| 13 | Wall thickness around blade slot | `shaft_wall_around_slot` (derived) | `= min((OD − slot_width)/2, (OD − slot_length)/2)`; rule: `≥ 2 mm`, `≥ 1.5 × blade.thickness` | **Critical constraint.** Derived from shaft OD and slot dimensions; spec rule enforced by validator. |
| 14 | Wall thickness around shaft end tap | `shaft_wall_around_end_tap` (derived) | `= shaft.end_to_slot_distance − shaft.end_tap_depth`; rule: `≥ 1.5 × thread major radius` | **Critical constraint.** Between the threaded hole at the right end of the shaft and the far wall of the blade slot. |
| 14a | Grub-screw tap depth (from right end face) | `shaft.end_tap_depth` | `[TBM]` | Depth of the tap that the grub screw threads into. Drives item 14. |
| 15 | Grub screw thread | `grub_screw.thread` | M3 or M4 `[TBM]` | Specify before sizing shaft end. |
| 16 | Grub screw nose protrusion (max) | `grub_screw.max_nose_advance` | `≥ shaft.blade_slot_width − min(stack_thickness)` | Grub screw must be able to reach the thinnest stack and clamp it. |
| 17 | Distance from shaft right-end face to blade slot | `shaft.end_to_slot_distance` | `[TBM]` | Determines how much wall is between shaft end tap and blade slot. See item 14. |
| 18 | Shaft total length | `shaft.length` | `[TBM]` | Must support: blade slot at right end + protrusion through shank during full Y travel + length to clear thumbwheel + axial gap + drive plate at outboard (left) end. |
| 19 | Drive plate mounting on shaft | `shaft.drive_plate_mount` | Two tapped holes, M2 or M2.5 `[TBM]`, on the **outboard end face of the shaft** | Replaces the original soldered joint. The two screws also stop the drive plate (and the shaft) from rotating. |

### 4.3 Tier 3 — Shank (driven by Tier 2 + wall-thickness rules)

| # | Parameter | Code field | Value rule | Notes |
|---|---|---|---|---|
| 20 | Shaft cross-bore diameter | `shank.crossbore_diameter` | `shaft.outer_diameter + sliding-fit allowance` | **Precision fit.** H7/g6 or equivalent (≈ 0.02–0.04 mm clearance). |
| 21 | Shank tapped bore | `drive_screw.thread` | M4 × 0.5 fine, or M3 fine `[TBM]` | Fine pitch preferred for fine edge-margin adjustment. |
| 22 | Centre-to-centre distance between shank tapped bore and shaft cross-bore | `shank.crossbore_to_tapped_bore_gap` | `[TBM]` | Must be large enough that wall between the two bores (≥ 1.5 × thread major radius, item 23) is preserved. |
| 23 | Wall thickness between shank tapped bore and shaft cross-bore | `shank_wall_between_bores` (derived) | `= gap − crossbore_radius − tapped_drill_radius`; rule: `≥ 1.0 × thread major radius`, `≥ 1.2 mm` | **Critical constraint.** Wall rule relaxed after measuring the original (was `≥ 1.5 × radius`, `≥ 2 mm`). |
| 24 | Wall thickness around shaft cross-bore (other directions) | `shank_wall_around_crossbore` (derived) | `= min(crossbore_x − crossbore_radius, depth/2 − crossbore_radius)`; rule: `≥ 0.15 × D_xb`, `≥ 1 mm` | **Critical constraint.** Wall rule relaxed after measuring the original tool (was `≥ 0.6 × D_xb`, `≥ 3 mm` — those values were a CAD-shop guess; the real brass tool runs much closer to 0.15× the bore diameter). Bore axis is along Y; walls measured in X (toward bottom of shank) and Z (top and bottom of cross-section). Assumes bore centred in Z. |
| 25 | Wall thickness around shank tapped bore (other directions) | `shank_wall_around_tapped_bore` (derived) | `= min(pos_tb − tap_drill_radius, depth/2 − tap_drill_radius)`; rule: `≥ 1.0 × thread major radius`, `≥ 1 mm` | **Critical constraint.** Wall rule relaxed (was `≥ 1.5 × radius`, `≥ 3 mm`). |
| 26 | Shank cross-section | `shank.width` × `shank.depth` (Y × Z) | Square (or near-square rectangular) | `width` is depth-from-working-face into the body (Y direction); `depth` is the cross-section dimension perpendicular to both the shank length and the shaft (Z direction). Must satisfy items 23, 24, 25. |
| 27 | Shank length (X) | `shank.length` | `[TBM]` (likely 90–110 mm) | Affects balance, reach, and the length of the depth-lock blind bore. |
| 28 | Shank cross-bore position (from top of shank) | `shank.crossbore_position_from_top` | `[TBM]` | Near the top. Sets how high the mechanism sits relative to the working face. |
| 29 | Shank tapped bore position | `shank.tapped_bore_position_from_top` | `= shank.crossbore_position_from_top − shank.crossbore_to_tapped_bore_gap` | Derived; sits above the shaft cross-bore. |
| 30 | Depth-lock blind bore diameter | `shank.depth_lock_bore_diameter` | Per depth-lock thread tap-drill, also accepts the push rod (sliding fit) | M6 tap drill is 5.0 mm; same diameter also accepts the 5 mm steel push rod in the upper (untapped) section of the bore. |
| 30a | Depth-lock bore threaded length | `shank.depth_lock_threaded_length` | `[TBM]` (ESTIMATE: 12 mm) | Only the *lower* section of the bore is tapped — typically just enough to engage the bolt fully. Above the tapped section the bore is smooth and contains the push rod. |
| 31 | Depth-lock blind bore depth | `shank.depth_lock_bore_depth` (derived) | `= shank.length − shank.crossbore_position_from_top` | Bore extends from the bottom of the shank up to and into the shaft cross-bore — the push rod must reach the cross-bore region to bear on the shaft. (Earlier draft of this spec called for a `small_clearance` below the cross-bore; that was wrong.) |
| 32 | Depth-lock thread | `depth_lock.thread` | M6 measured | Hand-clamped, not metered. |
| 33 | Relief slot width (Z) | `shank.relief_slot_width` | `[TBM]` (likely 2–8 mm) | Wide enough to clear edge irregularities; narrow enough to keep contact corners close. Measured *across* the working face, perpendicular to slot length. |
| 34 | Relief slot depth (Y) | `shank.relief_slot_depth` | ~1 mm | Depth into the body from the working face. Just enough to guarantee no contact in slot region. |
| 34a | Relief slot length (X) | `relief_slot_length` (derived) | `= shank.length − shank.crossbore_position_from_top` | Slot runs from the bottom of the shank up to the shaft cross-bore. Does *not* extend above the shaft (corrected from earlier drafts that said "full length of the shank"). |
| 35 | Working face convexity radius | `shank.working_face_radius` (derived) | Derived from the measured sagitta/chord: `R = (c² + 4s²) / (8s)` | Earlier spec drafts described this as a "large radius". Measurement gives R ≈ 8 mm on the original — far smaller than implied; the spec was wrong. |
| 35a | Top dome radius | `shank.top_dome_radius` | Similar to working face radius | Spherical dome at the +X end (top, next to the drive screw). Bottom end (−X, next to the depth-lock knob) is flat. |
| 35b | Edge fillet radius | `shank.edge_fillet_radius` | ~0.5 mm | Ergonomic finishing layer, not previously specified in §4. Applied to every external edge of the shank. |
| 36 | Contact corner width (Z) | `shank.contact_corner_width` (derived) | `= (shank.depth − shank.relief_slot_width) / 2` | Symmetric. Contact corners sit either side of the relief slot, measured in Z across the working face. |

### 4.4 Tier 4 — Drive train

| # | Parameter | Code field | Value rule | Notes |
|---|---|---|---|---|
| 37 | Drive screw thread | `drive_screw.thread` | Matches item 21 | |
| 38 | Drive screw thread pitch | `drive_screw.thread_pitch` | ≈ 0.5 mm (user estimates 2 turns/mm) | Sets adjustment resolution. |
| 39 | Drive screw length | `drive_screw.length` | `[TBM]` | Must support full Y travel of shaft + adequate engagement at minimum-margin setting. |
| 40 | Drive screw left-end tap | `drive_screw.left_face_tap` | For silver screw; M2 or M2.5 `[TBM]` | Bottomed by the silver screw — see Tier 5. Depth: `drive_screw.left_face_tap_depth`. |
| 41 | Thumbwheel diameter | `thumbwheel.diameter` | `[TBM]` (likely 15–22 mm) | Big enough for fingertip torque; small enough not to foul the work. |
| 42 | Thumbwheel thickness | `thumbwheel.thickness` | `[TBM]` | |
| 43 | Thumbwheel knurl | `thumbwheel.knurl` | Straight (axial) `[TBM]` | |
| 44 | Drive screw and thumbwheel join | — | **Integral** — one piece, or permanently joined | Must rotate as a unit. |

### 4.5 Tier 5 — Drive plate and silver-screw bearing

Geometry, outboard → inboard along Y: silver-screw head → drive plate → axial-play gap → thumbwheel left face → (silver-screw thread engagement inside thumbwheel).

| # | Parameter | Code field | Value rule | Notes |
|---|---|---|---|---|
| 45 | Drive plate height (Z) above shaft | `drive_plate.height` | `shank.crossbore_to_tapped_bore_gap + clearance_above_screw` | Plate must rise from shaft top to drive-screw axis, with enough material above and below the clearance hole. |
| 46 | Drive plate width (X) | `drive_plate.width` | `[TBM]` | |
| 47 | Drive plate thickness (Y) | `drive_plate.thickness` | `[TBM]` (likely 1.5–2.5 mm) | |
| 48 | Drive plate clearance hole | `drive_plate.clearance_hole_diameter` | `≥ silver_screw.thread.major × 1.1` | Light radial clearance — does not need precision (per user; see §8). |
| 49 | Drive plate position on shaft (X) | `drive_plate.shaft_mount_position` | Mounted on the outboard end face of the shaft | The shaft must be long enough on its outboard side that the drive plate sits clear of the thumbwheel. The axial-play gap (item 53) sits between them. |
| 50 | Silver screw thread | `silver_screw.thread` | Per item 40 | M2 or M2.5 `[TBM]`. |
| 51 | Silver screw useful length (head underside to tip) | `silver_screw.length` *(owned by `captive_bearing`)* | `= drive_plate.thickness + captive_bearing.axial_play + drive_screw.left_face_tap_depth` | **Critical:** the screw must bottom on the tap with `captive_bearing.axial_play` mm of axial clearance remaining between its head and the drive plate. |
| 52 | Silver screw head | `silver_screw.head` | Pan or cheese; larger than `drive_plate.clearance_hole_diameter` | Acts as the retainer. |
| 53 | Axial play | `captive_bearing.axial_play` *(owned by `captive_bearing`)* | 0.1–0.3 mm | The designed bearing clearance. Verify after assembly with feeler gauges. |

This is the *bearing*: silver-screw head + drive plate + thumbwheel left end face form a captive but non-binding interface. The drive plate floats in the axial-play gap; the thumbwheel rotates freely.

---

## 5. Open questions to resolve from the original

In priority order.

1. **Spacer storage / set.** Are spacers loose, or stored on the tool somehow? Are they brass or steel? If a set of different thicknesses is supplied, what are they?

2. **Wall between shaft end tap and blade slot.** How much material is there between the end of the blade slot and the bottom of the shaft end tap? Determines how deep the grub screw can be tapped without breaking through.

3. **Shaft rotation prevention.** Does the original rely solely on the drive plate's two screws to prevent shaft rotation in the shaft cross-bore, or is there also a flat machined along the shaft for the depth-lock bolt to bear on? Likely just the drive plate, but worth checking. (If there's no flat, the depth-lock bolt bears on the shaft's curved underside, which is fine — point contact is more than adequate clamping for this application.)

4. **Drive screw end at the shank tapped bore.** When the tool is at minimum edge margin (shaft pushed all the way toward the work), does the drive screw exit the shank tapped bore on the far side, or just bottom out internally?

5. **Maker's marks** on the original — note location and reproduce or omit as preferred.

---

## 6. Materials

| Component | Material | Notes |
|---|---|---|
| Shank | Free-machining brass (CZ121 / C36000) | Matches original. |
| Shaft | Free-machining brass | Brass to match the original. |
| Drive plate | Brass | Small cosmetic part. |
| Thumbwheel + drive screw (integral) | Brass | Knurl finish on thumbwheel. |
| Depth-lock knob + bolt | Brass for knob; steel bolt OR brass throughout | Original is likely brass throughout. Steel bolt with a brass knob silver-soldered on is an alternative. |
| Silver screw | Stainless steel | Small standard fastener; "silver" refers to its visible appearance versus the brass around it. |
| Grub screw | Stainless or hardened steel | Standard part — slotted, socket, or knurled head per original. |
| Drive plate mounting screws | Stainless steel | M2 / M2.5; flat or pan head, countersunk into drive plate if possible. |
| Blades | O1 tool steel, hardened and tempered, OR commercial Ibex/Herdim blades | See §7. |
| Spacers | Brass or steel shim stock | Set of sizes. |

---

## 7. Blade strategy (decide before finalising)

No convenient commercial supply of loose purfling blades exists. Three options:

1. **Commercial donor blades.** Buy a complete Ibex or Herdim purfling cutter, measure those blades, spec the new tool around them. Gives a permanent reorderable supply path. **Recommended.**
2. **Bespoke ground blades.** Have a toolmaker grind matching blades from O1 flat stock, hardened and tempered.
3. **Repurposed marking-knife or scalpel blanks.** Cheap and replaceable but non-traditional.

**Action item for the owner:** decide which before the spec goes to the draftsman, then fill in §4.1 with the chosen blade's dimensions.

---

## 8. Tolerances and fits

**Critical fits** (determine cut quality and must be tight):

| Interface | Recommended fit | Reason |
|---|---|---|
| Shaft in shaft cross-bore | H7/g6 (sliding, ≈ 0.02–0.04 mm clearance) | Controls how square the cut stays. |
| Drive screw in shank tapped bore | Standard tapped thread, class 6H/6g | Backlash here = backlash in edge-margin adjustment. |
| Blade slot to blade thickness | Light, hand-fit | The grub screw clamps the slop out. |

**Non-critical clearances** (just need not to bind):

| Interface | Recommended |
|---|---|
| Silver screw in drive plate clearance hole | Generous (0.1–0.3 mm radial) — sloppy is fine |
| Drive plate against thumbwheel end face | Light sliding contact when stationary; rotational clearance via the axial play of the silver screw |
| Drive plate position on shaft | Fixed location, no movement intended |
| Depth-lock bolt in blind bore | Standard thread fit |

General machining tolerance: **±0.05 mm** unless noted otherwise.

---

## 9. Finish

| Surface | Finish |
|---|---|
| All visible brass | Draw-filed and polished to a satin or low-gloss finish. No lacquer (original style). |
| Knurls | Straight (axial) knurl, medium pitch, on thumbwheel and depth-lock knob. |
| Contact corners (working face) | Polished smooth. These bear on the violin's finished edge and must not mark it. |
| Tapped/threaded bores | Standard. |
| Shaft (inside the shank cross-bore) | Smooth, free from burrs. |

---

## 10. Function tests (acceptance criteria)

After manufacture, the tool must:

1. Sit stable on a flat reference edge with both contact corners bearing simultaneously — no rocking.
2. Allow continuous, smooth Y travel of the shaft through the full range with the depth-lock knob loose.
3. Allow the depth lock to clamp the shaft firmly with no perceptible Y movement under reasonable hand force.
4. Allow the edge-margin thumbwheel to be turned by fingertip force, with one full rotation producing approximately `[TBM]` mm of shaft translation (matching the drive-screw pitch), repeatable to within ±0.05 mm.
5. Drive plate to spin freely on the silver-screw bearing — no binding when the thumbwheel is rotated; no axial slop greater than `[TBM]` mm (target ≤ 0.3 mm).
6. Hold blades square to the shaft axis and parallel to each other to within ±0.1° after grub-screw clamping.
7. Hold blade spacing to within ±0.05 mm of the spacer thickness over a representative cut (full perimeter of a violin top).
8. Cut two clean, parallel lines in figured maple ≥ 0.5 mm deep without blade deflection.

---

## 11. Things explicitly left to the draftsman's / machinist's judgement

- Exact shank cross-section dimensions, provided the wall-thickness rules in §4.3 are met.
- Exact thumbwheel and depth-lock-knob diameters and knurl detail, provided they match the original's visual style.
- Internal radii and chamfers, provided no sharp internal corners are left in stressed areas.
- Whether the depth-lock bolt's tip is flat, cone, or cup point — designer's choice, provided it grips reliably and does not mark the shaft excessively over many cycles.
- Surface texture beyond §9.

---

## 12. Deliverables

1. Fully parametric 3D CAD model with the part tree using §2 names.
2. 2D drawings of each part with dimensions and tolerances suitable for CNC quotation.
3. Assembly drawing showing the three independent adjustments.
4. STEP and native CAD files.
5. Bill of materials.

---

*End of specification. Items marked `[TBM]` to be filled in after measurement of the original tool — see `measurement-checklist.md`.*
