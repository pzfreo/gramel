# Gramil — project-specific notes for Claude

Lessons learned during work on this repo. Read before doing anything similar.

## Drawings (CNC handoff package)

We're producing one A4 landscape technical drawing per part: shank, shaft,
drive plate, thumbwheel + drive screw, depth-lock bolt + knob. `shank_drawing.py`
is the template — copy its structure for the rest.

### Drawing geometry is built with `process.prototype=False`

The CNC drawing must show **clean reference cylinders + thread callouts**, not
real helical thread geometry. ISO 6410 simplified representation is what the
shop reads. Always force prototype=False at the top of the drawing builder:

```python
params = params.model_copy(update={"process": params.process.model_copy(update={"prototype": False})})
```

Real threads are reserved for the FDM print STEP export. Don't confuse the
two contexts.

### Build123d `ExtensionLine.offset` sign convention

**Use the `_dim_outside(p1, p2, side, distance, …)` helper instead of raw
`_ext(...)`.** It takes a directional side ("left", "right", "above",
"below") and computes the offset sign for you. No more manual sign-juggling.

For reference (verified empirically with rendered output) the underlying
convention is:

| Border direction (p1 → p2) | offset sign | Dim lands on… |
|---|---|---|
| UP (bottom→top) | + | page-RIGHT of border |
| UP | − | page-LEFT |
| DOWN (top→bottom) | + | page-LEFT |
| DOWN | − | page-RIGHT |
| RIGHT (left→right) | + | page-BELOW |
| RIGHT | − | page-ABOVE |
| LEFT (right→left) | + | page-ABOVE |
| LEFT | − | page-BELOW |

**The rule: positive offset is always on the RIGHT side of path direction**
(right-hand rule with +Z out of page). Sign maps to page directions
differently depending on whether the border goes up/down or left/right —
which is why `_dim_outside` exists.

If a dim ends up *inside* the part outline, you used `_ext` directly with
the wrong sign. Switch to `_dim_outside` with the correct `side`.

### Text and SVG layers

Build123d's `Text` returns Faces (filled glyphs). Three rules:

1. **Text on a layer with no `fill_color` renders as thick outlined characters
   and is illegible at small sizes.** Always route text to a layer that has
   `fill_color=part_color, line_weight=0.05`.

2. **Title block, notes block, and leader callout labels are all "text"** —
   they must go on the same fill-black layer.

3. **Leader callouts** mix lines (need stroke rendering) and label text (need
   fill rendering). Return them as a tuple `(lines_compound, text_compound)`
   from the leader helper so the caller can route each to the correct layer.

4. **Leader lines must NOT strike through their label text.** The `_leader()`
   helper handles this by left-aligning (or right-aligning) the label at the
   line endpoint with a 1 mm gap, so the leader stops cleanly before the
   first character. Don't centre-align leader labels — that puts the line
   through the middle of the text.

### Don't use `build123d.TechnicalDrawing` for the frame

It draws a 6×4 grid of letters/numbers around the frame and a half-page-sized
title block in the bottom-right quadrant — both unconventional for a single
A4 drawing. Use the custom `_page_frame()` + `_title_block_lines/text()` +
`_notes_block_lines/text()` helpers in `shank_drawing.py` instead.

Standard ISO 5457 A4 layout we adopted:

- Page: 297 × 210 mm, origin at centre.
- Frame: 277 × 190 mm at ±10 mm margin → X ∈ [-138.5, 138.5], Y ∈ [-95, 95].
- 4 centering tick marks at the midpoints of each side, **no grid letters**.
- Title block: 100 × 50 mm bottom-right corner → X ∈ [38.5, 138.5], Y ∈ [-95, -45].
- Notes block: 100 × 50 mm above title block → X ∈ [38.5, 138.5], Y ∈ [-48, 2].
- Views go in the left half: X ∈ [-138.5, 38.5].

### View projection → page-axis mapping (gotcha)

For each view, work out which **world axis** maps to page-horizontal and
which to page-vertical, then size the view box and dim lines from those
extents. **This is the single most error-prone step.**

| View | Camera (origin) | Up | Page +X = | Page +Y = | Horizontal extent | Vertical extent |
|---|---|---|---|---|---|---|
| Working-face | (+∞, 0, L/2) | +Z | -world Y | +world Z | shank.depth (11) | shank.length (80) |
| Side | (0, +∞, L/2) | +Z | +world X | +world Z | shank.width (13.55) | shank.length (80) |
| Bottom | (0, 0, -∞) | +Y | -world X | +world Y | shank.width (13.55) | shank.depth (11) |
| Iso | (+∞, +∞, +∞) | +Z | iso projection | iso projection | ~25 (diag) | ~85 (incl. height) |

The bottom view caught us out: world X (= shank.width = 13.55) is the
HORIZONTAL extent, world Y (= shank.depth = 11) is VERTICAL. If you
write `b_left = bx - depth/2` instead of `bx - width/2`, the dim lines
will measure the wrong distance and the labels will look misplaced.

**Check every dim's label value matches its actual extent**. The user
caught a swapped-axis error on the bottom view — it's the kind of mistake
that should never reach the shop.

### Inline dim labels must fit the dim line's path length

