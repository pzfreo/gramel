# gramel

Parametric CAD model of a double-blade violin purfling cutter, written in
[build123d](https://github.com/gumyr/build123d) with all dimensions driven
from a single pydantic parameter tree.

Reverse-engineered from a physical original; intended outputs are:

1. An **FDM prototype STEP** with real helical threads, sliced and printed
   at 1.5× to verify the mechanism.
2. A **CNC handoff package** (per-part STEPs + A4 PDF drawings) using
   simplified-thread representation per ISO 6410.

## Quickstart

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
# Install (creates .venv, syncs pinned deps)
uv sync

# Build the full assembly and export STEP
uv run python -m gramel.assembly
# → /tmp/assembly.step (volume ≈ 14 800 mm³)

# Build a single part
uv run python -m gramel.parts.shank
# → /tmp/shank.step

# Render the shank's CNC drawing (A4 landscape PDF + SVG)
uv run python -m gramel.parts.shank_drawing
# → /tmp/shank_drawing.pdf

# Lint, type-check, test
uv run ruff check gramel/
uv run mypy gramel/
uv run pytest
```

The full assembly with `process.prototype=True` (real threads) takes
~2 min to build; per-part exports finish in seconds.

## What gets built

Modules under `gramel/parts/`, each with its own `main()` that exports a
STEP file:

| Module | Part | Role |
|---|---|---|
| `shank.py` | Brass shank | Square body that registers against the violin edge |
| `shaft.py` | Brass shaft | Slides through the shank crossbore, carries the blades |
| `blade.py`, `channel_spacer.py`, `blade_retainer.py` | Blade stack | Two single-bevel blades, optional channel-width shim, four bone-shaped copper retainers |
| `grub_screw.py` | M4 × 10 | Clamps the blade stack against the shaft slot |
| `drive_plate.py` | Brass | Egg-shaped plate linking shaft to drive screw |
| `thumbwheel_drive_screw.py` | Brass (integral) | Knurled thumbwheel + M3 × 0.5 drive screw |
| `captive_screw.py` | M2 captive screw | Captures the drive plate against the thumbwheel boss |
| `depth_lock_bolt.py` | M6 knurled bolt | Clamps the shaft via a push rod |
| `push_rod.py` | Steel rod | Translates the M6 bolt's advance to the shaft underside |
| `shank_drawing.py` | — | A4 landscape technical drawing of the shank (PDF + SVG) |

All cross-part dimensions live in `gramel/parameters.py` as a single
`PurflingCutterParams` pydantic model. Cross-part derivations (crossbore
diameter from shaft OD + sliding clearance, etc.) are exposed as
`computed_field`s; wall-thickness rules are enforced with model
validators.

## Prototype vs production mode

`process.prototype` (default `True`) switches between two manufacturing
profiles:

| | `prototype=True` (FDM) | `prototype=False` (CNC) |
|---|---|---|
| Sliding clearance | 0.25 mm (`fdm_sliding_clearance`) | 0.03 mm (`cnc_sliding_clearance`, H7/g6) |
| Threaded features | Real ISO helices via `bd_warehouse.IsoThread` | Clean reference cylinders at major / tap-drill diameter |
| Intended output | Print at 1.5× on FDM, threads engage as printed plastic | Send STEP + PDF drawing to a brass shop |

The thread split is deliberate: real-thread geometry helps the FDM print
mechanism engage and actively *hurts* the CNC handoff (the shop reads
the thread spec off the drawing per ISO 6410, not the helical geometry —
modelled threads bloat the STEP and confuse some CAM packages).

## Layout

```
gramel/
  parameters.py        single source of truth for all dimensions
  assembly.py          composes parts into a single STEP
  parts/
    *.py               one part per file, each with build_<part>() + main()
    _threads.py        ISO helix helpers (FDM path only)
    shank_drawing.py   A4 CNC drawing (more parts in progress)
specification.md       canonical CAD spec — intent + measured dimensions
code-spec.md           implementation companion — layering, mate classes, conventions
CLAUDE.md              project notes for LLM-assisted work
```

The relationship between `specification.md` and the code is one-to-one:
every numeric field in `parameters.py` carries a `spec_ref` pointing back
to a §-numbered entry in the spec.
