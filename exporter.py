"""
exporter.py

Writes a Mesh (see mesh_builder.py) out as a textured Wavefront OBJ:
  - name.obj              geometry + UVs, references name.mtl
  - name.mtl              material, references texture file
  - name_texture.png      copy of the source blueprint (or wall mask)

This trio opens directly in Blender, MeshLab, most game engines, and
online viewers like https://3dviewer.net/, or in this project's own
viewer.html.
"""

from __future__ import annotations

import os

from PIL import Image

from .mesh_builder import Mesh


def save_textured_obj(mesh: Mesh, texture_image: Image.Image, out_path: str) -> None:
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(out_path))[0]
    mtl_name = f"{base}.mtl"
    texture_name = f"{base}_texture.png"

    obj_path = out_path
    mtl_path = os.path.join(out_dir, mtl_name)
    texture_path = os.path.join(out_dir, texture_name)

    texture_image.convert("RGB").save(texture_path)

    with open(mtl_path, "w") as f:
        f.write("newmtl material0\n")
        f.write("Ka 1.000 1.000 1.000\n")
        f.write("Kd 1.000 1.000 1.000\n")
        f.write("Ks 0.000 0.000 0.000\n")
        f.write("d 1.0\n")
        f.write("illum 1\n")
        f.write(f"map_Kd {texture_name}\n")

    with open(obj_path, "w") as f:
        f.write(f"mtllib {mtl_name}\n")
        f.write("o blueprint_mesh\n")

        for x, y, z in mesh.vertices:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

        for u, v in mesh.uvs:
            f.write(f"vt {u:.6f} {v:.6f}\n")

        f.write("usemtl material0\n")
        for a, b, c in mesh.faces:
            f.write(f"f {a + 1}/{a + 1} {b + 1}/{b + 1} {c + 1}/{c + 1}\n")

    print(f"Wrote {obj_path}")
    print(f"Wrote {mtl_path}")
    print(f"Wrote {texture_path}")
