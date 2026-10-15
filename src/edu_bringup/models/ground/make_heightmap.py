#!/usr/bin/env python3
"""Generate the terrain heightmap for the Moon and Mars worlds.

Gazebo renders a <heightmap> from a greyscale image: pixel brightness ->
elevation (black = lowest, white = highest), scaled by the <size> in the
world file. The image must be square and (2^n + 1) on a side; we use
129x129, which is plenty for a 40 m arena and cheap to collide against.

Run once to (re)create heightmap.png next to this file. Kept in the repo
so the terrain is reproducible and nothing is downloaded.

    python3 make_heightmap.py

The terrain has:
  * gentle rolling hills (summed low-frequency sine waves),
  * a couple of real bowl-shaped CRATERS the rover can drive down into,
  * a mid-grey base so craters can dip below it and hills rise above it.
"""
import math
import os

from PIL import Image

N = 129                      # (2^7 + 1), Gazebo-legal heightmap size
BASE = 0.45                  # mid elevation (0..1); leaves room to dip down


def hills(nx, ny):
    """Rolling terrain in 0..1 from a few low-frequency waves."""
    h = 0.0
    h += 0.10 * math.sin(nx * 2 * math.pi * 1.3 + 0.5)
    h += 0.08 * math.sin(ny * 2 * math.pi * 1.1 + 1.7)
    h += 0.06 * math.sin((nx + ny) * 2 * math.pi * 0.9)
    h += 0.05 * math.sin((nx - ny) * 2 * math.pi * 1.7 + 3.0)
    h += 0.03 * math.sin(nx * 2 * math.pi * 3.1) * math.sin(ny * 2 * math.pi * 2.7)
    return h


def mound(nx, ny, cx, cy, radius, height):
    """A steep hill centred at (cx,cy): a NO-GO area.

    Deliberately much steeper than the rolling `hills` above. A gaussian
    rather than a cosine falloff, so the flanks keep rising instead of
    levelling off -- the rover loses traction partway up and slides back,
    which is the point. In low gravity this happens sooner than students
    expect, and is the terrain equivalent of an obstacle the planner has
    to route around rather than drive over.
    """
    d = math.hypot(nx - cx, ny - cy)
    if d > radius:
        return 0.0
    t = d / radius
    return height * math.exp(-(t * t) / 0.18)


def crater(nx, ny, cx, cy, radius, depth, rim):
    """A bowl depression centred at (cx,cy) in 0..1 coords. Negative in the
    middle (dug out), with a slightly raised rim, fading to 0 outside."""
    d = math.hypot(nx - cx, ny - cy)
    if d > radius:
        return 0.0
    t = d / radius                 # 0 at centre, 1 at rim
    # smooth bowl: deep at centre, up through a raised rim near the edge.
    bowl = -depth * (1.0 - t * t)
    ring = rim * math.exp(-((t - 0.85) ** 2) / 0.01)
    return bowl + ring


# Craters in 0..1 terrain coords (40 m span centred at 0; 0.5,0.5 = origin).
# A good spread of sizes and depths across the whole arena. The spawn point
# (~0.4,0.4) is deliberately left clear.
CRATERS = [
    # (cx, cy, radius, depth, rim)
    (0.62, 0.58, 0.14, 0.22, 0.04),   # big, deep
    (0.38, 0.66, 0.09, 0.12, 0.03),   # medium
    (0.22, 0.28, 0.11, 0.16, 0.03),   # medium, SW
    (0.80, 0.72, 0.08, 0.13, 0.03),   # NE
    (0.50, 0.85, 0.10, 0.14, 0.03),   # N
    (0.15, 0.80, 0.06, 0.09, 0.02),   # small, NW
    (0.85, 0.15, 0.09, 0.15, 0.03),   # SE
    (0.30, 0.50, 0.05, 0.08, 0.02),   # small, central-W
    # Small, sharp craters. A tight radius with a comparatively large
    # depth makes a steep-sided pit that reads as a hole to drive around
    # rather than a dish to roll through -- and gives the 3-D lidar some
    # abrupt depth changes to show.
    (0.70, 0.35, 0.040, 0.16, 0.02),  # pit, E
    (0.44, 0.22, 0.035, 0.14, 0.02),  # pit, S
    (0.58, 0.76, 0.045, 0.15, 0.02),  # pit, NNE
    (0.12, 0.45, 0.038, 0.13, 0.02),  # pit, W
    (0.90, 0.52, 0.042, 0.15, 0.02),  # pit, far E
    # A crater pair, close enough that the ridge between them is a
    # natural narrow pass.
    (0.26, 0.62, 0.070, 0.13, 0.035),
    (0.26, 0.74, 0.070, 0.13, 0.035),
]

# Steep hills the rover cannot climb: no-go areas it must route around.
# Height is in the same 0..1 units as everything else, so with the 4 m
# vertical range in moon.sdf a 0.20 mound stands ~0.8 m proud of its
# surroundings over a couple of metres -- far too steep for the rover.
MOUNDS = [
    # (cx, cy, radius, height)
    (0.78, 0.26, 0.11, 0.26),   # big massif, SE
    (0.18, 0.18, 0.09, 0.22),   # SW
    (0.46, 0.44, 0.07, 0.18),   # central, splits the arena
    (0.86, 0.86, 0.10, 0.24),   # far NE corner
    (0.08, 0.62, 0.075, 0.20),  # W
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = Image.new("L", (N, N))
    px = img.load()
    for j in range(N):
        for i in range(N):
            nx, ny = i / (N - 1), j / (N - 1)
            h = BASE + hills(nx, ny)
            for (cx, cy, r, hgt) in MOUNDS:
                h += mound(nx, ny, cx, cy, r, hgt)
            # Craters last, so a crater placed on a slope still digs in
            # rather than being filled by the mound added after it.
            for (cx, cy, r, dep, rim) in CRATERS:
                h += crater(nx, ny, cx, cy, r, dep, rim)
            h = max(0.0, min(1.0, h))
            px[i, j] = int(h * 255)
    out = os.path.join(here, "heightmap.png")
    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
