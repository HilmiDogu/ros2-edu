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


# Craters placed away from the spawn point (spawn is near -4,-4 in metres;
# in 0..1 terrain coords with a 40 m span centred at 0, that is ~0.4,0.4).
CRATERS = [
    # (cx, cy, radius, depth, rim)
    (0.62, 0.58, 0.14, 0.22, 0.04),   # big, deep
    (0.38, 0.66, 0.09, 0.12, 0.03),   # smaller, shallower
    (0.70, 0.30, 0.07, 0.10, 0.02),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = Image.new("L", (N, N))
    px = img.load()
    for j in range(N):
        for i in range(N):
            nx, ny = i / (N - 1), j / (N - 1)
            h = BASE + hills(nx, ny)
            for (cx, cy, r, dep, rim) in CRATERS:
                h += crater(nx, ny, cx, cy, r, dep, rim)
            h = max(0.0, min(1.0, h))
            px[i, j] = int(h * 255)
    out = os.path.join(here, "heightmap.png")
    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
