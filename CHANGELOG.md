# Changelog

All notable changes to this project are documented here.
This file is auto-updated by the release workflow on every tagged release.

---

## v0.1.9 (2026-05-27)

## What's Changed
* fix: use @BBL X1C filament profile instead of @base by @pzfreo in https://github.com/pzfreo/gramel/pull/64


**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.8...v0.1.9

---

---

## v0.1.8 (2026-05-27)

## What's Changed
* Engrave Chelli Strings logo on the lid top by @pzfreo in https://github.com/pzfreo/gramel/pull/56
* Update pip-hinge variant to new upstream API + Knuckle.SMALL by @pzfreo in https://github.com/pzfreo/gramel/pull/55
* pip-hinge: pivot_z_offset as a first-class HingeParams param by @pzfreo in https://github.com/pzfreo/gramel/pull/57
* README: credit original design by Brian Hart and Shem Mackey by @pzfreo in https://github.com/pzfreo/gramel/pull/58
* Add estampo.toml for reproducible P1S print pipeline by @pzfreo in https://github.com/pzfreo/gramel/pull/59
* slice.yml: run full pipeline including pack stage in CI by @pzfreo in https://github.com/pzfreo/gramel/pull/60
* release: attach sliced case gcode.3mf to every release by @pzfreo in https://github.com/pzfreo/gramel/pull/61
* Add CHANGELOG.md + auto-update on every release by @pzfreo in https://github.com/pzfreo/gramel/pull/62
* CLAUDE.md: rules for trusting the user's empirical evidence by @pzfreo in https://github.com/pzfreo/gramel/pull/49
* release: fix CHANGELOG push — checkout main before pushing by @pzfreo in https://github.com/pzfreo/gramel/pull/63


**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.7...v0.1.8

---

---

## v0.1.7 (2026-05-25)

## What's Changed
* Prevent stale dim labels: dim_label helper + regression test by @pzfreo in https://github.com/pzfreo/gramel/pull/54

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.6...v0.1.7

---

## v0.1.6 (2026-05-25)

## What's Changed
* Bone retainer: tighter waist (4.5→4.3) + shoulder fillets by @pzfreo in https://github.com/pzfreo/gramel/pull/52
* Promote blade + retainer from optional to main parts by @pzfreo in https://github.com/pzfreo/gramel/pull/53

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.5...v0.1.6

---

## v0.1.5 (2026-05-25)

## What's Changed
* Print-in-place clamshell case with reference-STL hinges by @pzfreo in https://github.com/pzfreo/gramel/pull/46
* Add printable case STLs (lid + base, print-flat) by @pzfreo in https://github.com/pzfreo/gramel/pull/47
* Replace split STLs with single combined print-in-place STL by @pzfreo in https://github.com/pzfreo/gramel/pull/48
* Hinge: drop reference hinge by 2 mm instead of 3.5 mm by @pzfreo in https://github.com/pzfreo/gramel/pull/50
* Add pip-hinge variant of print-in-place case by @pzfreo in https://github.com/pzfreo/gramel/pull/51

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.4...v0.1.5

---

## v0.1.4 (2026-05-22)

## What's Changed
* Sync to measured tool: shaft 35, drive screw 18, slot 6.4×4.75, bone retainer w/ fillet by @pzfreo in https://github.com/pzfreo/gramel/pull/44
* Add Prusa Open Community License (OCL v1) + README notice by @pzfreo in https://github.com/pzfreo/gramel/pull/45

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.3...v0.1.4

---

## v0.1.3 (2026-05-21)

## What's Changed
* Fix CI: declare markdown-pdf + add interference tests by @pzfreo in https://github.com/pzfreo/gramel/pull/43

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.2...v0.1.3

---

## v0.1.1 (2026-05-21)

## What's Changed
* RFQ tighten per shop review by @pzfreo in https://github.com/pzfreo/gramel/pull/40
* Drive screw 18→28 mm; shank fillet that actually applies by @pzfreo in https://github.com/pzfreo/gramel/pull/41

**Full Changelog**: https://github.com/pzfreo/gramel/compare/v0.1.0...v0.1.1

---

## v0.1.0 (2026-05-20)

