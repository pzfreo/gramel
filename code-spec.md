# Purfling Cutter — Code Implementation Spec

**Companion to:** `specification.md` (canonical CAD spec) and `measurement-checklist.md`.
**Status:** First-draft prototype build.
**Scope:** Captures the *code* and *CAD-as-code* approach to producing a 3D-printable prototype of the tool described in `specification.md`. The main spec stays neutral — usable by any human CAD designer. This document layers implementation decisions on top.

---

## 1. Relationship to other documents

- `specification.md` is the canonical, **neutral** CAD specification. A human draftsman with no Python could pick it up and produce the same drawings. It names no CAD package, no library, no programming language. Keep it that way.
- `measurement-checklist.md` is for the owner of the original tool, callipers in hand. Independent of any code.
- This document is the prototype-build companion: the language, library, structure, mate-class methodology, and 3D-print decisions that turn the canonical spec into runnable build123d code.

**Rule of thumb:** universal CAD intent → `specification.md`. "We are building this with build123d at 1.5× FDM print" → here.

---

## 2. Goals of this iteration

1. Fully parametric 3D model in build123d.
2. Print a working prototype at 1.5× scale. Slicer handles scaling; the CAD model is at real-world dimensions.
3. The prototype must demonstrate the **drive-screw / shank-tapped-bore mechanism** — i.e. the fine-feed edge-margin adjustment must actually work in plastic.
4. The model must hold up under the measurement pass. When `[TBM]` values become measured, swapping them in must not break geometry or constraints.
5. **Evaluate** the Layer-1/2/3 constraint-modeling methodology from `docs/constraint-modeling.md` (Spurfle repo) on a non-trivial assembly. Treat the methodology as something to test and refine, not as gospel.

---

## 3. Tooling

| Tool | Purpose |
|---|---|
| Python 3.11+ | Language |
| build123d | CAD kernel |
| build123d-mcp | Iterative dev loop (`execute`, `measure`, `render_view`, `export`, snapshots) |
| pydantic v2 | Parameter models, validators, JSON schema |
| bd_warehouse | Standard fasteners and threaded holes |

### 3.1 MCP sandbox configuration

The build123d MCP sandbox blocks third-party imports by default. Pydantic is enabled for this project via a project-level `.mcp.json` at the repo root that uses the server's `--allow-imports` flag:

```json
{
  "mcpServers": {
    "build123d-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": ["tool", "run", "--python", "3.12", "build123d-mcp", "--allow-imports", "pydantic"]
    }
  }
}
```

Project-scoped — it does not relax sandboxing for other projects on the machine. Pydantic v2's transitive deps (`pydantic_core`, `annotated_types`) load transparently; no further allowlisting needed. The parameter model can be imported directly into `execute()` calls.

For builds that hit the MCP's `execute()` timeout, the workflow-hints fallback remains available: write the build as a script, run via Bash, import the result as STEP.

---

## 4. Build flow — part-by-part

Order: **shank → blades + spacer → shaft → drive plate → thumbwheel + drive screw → small fasteners → assembly**.

Shank comes first because it is the geometric anchor: it hosts the two bores everything else hangs off, and its working face is the diagnostic feature of the tool.

Blades and spacer are sized just before the shaft, because the shaft's blade slot is a function of their thicknesses.

For each part:
1. Add the necessary fields to the parameter model.
2. Build the part via `execute()`.
3. Verify with `measure()` — topology, volume, bounding box.
4. Render with `render_view()`.
5. Snapshot before iterating.
6. Move on once the part stands on its own.

---

## 5. Parameter model

### 5.1 Structure

One pydantic `BaseModel` per spec tier (Tier 1–5), composed into a top-level `PurflingCutterParams` model. Sub-models accessed by attribute:

```
params.blade.thickness
params.shank.length
params.process.sliding_clearance
```

The top-level model owns:
- A `process: ProcessConfig` field carrying the prototype/production flag and shared fit clearances.
- Cross-tier `computed_field` properties for values derived across part boundaries (stack thickness, slot width, derived shaft OD, etc.).
- `model_validator`s implementing the spec's wall-thickness rules.

### 5.2 Field metadata pattern

Every numeric field uses pydantic `Field` with:
- `description` — purpose, in the same words the spec uses where possible.
- `json_schema_extra` with three keys:
  - `spec_ref` — back-pointer to specification.md, e.g. `"§4.1.1"`.
  - `status` — `"ESTIMATE"` | `"MEASURED"` | `"DERIVED"`.
  - `units` — typically `"mm"` or `"deg"`.

