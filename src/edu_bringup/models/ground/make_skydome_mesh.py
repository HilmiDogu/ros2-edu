#!/usr/bin/env python3
"""Generate skydome.obj: a large sphere with INWARD-facing normals.

    python3 make_skydome_mesh.py

A normal sphere is viewed from outside, so from within the world it is
invisible -- back-face culling removes exactly the faces you want to see.
Reversing the winding order makes the inside the visible surface, which
is what turns a sphere into a sky.

UV mapping is equirectangular, matching starfield.png's 2:1 layout.
"""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
R = 120.0          # metres. Comfortably beyond the 30 m terrain, and
                   # inside the camera's 100 m far clip so it renders.
RINGS, SEGS = 32, 64

verts, uvs, norms, faces = [], [], [], []
for i in range(RINGS + 1):
    lat = math.pi * i / RINGS           # 0 at +z pole
    for j in range(SEGS + 1):
        lon = 2 * math.pi * j / SEGS
        x = R * math.sin(lat) * math.cos(lon)
        y = R * math.sin(lat) * math.sin(lon)
        z = R * math.cos(lat)
        verts.append((x, y, z))
        uvs.append((j / SEGS, 1.0 - i / RINGS))
        # Normals point INWARD, towards the origin.
        n = math.sqrt(x*x + y*y + z*z) or 1.0
        norms.append((-x/n, -y/n, -z/n))

def vid(i, j):
    return i * (SEGS + 1) + j + 1       # OBJ is 1-indexed

for i in range(RINGS):
    for j in range(SEGS):
        a, b, c, d = vid(i, j), vid(i, j+1), vid(i+1, j+1), vid(i+1, j)
        # Reversed winding, so the inside faces the viewer.
        faces.append((a, d, c))
        faces.append((a, c, b))

out = os.path.join(HERE, "skydome.obj")
with open(out, "w") as f:
    f.write("# inward-facing sky sphere\n")
    for v in verts: f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
    for t in uvs:   f.write(f"vt {t[0]:.5f} {t[1]:.5f}\n")
    for n in norms: f.write(f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}\n")
    for a, b, c in faces:
        f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
print(f"wrote {out}: {len(verts)} verts, {len(faces)} faces, R={R}")
