# RFQ — Double-Blade Purfling Cutter

**Customer:** Paul Fremantle <paul@fremantle.org>
**Project:** Precision violin purfling cutter, brass body
**Date issued:** 2026-05-20
**Quantities requested:** 1, 20, and 50 sets (please quote each tier)

> **Summary.** Small precision brass hand tool for violin making — six components per set, moderate tolerances, cosmetic finishing.

---

## 1. Scope

CNC manufacture of the five brass parts in §3 plus one steel push rod (cut to length, no other machining). Threaded fasteners (captive screw, mount screw, grub screw) are standard stock items and **not** in scope.

The brass parts assemble into a hand tool used by violin makers. See `GRM-00 ASSEMBLY` (exploded view + BOM) for the relationship between parts.

Please quote at three quantities: **1, 20, and 50 sets** (a "set" = one of each of the five brass parts plus one push rod). The 50-set quote should reflect setup amortisation if applicable.

---

## 2. Materials

| Component | Material | Notes |
|---|---|---|
| Brass parts (GRM-01 through GRM-05) | **Free-machining brass such as CZ121 (C36000) or equivalent** | Matches the original 20th-century tool. Please flag the actual grade you'd use. |
| Push rod | **Bright drawn mild steel, ⌀4.5 mm round bar** | Cut to 45 mm; ends square and deburred. No further machining. |

Surface finish notes per drawing; see §4 below.

---

## 3. Parts list

| # | Part | Drawing | Qty | Key features |
|---|---|---|---|---|
| 1 | Shank | GRM-01 | 1 | Square brass body 13.55 × 11 × 80 mm with cross-bore, tapped bore, depth-lock blind bore (three sections: collar bore ⌀6.35, M6 tap, ⌀5 push-rod bore), relief slot on working face, top dome, edge fillets |
| 2 | Shaft | GRM-02 | 1 | ⌀8 g6 × 45 mm with axial blade slot, end-face slot (anti-rotation), M2 mount tap, M4 grub-screw tap, flat machined along underside |
| 3 | Thumbwheel + drive screw (integral) | GRM-03 | 1 | Turned from one piece. Knurled disc ⌀10 + ⌀5 collar + M3 × 0.5 thread. ⌀6 silver-screw boss + M2 tap on the −X face. |
| 4 | Drive plate | GRM-04 | 1 | Egg-shape (⌀8 big boss + ⌀6 small boss, 9.5 mm centres). 3 mm thick + 1.5 mm anti-rotation tenon on back face. Two through-holes (⌀2.4 mount + ⌀2.6 captive bearing). |
| 5 | Depth-lock bolt + knurled knob | GRM-05 | 1 | Knurled knob ⌀10 × 14 mm + ⌀6.25 collar × 5 mm + M6 × 1 thread × 13 mm + 0.5 × 45° lead-in chamfer |
| 6 | Push rod | (no drawing — see §2) | 1 | ⌀4.5 mm bright drawn mild steel rod, **cut to 45 mm**. Both ends square and deburred. ±0.2 mm length tolerance. |

---

## 4. Tolerances, fits and finishes

