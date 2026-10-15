#!/usr/bin/env python3
"""Re-seat the rocks in moon.sdf / mars.sdf onto the current terrain.

    python3 reseat_rocks.py ../../worlds/moon.sdf

Each rock's <pose> carries a hand-set z chosen for the terrain as it was
when the rock was placed. Regenerate the heightmap -- add a crater, raise
a hill -- and those z values no longer match: rocks that sat on the
surface end up buried in a new mound or hanging in the air over a new
crater. Both look like bugs and neither is obvious from the SDF.

This recomputes z from heightmap.png for every rock's (x, y), using the
same mapping make_terrain_mesh.py uses to build the mesh, and rewrites
the pose in place. Run it after any change to make_heightmap.py.

The rest of each pose -- x, y and the three rotations -- is left alone,
so the deliberate scatter is preserved.
"""

import os
import re
import sys

from PIL import Image

# Must match the values in moon.sdf's terrain model and
# make_terrain_mesh.py. The mesh spans SIZE metres square, with the
# heightmap's full 0..255 range mapped onto VERTICAL_RANGE metres, and
# the image's mid-grey (BASE in make_heightmap.py) sitting at z=0.
SIZE = 40.0           # SPAN in make_terrain_mesh.py
VERTICAL_RANGE = 4.0  # VRANGE
ZOFF = -1.8           # ZOFF -- these three MUST match that script

# Rocks are meshes whose origin is near their centre, so seating one
# exactly on the surface half-buries it. A small lift puts it on the
# ground rather than in it; scaled per rock would be better still, but
# this is close enough that it reads correctly.
SINK_COMPENSATION = 0.05


def load_heights(path):
    img = Image.open(path).convert("L")
    return img, img.load(), img.size[0]


def height_at(px, n, x, y):
    """Terrain height in metres at world (x, y)."""
    # World coords -> 0..1 image coords. The mesh is centred on the
    # origin, so x = -SIZE/2 maps to column 0.
    u = (x + SIZE / 2.0) / SIZE
    # Row index is INVERTED: make_terrain_mesh.py builds each vertex as
    # y = (0.5 - j/(M-1)) * SPAN, so image row 0 is +y, not -y. Without
    # the flip every lookup is mirrored north/south and rocks are seated
    # at the height of the wrong side of the map.
    v = (SIZE / 2.0 - y) / SIZE
    u = min(max(u, 0.0), 1.0)
    v = min(max(v, 0.0), 1.0)

    i = int(round(u * (n - 1)))
    j = int(round(v * (n - 1)))
    # Exactly the mapping make_terrain_mesh.py uses to build the mesh;
    # anything else puts rocks at a plausible-looking but wrong height.
    return (px[i, j] / 255.0) * VERTICAL_RANGE + ZOFF


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    here = os.path.dirname(os.path.abspath(__file__))
    _, px, n = load_heights(os.path.join(here, "heightmap.png"))

    world_path = os.path.abspath(sys.argv[1])
    with open(world_path, encoding="utf-8") as fh:
        text = fh.read()

    # <pose>x y z roll pitch yaw</pose> inside a rock <include> block.
    pattern = re.compile(
        r'(<include><name>rock_\w+</name><uri>[^<]+</uri>\s*'
        r'<pose>)([-\d.]+) ([-\d.]+) ([-\d.]+)( [^<]*</pose>)')

    moved = []

    def fix(m):
        head, xs, ys, zs, tail = m.groups()
        x, y, old_z = float(xs), float(ys), float(zs)
        new_z = height_at(px, n, x, y) + SINK_COMPENSATION
        moved.append((x, y, old_z, new_z))
        return f"{head}{x} {y} {new_z:.2f}{tail}"

    new_text, count = pattern.subn(fix, text)

    if not count:
        print(f"no rock poses matched in {world_path}")
        return 1

    with open(world_path, "w", encoding="utf-8") as fh:
        fh.write(new_text)

    print(f"re-seated {count} rocks in {os.path.basename(world_path)}")
    for x, y, old_z, new_z in moved:
        delta = new_z - old_z
        flag = "  <-- moved a lot" if abs(delta) > 0.5 else ""
        print(f"  ({x:6.1f},{y:6.1f})  {old_z:+.2f} -> {new_z:+.2f}"
              f"  ({delta:+.2f}){flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
