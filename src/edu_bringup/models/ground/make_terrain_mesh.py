#!/usr/bin/env python3
"""Turn the heightmap into a terrain MESH (terrain.obj).

Why a mesh and not just the <heightmap> element: Gazebo's physics engine
(DART) collides reliably against triangle meshes but only flakily against
heightmaps -- a light body in low gravity driving at speed tunnels
straight through a <heightmap> collision and falls out of the world. A
mesh collision holds. So the worlds use this .obj for BOTH collision and
visual, built from the same elevation data as heightmap.png.

Run after regenerating the heightmap:
    python3 make_heightmap.py && python3 make_terrain_mesh.py

Produces terrain.obj (grid of triangles) next to this file. 40 x 40 m
span, 4 m vertical range, matching the heightmap's <size> in the worlds.
UVs tile the surface texture a few times across. No external deps beyond
PIL; writes a plain Wavefront OBJ.
"""
import os

from PIL import Image

SPAN = 30.0        # metres across (X and Y)
VRANGE = 12.0      # metres of elevation (black->white)
#
# 4 m of relief over a 40 m span is a 10% grade -- geometrically correct
# but visually flat: the craters and hills were there and simply did not
# read as terrain. 12 m over 30 m makes the mounds genuinely unclimbable
# and the craters visibly deep, which is the point of having them.
ZOFF = -5.4        # mid-grey (0.45) sits near z=0: -0.45*VRANGE
TILES = 8.0        # texture repeats across the terrain


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = Image.open(os.path.join(here, "heightmap.png")).convert("L")
    N, M = img.size
    px = img.load()

    def elev(i, j):
        return (px[i, j] / 255.0) * VRANGE + ZOFF

    verts = []
    uvs = []
    # Grid of vertices. World x spans -SPAN/2..SPAN/2 across image columns,
    # world y across image rows (row 0 = +y, to match Gazebo heightmap).
    for j in range(M):
        for i in range(N):
            x = (i / (N - 1) - 0.5) * SPAN
            y = (0.5 - j / (M - 1)) * SPAN
            z = elev(i, j)
            verts.append((x, y, z))
            uvs.append((i / (N - 1) * TILES, (1 - j / (M - 1)) * TILES))

    def vid(i, j):
        return j * N + i + 1          # OBJ is 1-indexed

    faces = []
    for j in range(M - 1):
        for i in range(N - 1):
            a, b = vid(i, j), vid(i + 1, j)
            c, d = vid(i, j + 1), vid(i + 1, j + 1)
            # two triangles per cell, wound CCW for upward normals
            faces.append((a, c, b))
            faces.append((b, c, d))

    # Per-vertex normals from the heightmap gradient. DART's mesh collider
    # REQUIRES a normal per vertex -- without them it ignores the mesh and
    # then segfaults, so these are not optional. The surface normal at a
    # grid point is (-dz/dx, -dz/dy, 1) normalised.
    import math
    dx = SPAN / (N - 1)
    dy = SPAN / (M - 1)
    normals = []
    for j in range(M):
        for i in range(N):
            zl = elev(max(0, i - 1), j)
            zr = elev(min(N - 1, i + 1), j)
            zd = elev(i, max(0, j - 1))
            zu = elev(i, min(M - 1, j + 1))
            nx = -(zr - zl) / (2 * dx)
            ny = -(zu - zd) / (2 * dy)
            nz = 1.0
            n = math.sqrt(nx * nx + ny * ny + nz * nz)
            normals.append((nx / n, ny / n, nz / n))

    out = os.path.join(here, "terrain.obj")
    with open(out, "w") as f:
        f.write("# terrain mesh generated from heightmap.png\n")
        for (x, y, z) in verts:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for (u, v) in uvs:
            f.write(f"vt {u:.4f} {v:.4f}\n")
        for (nx, ny, nz) in normals:
            f.write(f"vn {nx:.4f} {ny:.4f} {nz:.4f}\n")
        for (a, c, b) in faces:
            f.write(f"f {a}/{a}/{a} {c}/{c}/{c} {b}/{b}/{b}\n")
    print(f"wrote {out}: {len(verts)} verts, {len(normals)} normals, "
          f"{len(faces)} faces")


if __name__ == "__main__":
    main()
