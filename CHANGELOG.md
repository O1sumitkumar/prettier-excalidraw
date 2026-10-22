# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `build.py` refuses an empty icon or image file, or one whose bytes do not match
  its `.svg`, `.png` or `.jpg` extension, and names the file and the box (#1).

### Planned
See [ROADMAP.md](ROADMAP.md).

## [0.2.0] - 2026-10-22

### Added
- `build.py`: `subtitle` on regions (note in the corner opposite the title);
  warning when an icon has to shrink below 65 % of its box height.
- `fix.py`: prints `check label:` for any text whose size changed by 4 px or more.
- `SKILL.md`: gap-filling step - ask about store owners, edge direction,
  boundaries and callbacks before drawing, or state the assumption.
- `lint.py`: `misleading-proximity` - a store sitting under a box it has no
  arrow to; `arrow-through-text`, `arrow-through-box`, `arrow-overlap`,
  `text-overlap`, `text-over-box` - layout collisions the eye catches but the
  old rules did not.
- `build.py`: `bend` on arrows to choose where the middle segment runs, so two
  arrows between the same rows do not share a line.
- `preview.py`: `--square` for quick-look thumbnails; exact text widths.

### Changed
- `fix.py` re-measures text boxes and re-centres bound labels after a font or
  size change, so Excalidraw no longer shows stale, off-centre labels.
- `build.py` widens boxes to the next multiple of 20 px instead of an arbitrary
  width; same-side arrows (bottom→bottom, right→right) loop out 40 px instead of
  running along the box edges.
- `fix.py` keeps the left edge of a caption whose size changes drastically, so
  it stays beside the icon it belonged to.
- `build.py` rounds heightened boxes to the 20 px grid; `preview.py` prints
  usage instead of a traceback.
- Chrome recipe listed first for PNG previews, with the device scale factor.
- Example specs widened so every icon stays at full size; arrows re-routed so
  none crosses a region title.

## [0.1.0] - 2026-10-22

### Added
- `SKILL.md` with generate / restyle / check workflows and the reasoning behind
  each style rule, including a gap-filling step for under-specified prompts.
- `scripts/build.py`: JSON spec to `.excalidraw`, handling bound labels, elbowed
  bound arrows, embedded icons, same-side arrow loops and z-order.
- `scripts/lint.py`: 14 style rules including hidden arrows, child-before-parent
  z-order, icon sizing and misleading store placement.
- `scripts/fix.py`: mechanical fixes for font, size, roughness, fills, corners,
  arrowheads and z-order without moving anything.
- `scripts/preview.py`: SVG preview with exact text widths and a `--square` mode
  for quick-look thumbnails.
- Style guide and spec format references; five worked examples with specs.
- Eval set (3 cases) and grader; CI running the unit tests.
