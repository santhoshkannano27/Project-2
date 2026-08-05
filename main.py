#!/usr/bin/env python3
"""
main.py — 2D blueprint / floor plan to 3D massing model.

Usage:
    python main.py --input floorplan.png --output output/model.obj

Pipeline:
    1. Load the blueprint image.
    2. Threshold it into a binary wall mask (dark lines = walls).
    3. Extrude the mask into a 3D mesh: walls raised, floor flat.
    4. Export as a textured Wavefront OBJ, viewable in Blender, MeshLab,
       or the included viewer.html.

See README.md for tuning the wall detection and scale.
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert a 2D blueprint/floor plan into a 3D massing model.")
    p.add_argument("--input", "-i", required=True, help="Path to the blueprint image.")
    p.add_argument(
        "--output", "-o", default="output/model.obj",
        help="Path to the output .obj file (default: output/model.obj).",
    )
    p.add_argument(
        "--threshold", type=int, default=200,
        help="Grayscale cutoff 0-255 for what counts as a wall line (default: 200). "
             "Lower it if faint walls are missed; raise it if text/furniture get picked up.",
    )
    p.add_argument(
        "--invert", action="store_true",
        help="Use if your blueprint has light walls on a dark background.",
    )
    p.add_argument(
        "--thicken", type=int, default=1,
        help="Dilation passes to close small gaps in wall lines (default: 1).",
    )
    p.add_argument(
        "--resolution", type=int, default=400,
        help="Longer side of the mesh grid, in vertices (default: 400). "
             "Higher = crisper wall edges, more triangles, slower.",
    )
    p.add_argument(
        "--wall-height", type=float, default=1.0,
        help="Wall height in world units (default: 1.0). See --pixels-per-unit "
             "to tie this to your blueprint's real scale.",
    )
    p.add_argument(
        "--pixels-per-unit", type=float, default=None,
        help="If known, how many pixels in the blueprint equal one real-world "
             "unit (e.g. one meter). Ties --wall-height to a real scale. "
             "If omitted, the plan is just normalized to fit a unit box.",
    )
    p.add_argument(
        "--save-mask-preview", action="store_true",
        help="Also save the detected wall mask as a black/white PNG, for tuning --threshold.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"Input image not found: {args.input}", file=sys.stderr)
        return 1

    from src.wall_detector import load_wall_mask, wall_coverage_ratio
    from src.mesh_builder import build_mesh_from_mask
    from src.exporter import save_textured_obj

    print(f"Loading blueprint: {args.input}")
    image = Image.open(args.input).convert("RGB")

    print("Detecting walls...")
    mask = load_wall_mask(
        image,
        threshold=args.threshold,
        invert=args.invert,
        thicken=args.thicken,
    )

    coverage = wall_coverage_ratio(mask)
    print(f"Wall coverage: {coverage:.1%} of pixels")
    if coverage < 0.005 or coverage > 0.6:
        print(
            "Warning: that coverage looks off for a floor plan — try adjusting "
            "--threshold, or add --invert if walls are light-on-dark.",
            file=sys.stderr,
        )

    if args.save_mask_preview:
        out_dir = os.path.dirname(args.output) or "."
        os.makedirs(out_dir, exist_ok=True)
        preview_path = os.path.join(out_dir, "wall_mask_preview.png")
        Image.fromarray((mask * 255).astype("uint8")).save(preview_path)
        print(f"Wrote {preview_path}")

    print("Building mesh...")
    mesh = build_mesh_from_mask(
        mask,
        max_dimension=args.resolution,
        wall_height=args.wall_height,
        pixels_per_unit=args.pixels_per_unit,
    )
    print(f"Mesh has {len(mesh.vertices)} vertices, {len(mesh.faces)} faces.")

    print("Exporting textured OBJ...")
    save_textured_obj(mesh, image, args.output)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