This makes the measurement pass mechanical: grep for `ESTIMATE`, swap in the measured value, retag to `MEASURED`.

### 5.3 Prototype vs production overrides

For values that diverge between FDM prototype and machined production, declare both and route through a `computed_field`:

```python
class ProcessConfig(BaseModel):
    prototype: bool = True
    fdm_sliding_clearance: float = 0.25
    cnc_sliding_clearance: float = 0.03

    @computed_field
    @property
    def sliding_clearance(self) -> float:
        return self.fdm_sliding_clearance if self.prototype else self.cnc_sliding_clearance
```

Geometry code **never** branches on the prototype flag directly. It always reads the resolved value (e.g. `params.process.sliding_clearance`).

### 5.4 Wall-thickness rules (Layer 3)

The spec lists wall-thickness rules in §4.2 (items 13, 14) and §4.3 (items 23, 24, 25). All are of the form *"≥ K × thread radius, ≥ N mm."* These become `model_validator`s on `PurflingCutterParams` and fail loudly if a chosen shank cross-section or shaft OD would violate them. The intent: invalid geometry is **unrepresentable**.

### 5.5 Documentation sync with specification.md

- **Forward (spec → code):** every `Field` carries `spec_ref`. Renaming a code field doesn't break the link.
- **Reverse (code → spec):** §4's "Symbol" column in `specification.md` is updated from `t_b` etc. to the code field path (`blade.thickness`). Two names for one thing is the drift we're eliminating.
- **Drift detection:** a one-shot script (`scripts/drift_check.py`) walks the model, collects `spec_ref`s, parses §4 tables, and reports orphans on either side. Manual, not CI. Run before each build session.

---

## 6. Mate classes (Layer 2)

To evaluate the constraint-modeling methodology, **all** mating relationships in the build are encoded as Python classes. Each class owns the shared parameters of an interface and emits the geometry / locations both halves need.

### 6.1 Initial mate inventory

| Mate class | Interface | What it generates |
|---|---|---|
| `SlidingFit` | Shaft ↔ shank cross-bore | Shaft OD, cross-bore ID (= OD + sliding_clearance), bore axis location |
| `ThreadedFit` | Drive screw ↔ shank tapped bore | Thread spec, screw major/minor, bore drill diameter, engagement length, induced wall-thickness rule |
| `CaptiveBearing` | Silver screw + drive plate + thumbwheel left face | Silver-screw length (= plate thickness + play + tap depth), clearance hole, tap depth, mounted axial gap |
| `BladeStackClamp` | Blade + spacer + blade ↔ blade slot + grub screw | Slot width (= 2·blade thickness + spacer + grub-screw advance + clearance), grub-screw nose-advance range |

`CaptiveBearing` is the highest-value mate — the deliberately-over-length silver screw and the resulting axial-play geometry is the signature feature of this tool. If any mate must be consistent-by-construction, it is this one.

### 6.2 Open methodology questions

- **Where do mate classes live?** Working hypothesis: `gramel/mates.py`, consuming the parameter model and emitting (a) updated locations to feed `Joint`s in the assembly step and (b) helper functions called by part-build code.
- **How much do mate classes own vs the part-build code?** Working hypothesis: a mate owns the *interface dimensions* only; part code consumes those and decides where to place them in part-local coordinates.
- **How do we test mate consistency?** Working hypothesis: pytest fixtures that instantiate a mate, generate both halves, assert clearance/interference is what the mate promised.

These are intentionally open. Part of the iteration's goal is to discover what the right answers are.

---

## 7. Threads and fasteners

### 7.1 Strategy at 1.5× FDM

Model dimensions are at real-world (small) scale; slicer scales 1.5× at print time. Consequence: scaled-up printed threads are not standard fastener sizes (e.g. an M3 model thread becomes a 4.5 mm major × 0.75 mm pitch printed thread). **Off-the-shelf metal screws will not fit any printed thread in the prototype.**

For the prototype this means:
- **Drive screw + shank tapped bore:** both are *printed* threads engaging each other. They self-mate (both scale together). **This is the mechanism we are testing.**
- **Silver screw, grub screw, drive-plate mount screws, depth-lock bolt:** also printed; cosmetic / static in the prototype. The over-length silver screw still demonstrates the captive-bearing geometry, but it does not need to thread under load.

If the prototype shows we need stronger small fasteners, the production path uses standard metal fasteners at the real-world thread sizes. Until then, accept printed-everywhere.

### 7.2 Thread modelling

Use `bd_warehouse` standard threaded geometry where available (`IsoThread`, `TapHole`, `ClearanceHole`). Never compute tap-drill diameters by hand.

