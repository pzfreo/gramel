# CNC Quotation Request — Double-Blade Purfling Cutter

**Customer:** Paul Fremantle <paul@fremantle.org>
**Project:** One-off precision violin purfling cutter, brass body
**Date issued:** 2026-05-20
**Quantity:** 1 set (all parts)

---

## 1. Scope

CNC manufacture of the brass parts listed in §3, complete to the drawings supplied in §6. All steel fasteners (captive screw, mount screw, grub screw, push rod) are stock items — **not** in scope unless your shop also supplies them; please quote on the brass parts only.

The five brass parts assemble into a hand tool used by violin makers. See `GRM-00 ASSEMBLY` (exploded view + BOM) for the relationship between parts.

---

## 2. Materials

| Component | Material | Notes |
|---|---|---|
| All listed brass parts | **Free-machining brass, CZ121 / C36000 (or equivalent C26800 / CuZn37)** | Matches the original 19th-century tool. Substitution to a closely equivalent free-machining brass is acceptable — please flag the actual grade you'd use. |

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
| **Material removal** | All visible brass to be **draw-filed and polished to a satin / low-gloss finish**. **No lacquer.** Knurls remain as-knurled. |

---

## 5. Special manufacturing notes

- **Knurls.** Straight (axial) knurl, ~0.5 mm pitch, on:
  - Thumbwheel disc edge (GRM-03)
  - Depth-lock knob (GRM-05)

- **Drive plate (GRM-04) is small.** Plate is 8 × 17 × 3 mm with a small raised tenon on the back face. The tenon follows the egg perimeter of the plate (so it does not have protruding corners). 3:1 scale on the drawing.

- **Drive plate ↔ shaft anti-rotation.** Drive plate has a 1.5 × 3 × 8 mm rectangular tenon raised on its +X back face; the shaft has a matching slot cut across its −X end face (full diameter, one mill pass). The plate's tenon outline follows the plate's egg perimeter — verify on GRM-04 that the corners are clipped to match.

- **Depth-lock bolt thread tip (GRM-05).** Lead-in chamfer 0.5 mm at 45° to prevent cross-threading; small but important.

- **Captive-bearing relationship.** The captive screw (M2 × 6 stock screw, supplied by customer) bottoms on the M2 tap in the thumbwheel's −X face *before* its head clamps the drive plate, leaving 0.2 mm of axial bearing play. The geometry is built in — no adjustment needed at assembly — but please measure the M2 tap depth (2.8 mm nominal) carefully; this is the dial that sets the bearing play.

- **Shank relief slot (GRM-01).** Runs from the bottom of the shank up to the shaft cross-bore — does *not* continue above. The shank's working face is convex (R ≈ 8 mm, ~2 mm sagitta over the chord); the slot is cut into this convex face.

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

STEP files can be supplied for each part on request — please indicate if you'd find them useful for CAM setup.

---

## 7. Deliverables expected from the shop

1. Five brass parts to drawing, plus an in-process inspection certificate or a verbal note on any feature you needed to deviate on.
2. Hand-assembled trial fit: confirm shaft slides in the shank crossbore (item §4 critical fit), and confirm the drive plate tenon engages the shaft end-face slot without binding.
3. Parts shipped to: **address to be confirmed before despatch**.

---

## 8. Timing

This is a one-off personal project — no rush. Please quote on your standard lead time. Indicate if any feature (e.g., the small captive-bearing hole, the knurls, the small tenon clipped to the plate perimeter) drives a setup cost; we can iterate on the design to bring the price down before you cut metal.

---

## 9. Quote format requested

| Item | Unit cost | Total |
|---|---|---|
| GRM-01 Shank | | |
| GRM-02 Shaft | | |
| GRM-03 Thumbwheel + drive screw | | |
| GRM-04 Drive plate | | |
| GRM-05 Depth-lock bolt + knob | | |
| Setup / fixturing | | |
| Material | | |
| Finish (polish, deburr, etc.) | | |
| Shipping | | |
| **Total** | | |

Please flag any feature you'd want to discuss before committing.

---

## 10. Contact

**Paul Fremantle**
Email: paul@fremantle.org

For questions on the spec or to request STEP / source files, please reply to this email.

Source CAD model is parametric (Python / build123d) and lives at `https://github.com/pzfreo/gramel` — happy to share if useful.