## What's Changed
* Bootstrap parametric shank model with build123d pipeline by @pzfreo in https://github.com/pzfreo/gramel/pull/1
* Capture measurements of the original shank + spec corrections by @pzfreo in https://github.com/pzfreo/gramel/pull/2
* Measure blades and bone-shaped retainers; correct slot axes by @pzfreo in https://github.com/pzfreo/gramel/pull/3
* Reorient axes: Z = shank long (vertical), X = shaft, Y = third by @pzfreo in https://github.com/pzfreo/gramel/pull/4
* Clarify blade axis orientation in docstrings by @pzfreo in https://github.com/pzfreo/gramel/pull/5
* First-pass shaft build by @pzfreo in https://github.com/pzfreo/gramel/pull/6
* Measure drive train and captive bearing by @pzfreo in https://github.com/pzfreo/gramel/pull/7
* First-pass thumbwheel + drive screw (integral) by @pzfreo in https://github.com/pzfreo/gramel/pull/8
* Build remaining parts and assemble the full cutter by @pzfreo in https://github.com/pzfreo/gramel/pull/9
* Real ISO threads on FDM prototype path by @pzfreo in https://github.com/pzfreo/gramel/pull/11
* Ignore .claude/ harness state directory by @pzfreo in https://github.com/pzfreo/gramel/pull/12
* Fix blade stack model: spacer absent by default, slot_spare replaces grub_advance_remaining by @pzfreo in https://github.com/pzfreo/gramel/pull/13
* Rebuild shank drawing as ISO CNC-handoff package by @pzfreo in https://github.com/pzfreo/gramel/pull/14
* Make README.md useful (closes #15) by @pzfreo in https://github.com/pzfreo/gramel/pull/21
* Extract thread tables into gramel/threads.py API (closes #18) by @pzfreo in https://github.com/pzfreo/gramel/pull/22
* Add geometry tests (closes #17) by @pzfreo in https://github.com/pzfreo/gramel/pull/24
* Clean up shank_drawing.py lint by @pzfreo in https://github.com/pzfreo/gramel/pull/25
* Cutting pair: nominal diameter + ISO 286 fit classes by @pzfreo in https://github.com/pzfreo/gramel/pull/26
* Spec silver screw as M2 × 6 stock; tap depth derives by @pzfreo in https://github.com/pzfreo/gramel/pull/27
* Refactor shank_drawing.py to use build123d_drafting helpers by @pzfreo in https://github.com/pzfreo/gramel/pull/28
* Drop leader workaround (build123d-drafting-helpers 0.1.2) by @pzfreo in https://github.com/pzfreo/gramel/pull/29
* Shank drawing: fix slot width placement + add slot depth callout by @pzfreo in https://github.com/pzfreo/gramel/pull/30
* Add shaft drawing (GRM-02) by @pzfreo in https://github.com/pzfreo/gramel/pull/31
* Extract shared drawing infrastructure into gramel/parts/_drawing.py by @pzfreo in https://github.com/pzfreo/gramel/pull/32
* Add thumbwheel drawing (GRM-03); rename silver_screw → captive_screw by @pzfreo in https://github.com/pzfreo/gramel/pull/33
* Bump shaft tenon to 1.5 × 3.0 mm by @pzfreo in https://github.com/pzfreo/gramel/pull/34
* Add depth-lock bolt collar + tip chamfer (with matching shank bore) by @pzfreo in https://github.com/pzfreo/gramel/pull/35
* Drive plate drawing (GRM-04) + swap tenon onto plate by @pzfreo in https://github.com/pzfreo/gramel/pull/36
* Depth-lock bolt drawing (GRM-05); push rod ⌀5 → ⌀4.5 by @pzfreo in https://github.com/pzfreo/gramel/pull/37
* Sync specification.md with current model by @pzfreo in https://github.com/pzfreo/gramel/pull/38
* Assembly drawing (GRM-00) with exploded view + BOM by @pzfreo in https://github.com/pzfreo/gramel/pull/39

## New Contributors
* @pzfreo made their first contribution in https://github.com/pzfreo/gramel/pull/1

**Full Changelog**: https://github.com/pzfreo/gramel/commits/v0.1.0
