#!/usr/bin/env python3
"""Generate tileable ground textures for the Moon and Mars worlds.

Run once to (re)create the PNGs under materials/textures/. Kept in the
repo so the textures are reproducible and the workspace stays offline:
no image is downloaded, everything is procedural.

    python3 make_textures.py

Produces:
    materials/textures/moon_regolith.png   grey, speckled, faint craters
    materials/textures/mars_soil.png       red-brown dust with darker rocks

Both are seamless (wrap-around), so tiling them across the ground plane
shows no visible seams.
"""
import math
import os
import random

from PIL import Image

SIZE = 512  # texture is SIZE x SIZE, tileable


def _wrapped_blob(px, cx, cy, radius, delta, w, h):
    """Add `delta` to pixels within `radius` of (cx, cy), wrapping at the
    edges so the texture stays seamless. delta<0 darkens (a pit), >0
    lightens (a rim highlight)."""
    r2 = radius * radius
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d2 = dx * dx + dy * dy
            if d2 > r2:
                continue
            falloff = 1.0 - math.sqrt(d2) / radius
            x = (cx + dx) % w
            y = (cy + dy) % h
            r, g, b = px[x, y]
            k = int(delta * falloff)
            px[x, y] = (
                max(0, min(255, r + k)),
                max(0, min(255, g + k)),
                max(0, min(255, b + k)),
            )


def make(path, base, grain, seed, n_craters, n_rocks):
    """base = (r,g,b) mean colour; grain = per-pixel noise amplitude."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()

    # 1. base colour + fine per-pixel grain (the dusty speckle)
    for y in range(SIZE):
        for x in range(SIZE):
            n = rnd.randint(-grain, grain)
            px[x, y] = (
                max(0, min(255, base[0] + n)),
                max(0, min(255, base[1] + n)),
                max(0, min(255, base[2] + n)),
            )

    # 2. faint craters: a dark pit with a slightly lighter rim
    for _ in range(n_craters):
        cx, cy = rnd.randrange(SIZE), rnd.randrange(SIZE)
        radius = rnd.randint(12, 40)
        _wrapped_blob(px, cx, cy, radius, -rnd.randint(18, 34), SIZE, SIZE)
        _wrapped_blob(px, cx, cy, max(3, radius // 3),
                      rnd.randint(10, 20), SIZE, SIZE)

    # 3. scattered small rocks: little dark clumps
    for _ in range(n_rocks):
        cx, cy = rnd.randrange(SIZE), rnd.randrange(SIZE)
        _wrapped_blob(px, cx, cy, rnd.randint(2, 6),
                      -rnd.randint(20, 45), SIZE, SIZE)

    img.save(path)
    print("wrote", path)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    tex = os.path.join(here, "materials", "textures")
    os.makedirs(tex, exist_ok=True)

    # Moon: neutral grey regolith, low colour, many small craters.
    make(os.path.join(tex, "moon_regolith.png"),
         base=(105, 103, 100), grain=14, seed=1, n_craters=40, n_rocks=500)

    # Mars: warm red-brown iron-oxide dust, fewer craters, more rocks.
    make(os.path.join(tex, "mars_soil.png"),
         base=(140, 78, 52), grain=16, seed=2, n_craters=18, n_rocks=650)