For build performance, modelled threads may be approximated by helical sweeps at lower resolution during iteration, then upgraded to full `IsoThread` for the final STEP export. Decision is per-part.

---

## 8. Fillets and ergonomic finishing

The canonical spec does not specify fillets — it captures functional intent only. Fillets and chamfers are added here as a per-part finishing layer:

- Default external edge fillet: 0.5 mm (visible edges, hand-touched surfaces).
- Larger fillet at stress concentrators: 1–2 mm (e.g. where the relief slot terminates).
- No fillets on functional internal surfaces (slot bottoms, grub-screw seats, tapped-bore bottoms).

Fillet sizes live in a `FilletParams` block in the parameter model and are treated the same as any other parameter (status: typically `ESTIMATE`).

---

## 9. Assembly

### 9.1 Joint topology

Assembly uses build123d Joints. Rotations and translations expressed via joints, not raw `.move()`, so the parent can be repositioned later and children follow.

| Joint type | Used for |
|---|---|
| `CylindricalJoint` | Shaft in shank cross-bore (rotate + slide; rotation prevented downstream by drive-plate mount screws) |
| `CylindricalJoint` + thread coupling | Drive screw in shank tapped bore (translates as it rotates) |
| `RigidJoint` | Drive plate to shaft outboard end face; blades + spacer pinched in slot; silver screw bottomed in thumbwheel tap |
| `LinearJoint` with `limit=play` | Silver-screw head ↔ drive plate face (the captive-bearing degree of freedom) |

### 9.2 Verification

After assembly:
- `clearance()` between all sliding-fit pairs returns within expected range.
- `interference()` returns no volume.
- Kinematic sweep across edge-margin range — assert no collision.
- Fixed-camera renders matching the diagram for visual regression later.

---

## 10. Proposed repo layout

```
gramel/
├── specification.md           — canonical CAD spec (unchanged)
├── measurement-checklist.md   — owner-side measurement plan (unchanged)
├── code-spec.md               — this document
├── diagram.png / diagram.svg  — naming and axes (unchanged)
├── pyproject.toml             — pydantic, build123d, bd_warehouse
└── gramel/
    ├── __init__.py
    ├── parameters.py          — pydantic param model + validators
    ├── mates.py               — mate classes
    ├── fits.py                — ISO fit tables (if used)
    ├── parts/
    │   ├── shank.py
    │   ├── shaft.py
    │   ├── blades.py
    │   ├── spacer.py
    │   ├── drive_plate.py
    │   ├── thumbwheel.py
    │   ├── fasteners.py
    │   └── depth_lock.py
    ├── assembly.py
    └── scripts/
        ├── drift_check.py     — spec_ref ↔ §4 audit
        ├── build_all.py       — exports STEPs of every part
        └── render_doc.py      — renders for embedding in docs
```

Subject to revision once we hit the first part that doesn't fit.

---

## 11. Decision log

In conversation order. The *why* matters more than the *what*.

1. **3D print at 1.5×, slicer-side scaling.** Model at real-world dimensions; the printer scales. Trade-off accepted: printed threads are not standard fasteners.
2. **Pydantic over stdlib dataclass.** Field metadata and validators are first-class. Worth the dependency for a constraint-heavy model.
3. **All mates as Layer-2 classes** (not just the captive bearing). Goal: evaluate and improve the methodology on a real assembly, not just the obvious-win case.
4. **Shank first, not shaft.** Shank is the geometric anchor; everything hangs off it.
5. **Field metadata pattern: description + spec_ref + status + units.** No automation upfront; one-shot drift script if needed.
6. **Update §4 of `specification.md`** to replace the symbol column with code field names, eliminating dual-naming.

---

## 12. Open implementation issues

- **Print orientation of the shank.** Tapped bore and cross-bore are horizontal in use. Printing with shank standing vertically puts thread axes horizontal in print orientation — layer lines run along threads (weak). May need to print on its side, or split the shank.
- **Thread resolution.** Real `IsoThread` geometry is expensive in build123d. Whether to use full threads or helical-sweep approximations during iteration is a per-part call.
- **Working-face geometry order.** Apply convexity radius first then subtract the relief slot, or build the relief slot and chamfer the remainder? Affects production machinability; probably indistinguishable in print.
- **ESTIMATE warnings.** Should using an `ESTIMATE` field trigger a runtime warning? Current plan: status tag only. Tempting to escalate to warnings once we have a measured baseline.

---

*End of code spec. The canonical CAD spec remains the single source of design intent. This document is the prototype-build companion and may be revised freely as the build progresses.*