Build123d's `DimensionLine` crashes with `ValueError: Can't get geom
adaptor of empty wire` when the label text is wider than the dim path AND
the path is too short to host even the "label outside arrows" fallback.

**Rule of thumb**: keep inline dim labels to **just the numeric value**.
Put thread specs (`M3 × 0.5`), fit classes (`H7`), surface-finish marks
(`Ra 1.6`) on **leader callouts** instead of in the dim label.

### Iso view: 1:1, same scale as the orthographics

Mixing scales on one drawing without an explicit scale callout in the title
block is wrong by drafting convention. Either render the iso at the same
scale as the rest, or drop it. **Don't** silently shrink it to 0.5×.

The iso view of the shank at 1:1 fits in a ~25 × 85 mm bounding box on
the page, which slots comfortably into the upper-centre between the side
view and the title/notes column.

### PDF is the deliverable

`uv run python -m gramil.parts.<part>_drawing` exports SVG **and** PDF
(via `cairosvg.svg2pdf`). The PDF is what the shop sees. The SVG is kept
as a vector intermediate for further editing if needed.

Don't skip the PDF step.

## Trusting the user (rules learned the hard way)

These exist because of failure patterns observed during the print-in-place
hinge work: arguing with the user's empirical evidence, doubling down on
wrong analyses after being told so, and re-running analyses to verify
what the user had just told me. Read before doing any 3D / geometry /
physical-artifact work in this repo.

1. **Empirical evidence outranks my analysis. Always.** If the user says
   "I've printed this and it works", that is ground truth. If my analysis
   disagrees, the analysis is wrong — not the reality. Stop the analysis,
   trust the report.

2. **One "you're wrong" from the user = mandatory stop and recalibrate.**
   Not "let me check one more thing." Stop, ask what they want me to do,
   do it. No contrarian follow-ups. No more "but the data shows…".

3. **Do not run an analysis to verify what the user has just told me.**
   If they say the orientation is X, the orientation is X. Building a
   z-distribution to "check" is disrespectful and usually produces a
   wrong answer that I then defend.

4. **For 3D / spatial geometry, my intuition is often wrong.** Defer to
   the user's spatial judgment. They can see the object; I'm reasoning
   from bounding boxes and triangle centroids.

5. **For physical artifacts, ask before building.** Two questions on hour
   1 will save hours of wasted modelling:
   - "Does the reference part work as-is, or does it need a separate
     metal part (pin, magnet, fastener)?"
   - "In print/use orientation, what's on top — feature A or feature B?"

6. **Sanity-check the output artifact before declaring done.** Two STL
   files shipped for a print-in-place hinge should have failed an
   obvious "would a slicer treat this correctly?" check before I
   declared the task complete. Look at what you're handing over.

7. **Stretch goal + pragmatic fallback: timebox the stretch and offer
   the fallback explicitly.** When a goal is "build a reusable parametric
   X" but a working reference Y exists, the stretch attempt is worth
   making — that's research, not waste. But after ~3 iterations without
   convergence, surface the situation to the user: "Parametric attempt
   isn't converging; the reference is right there and would unblock the
   downstream work. Want me to ship the reference now and keep the
   parametric attempt as a separate open thread, or keep iterating?"
   Don't silently keep iterating, and don't silently drop the stretch
   goal.

## Open research: reusable parametric print-in-place hinge

The user's longer-term goal is a **reusable parametric print-in-place
hinge** that could be dropped into multiple future projects. The
attempts so far (in commits before the case-design PR; the modules
themselves were dropped from main) didn't converge — central knuckle
floated free, geometry didn't survive rotation, Hausdorff distance
plateaued around 17–28%. This is an open thread, not a closed one.
If revisiting:

- Don't try to replicate the OralB hinge geometry — its print-in-place
  behaviour is not yet understood by me. Start from first principles of
  what makes a PIP hinge work (knuckle clearance, pin geometry,
  supportless overhangs).
- The user has printed the OralB hinge multiple times and it works as
  PIP. That is the ground truth to design *toward*, not to argue with.
- Validate by actually printing, not by Hausdorff distance to the
  reference mesh.

## Workflow rules (also in global CLAUDE.md, repeated here)

- Branch per change. Never commit to main, never auto-merge.
- Test STEP exports and drawing renders before declaring a part "done".
- When the user shows a photo of a layout issue, **identify the specific
  feature** (which view, which dim, which axis) before changing anything.
  Drawing layouts go wrong subtly and randomly tweaking offsets without
  a hypothesis just churns.

## Memory checklist before starting a new drawing

When porting the shank template to shaft / drive plate / thumbwheel /
depth-lock bolt:

1. ☐ Force `process.prototype=False`.
2. ☐ Work out the view→page axis mapping for **each** view and document
   it as a comment block above the dim section.
3. ☐ Pick offset signs per the table above; render and verify each
   dim is outside the view before adding the next.
4. ☐ Dim labels = numeric values only. Thread/fit specs on leaders.
5. ☐ Every leader returns `(lines, text)` — route to part-layer and
   text-layer respectively.
6. ☐ Notes-block content per part (material, thread classes, surface
   finishes) updated to match the part.
7. ☐ Title block: GRM-01 (shank), GRM-02 (shaft), GRM-03 (drive plate),
   GRM-04 (thumbwheel), GRM-05 (depth-lock bolt).
8. ☐ Render PDF, eyeball it end-to-end, only then declare ready for review.
