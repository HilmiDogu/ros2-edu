#!/usr/bin/env python3
"""Generate the space backdrop textures: starfield, Earth and Mars discs.

    python3 make_sky.py

Writes into materials/textures/ next to this script. Re-run after
changing any of the constants below.

WHY GENERATE THEM RATHER THAN SHIP IMAGES

The same reason the terrain is generated: the repository stays small and
text-only, every asset is reproducible, and a student can read exactly
how the thing they are looking at was made. Nothing here needs a network
connection or a licence check.

WHY GEOMETRY RATHER THAN A GAZEBO <sky>

Gazebo's built-in sky renders an ATMOSPHERIC sky -- blue gradient,
drifting clouds -- which is precisely wrong on an airless body. More
importantly the rover's camera does not see it: the sky is a GUI-side
effect, so the camera image would stay black while the 3-D view looked
right. Painting the stars and planets onto real geometry means every
sensor sees the same scene the viewer does.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "materials", "textures")

STAR_W, STAR_H = 2048, 1024     # equirectangular, 2:1 for a sphere
PLANET_PX = 512

# Fixed seed: the same sky every run, so a regenerated texture does not
# silently differ from the one in the last screenshot.
random.seed(20261015)


def starfield():
    """A dark sky with stars of varying brightness, plus a faint band.

    Real star fields are mostly empty with a few bright points, not an
    even sprinkle. Drawing a lot of very dim stars and a handful of
    bright ones is what makes it read as a sky rather than as noise.
    """
    img = Image.new("RGB", (STAR_W, STAR_H), (2, 2, 6))
    d = ImageDraw.Draw(img)

    # Milky Way: a diffuse band across the sphere, drawn first so stars
    # sit on top of it.
    band = Image.new("L", (STAR_W, STAR_H), 0)
    bd = ImageDraw.Draw(band)
    for x in range(STAR_W):
        # A gentle sine so the band is not a straight stripe.
        cy = STAR_H * 0.5 + math.sin(x / STAR_W * math.pi * 2) * STAR_H * 0.12
        for _ in range(60):
            y = random.gauss(cy, STAR_H * 0.05)
            if 0 <= y < STAR_H:
                bd.point((x, int(y)), fill=random.randint(12, 34))
    band = band.filter(ImageFilter.GaussianBlur(9))
    img = Image.composite(Image.new("RGB", img.size, (26, 24, 40)), img, band)
    d = ImageDraw.Draw(img)

    # Dim background stars: many, 1 px.
    for _ in range(9000):
        x, y = random.randrange(STAR_W), random.randrange(STAR_H)
        v = random.randint(40, 110)
        d.point((x, y), fill=(v, v, min(255, int(v * 1.05))))

    # Brighter stars: fewer, with a touch of colour and a soft halo.
    for _ in range(600):
        x, y = random.randrange(STAR_W), random.randrange(STAR_H)
        v = random.randint(150, 255)
        # Slight blue or amber tint, as real stars have.
        if random.random() < 0.3:
            col = (v, int(v * 0.88), int(v * 0.72))      # warm
        else:
            col = (int(v * 0.82), int(v * 0.9), v)       # cool
        r = random.choice((1, 1, 1, 2))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    # A dozen standouts with cross flare, which is what sells "space".
    for _ in range(14):
        x, y = random.randrange(STAR_W), random.randrange(STAR_H)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 255))
        for L in range(3, 11):
            f = int(200 * (1 - L / 11))
            d.point((x - L, y), fill=(f, f, f))
            d.point((x + L, y), fill=(f, f, f))
            d.point((x, y - L), fill=(f, f, f))
            d.point((x, y + L), fill=(f, f, f))

    path = os.path.join(OUT, "starfield.png")
    img.save(path)
    print("wrote", path, img.size)


def _disc(name, ocean, land, cloud_strength, polar):
    """A planet disc on transparency: a lit sphere, not a flat circle."""
    n = PLANET_PX
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = img.load()
    cx = cy = n / 2.0
    r = n / 2.0 - 2

    for j in range(n):
        for i in range(n):
            dx, dy = (i - cx) / r, (j - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1.0:
                continue

            # z on the unit sphere, for shading and for continent noise.
            z = math.sqrt(max(0.0, 1.0 - d2))

            # Continents: summed sine waves over the sphere surface.
            v = (math.sin(dx * 7.0 + dy * 3.0) * 0.5
                 + math.sin(dy * 5.5 - dx * 2.5) * 0.35
                 + math.sin((dx + dy) * 11.0) * 0.2
                 + math.sin(z * 6.0) * 0.25)
            is_land = v > 0.18

            # Ice at the poles.
            if abs(dy) > polar:
                base = (235, 240, 245)
            elif is_land:
                base = land
            else:
                base = ocean

            # Cloud veil, brightest where the continents are not.
            c = (math.sin(dx * 9.0 - dy * 4.0) * 0.5
                 + math.sin(dy * 13.0 + dx * 6.0) * 0.5)
            if c > 0.45:
                k = cloud_strength * (c - 0.45) / 0.55
                base = tuple(int(b + (248 - b) * k) for b in base)

            # Lambert shading from the upper left, so the disc reads as a
            # sphere. A flat-lit circle looks like a sticker.
            lx, ly, lz = -0.45, -0.45, 0.77
            lam = max(0.0, dx * lx + dy * ly + z * lz)
            shade = 0.12 + 0.88 * lam

            # Soften the limb so there is no hard pixel edge.
            edge = min(1.0, (1.0 - math.sqrt(d2)) * r / 1.5)

            px[i, j] = (int(base[0] * shade), int(base[1] * shade),
                        int(base[2] * shade), int(255 * edge))

    path = os.path.join(OUT, name)
    img.save(path)
    print("wrote", path, img.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    starfield()
    # Earth seen from the Moon: blue oceans, green-brown land, heavy cloud.
    _disc("earth.png", ocean=(28, 68, 140), land=(72, 110, 62),
          cloud_strength=0.85, polar=0.86)
    # Earth seen from Mars is a pale dot, but a visible disc is more use
    # to a student than an astronomically faithful speck.
    _disc("earth_far.png", ocean=(40, 80, 150), land=(90, 120, 70),
          cloud_strength=0.8, polar=0.86)


if __name__ == "__main__":
    main()