| Item | Spec | Reference |
|---|---|---|
| **General tolerance** | ISO 2768-mK | All untoleranced dims |
| **Critical fit: shaft ↔ shank crossbore** | H7 / g6 nominal ⌀8 (≈ 0.02–0.04 mm clearance) | GRM-01 + GRM-02 |
| **Captive-bearing hole** | ⌀2.6, deliberately sloppy (~0.3 mm radial clearance on M2) | GRM-04 |
| **Depth-lock collar bore** | ⌀6.35 H8 over the ⌀6.25 collar (sliding fit) | GRM-01 + GRM-05 |
| **Push-rod bore** | ⌀5 over a ⌀4.5 stock rod (sliding fit) | GRM-01 |
| **Drive-plate captive hole** | ⌀2.6 deliberately sloppy (~0.3 mm radial clearance on M2) | GRM-04 |
| **Threads** | ISO metric class 6H / 6g, ISO 6410 simplified representation on drawings | All threaded features |
| **Surface finish — general** | Ra 3.2 | Default |
| **Surface finish — mating sliding surfaces** | Ra 1.6 | Shaft OD, drive-screw thread, push-rod bore — noted on drawings |
| **Edges** | Break all sharp edges 0.3 max; shank has 0.5 mm ergonomic fillet | GRM-01 |
| **Visible brass finish** | Deburred with an attractive satin finish suitable for a hand tool. **No lacquer.** Knurls remain as-knurled. (Hand-polish only if it doesn't drive cost disproportionately at higher quantities — please flag.) |

---

## 5. Special manufacturing notes

- **Knurls.** Straight (axial) knurl, ~0.5 mm pitch — thumbwheel disc edge (GRM-03) and depth-lock knob (GRM-05).
- **GRM-03 M2 tap depth = 2.8 mm.** This is a captive-bearing critical dim; please hold ±0.1 mm. Drill 3.8 mm (chip-relief well below the tap).
- **GRM-03 thread tip chamfer.** 0.5 × 45° lead-in on the M6 thread.
- **GRM-04 drive plate** is 8 × 17 × 3 mm; the back-face tenon is profile-clipped to the egg outline, which falls out naturally if you mill the back-face relief first and profile the egg outline second.
- **GRM-01 relief slot** stops at the cross-bore; does not continue above. Flat-floored (not following the convex face).

---

## 6. Drawings (included with this quotation request)

| File | Drawing | Description |
|---|---|---|
| `GRM-00_assembly_drawing.pdf` | GRM-00 | Assembly view + exploded view + Bill of Materials |
| `GRM-01_shank_drawing.pdf` | GRM-01 | Shank |
| `GRM-02_shaft_drawing.pdf` | GRM-02 | Shaft |
| `GRM-03_thumbwheel_drive_screw_drawing.pdf` | GRM-03 | Thumbwheel + drive screw (integral turned piece) |
| `GRM-04_drive_plate_drawing.pdf` | GRM-04 | Drive plate |
| `GRM-05_depth_lock_bolt_drawing.pdf` | GRM-05 | Depth-lock bolt + knurled knob |

**STEP files supplied:** `GRM-01_shank.step`, `GRM-02_shaft.step`, `GRM-03_thumbwheel_drive_screw.step`, `GRM-04_drive_plate.step`, `GRM-05_depth_lock_bolt.step` — CNC-clean (no helical thread geometry; threads per the drawing callouts).

---

## 7. Deliverables expected from the shop

1. Five brass parts to drawing, plus a brief note identifying any deviations from the drawings.
2. Hand-assembled trial fit: confirm shaft slides in the shank crossbore (item §4 critical fit), and confirm the drive plate tenon engages the shaft end-face slot without binding.
3. Parts shipped to: **address to be confirmed before despatch**.

---

## 8. Timing

Please quote on your standard lead time at each quantity tier. Indicate if any feature (e.g., the small captive-bearing hole, the knurls, the small tenon clipped to the plate perimeter) drives a disproportionate setup cost; we can iterate on the design to bring the price down before you cut metal.

---

## 9. Quote format requested

Per-set unit cost at each tier (i.e. fully-amortised cost per set, all five brass parts). Setup, material, finish, and shipping can be itemised separately or rolled into the per-set price — whichever your accounting prefers.

| Item | 1 set | 20 sets (per set) | 50 sets (per set) |
|---|---|---|---|
| GRM-01 Shank | | | |
| GRM-02 Shaft | | | |
| GRM-03 Thumbwheel + drive screw | | | |
| GRM-04 Drive plate | | | |
| GRM-05 Depth-lock bolt + knob | | | |
| Push rod (⌀4.5 × 45 steel) | | | |
| Setup / fixturing (allocated) | | | |
| Material | | | |
| Finish (polish, deburr, etc.) | | | |
| **Per-set total** | | | |
| Shipping (total order) | | | |
| **Order total** | | | |

Please flag any feature you'd want to discuss before committing. If the 20-set or 50-set quote drops setup cost dramatically, please note that — useful for planning.

---

## 10. Contact

**Paul Fremantle**
Email: paul@fremantle.org

For questions on the spec or to request STEP / source files, please reply to this email.

Source CAD model is parametric (Python / build123d) and lives at `https://github.com/pzfreo/gramel` — happy to share if useful.
