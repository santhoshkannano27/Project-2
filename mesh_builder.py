"""
mesh_builder.py

Extrudes a binary wall mask into a simple 3D massing model: wall pixels
are raised to `wall_height`, floor pixels stay at 0. Built as a grid
heightfield (like a terrain mesh) — since the height only ever takes two
values, the mesh naturally forms flat floor, flat wall-tops, and near-
vertical cliffs exactly where the mask transitions from floor to wall.

This is a lightweight way to get a walkable-scale block model of a floor
plan without a full polygon/CAD import + triangulation pipeline. It's an
open surface (no separate floor slab or roof solid) — plenty for a quick
visual / massing model, not meant for CAD-grade output.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass
class Mesh:
    vertices: np.ndarray  # (N, 3) float32
    uvs: np.ndarray       # (N, 2) float32, in [0, 1]
    faces: np.ndarray     # (M, 3) int32, 0-indexed into vertices


def build_mesh_from_mask(
    mask: np.ndarray,
    max_dimension: int = 400,
    wall_height: float = 1.0,
    pixels_per_unit: float | None = None,
) -> Mesh:
    """
    Args:
        mask: (H, W) binary array, 1 = wall, 0 = floor (see wall_detector.py).
        max_dimension: the mesh grid is downsampled so its longer side has
            at most this many vertices (keeps triangle count sane for
            large blueprint scans).
        wall_height: height of walls in world units, relative to the
            floor plan's own units (see pixels_per_unit).
        pixels_per_unit: if you know your blueprint's scale (e.g. this
            many pixels = 1 meter), pass it so the model comes out at a
            sensible real-world proportion. If None, the plan's longer
            side is normalized to 1.0 unit and wall_height is interpreted
            relative to that.

    Returns:
        Mesh ready for export.
    """
    h, w = mask.shape

    scale = max_dimension / max(w, h)
    grid_w = max(2, int(round(w * scale)))
    grid_h = max(2, int(round(h * scale)))

    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    # NEAREST keeps the mask binary (no gray fringing) when downsampling.
    mask_small = np.asarray(mask_img.resize((grid_w, grid_h), resample=Image.NEAREST))
    mask_small = (mask_small > 127).astype(np.float32)

    if pixels_per_unit:
        unit_w = w / pixels_per_unit
        unit_h = h / pixels_per_unit
    else:
        longer = max(w, h)
        unit_w = w / longer
        unit_h = h / longer

    xs = np.linspace(0.0, unit_w, grid_w, dtype=np.float32)
    ys = np.linspace(0.0, unit_h, grid_h, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(xs, ys)  # (grid_h, grid_w)

    vx = grid_x - unit_w / 2
    vy = unit_h / 2 - grid_y  # flip so row 0 (top of image) is +Y
    vz = mask_small * wall_height

    vertices = np.stack([vx, vy, vz], axis=-1).reshape(-1, 3).astype(np.float32)

    uv_u = np.linspace(0.0, 1.0, grid_w, dtype=np.float32)
    uv_v = np.linspace(1.0, 0.0, grid_h, dtype=np.float32)
    guv_u, guv_v = np.meshgrid(uv_u, uv_v)
    uvs = np.stack([guv_u, guv_v], axis=-1).reshape(-1, 2).astype(np.float32)

    faces = []
    for j in range(grid_h - 1):
        row0 = j * grid_w
        row1 = (j + 1) * grid_w
        for i in range(grid_w - 1):
            v00 = row0 + i
            v01 = row0 + i + 1
            v10 = row1 + i
            v11 = row1 + i + 1
            faces.append((v00, v10, v11))
            faces.append((v00, v11, v01))

    faces = np.asarray(faces, dtype=np.int32)

    return Mesh(vertices=vertices, uvs=uvs, faces=faces)
