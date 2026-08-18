# 2D Blueprint → 3D Massing Model

Converts a 2D architectural blueprint / floor plan image into a 3D model
by detecting walls and extruding them upward. Output is a standard
`.obj` file you can open in Blender, MeshLab, Unity, or the included
browser viewer.

How it works, in three steps:

1. **Wall detection** (`src/wall_detector.py`) — the blueprint is
   thresholded into a binary mask: dark line-work (walls) vs. light
   background (open floor space). A small dilation step closes tiny gaps
   in hand-drawn or low-resolution scans.
2. **Extrusion** (`src/mesh_builder.py`) — the mask is extruded into a
   3D grid mesh: wall pixels are raised to `wall_height`, floor pixels
   stay flat at 0. This naturally produces flat floor, flat wall-tops,
   and vertical faces exactly at the wall/floor boundary.
3. **Export** (`src/exporter.py`) — the mesh is written out as a
   textured Wavefront OBJ (`.obj` + `.mtl` + a copy of the blueprint as
   texture).

This gives you a **massing model** — correct footprint, correct wall
heights, walls where the drawing has walls — not a full architectural
BIM model with doors, windows, room labels, or multiple floors. See
"Going further" below for where to take it from here.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

No ML models, no GPU, no internet needed — it's pure image processing
(Pillow + numpy), so it also runs instantly.

## Usage

```bash
python main.py --input floorplan.png --output output/model.obj
```

Then open `output/model.obj` in Blender/MeshLab, drag it into
https://3dviewer.net/, or open `viewer.html` in a browser and select the
`.obj`/`.mtl`/texture files it wrote to `output/`.

### Tuning wall detection

Blueprints vary a lot (hand-drawn, CAD export, scanned print), so the
defaults won't always be right first try:

```bash
python main.py -i floorplan.png -o output/model.obj --save-mask-preview
```

This also writes `output/wall_mask_preview.png` — open it and check that
walls are white and open floor is black. If not:

| Problem | Fix |
|---|---|
| Walls missing / mask mostly black | Lower `--threshold` (try 150–180) |
| Everything is a wall / mask mostly white | Raise `--threshold` (try 210–240) |
| Walls are light-on-dark in the source | Add `--invert` |
| Wall lines are broken/dashed in the mask | Increase `--thicken` (try 2–3) |
| Text, furniture, dimension lines picked up as walls | Raise `--threshold`, or clean the source image first |

### Other options

| Flag | Default | What it does |
|---|---|---|
| `--resolution` | `400` | Mesh grid detail. Higher = crisper wall edges, more triangles, slower. |
| `--wall-height` | `1.0` | Wall height in world units. |
| `--pixels-per-unit` | none | If you know your blueprint's scale (e.g. 50px = 1 meter), pass it here so `--wall-height` corresponds to real units instead of an arbitrary normalized scale. |

Example, for a blueprint where 40 pixels = 1 meter and you want 2.7m walls:

```bash
python main.py -i floorplan.png -o output/model.obj --pixels-per-unit 40 --wall-height 2.7 --resolution 600
```

## Project layout

```
blueprint-to-3d/
├── main.py                 # CLI entry point
├── viewer.html             # drag-and-drop browser viewer (three.js via CDN)
├── requirements.txt
├── src/
│   ├── wall_detector.py    # image -> binary wall mask
│   ├── mesh_builder.py     # mask -> extruded Mesh
│   └── exporter.py         # Mesh -> textured .obj/.mtl/texture.png
└── output/                 # created on first run
```

## Going further

- **Real architectural model (walls, doors, windows, rooms as separate
  objects)**: this needs vector/CAD input (DXF/DWG/IFC) rather than a
  raster image, plus symbol recognition for doors/windows — a much
  bigger project, but tools like FreeCAD's Arch workbench or
  IfcOpenShell are the right starting point.
- **Cleaner wall geometry**: swap the pixel-grid extrusion for polygon
  extraction (OpenCV `findContours`) + proper 2D triangulation (e.g. the
  `mapbox_earcut` or `triangle` packages), which gives straight wall
  edges instead of a stair-stepped raster edge.
- **Multi-floor buildings**: run this once per floor plan image, then
  stack the resulting meshes at the right Z offsets in Blender.
- **Room detection**: flood-fill the non-wall (floor) area to find
  enclosed rooms, and use that to auto-place floor slabs per room or
  compute room areas.

  ##prototype video
  https://youtu.be/gru139WfzCo?si=nBRA72gkgu42QQ2A
