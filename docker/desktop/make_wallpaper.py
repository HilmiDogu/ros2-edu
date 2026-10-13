#!/usr/bin/env python3
"""Generate the desktop wallpaper for the ROS 2 + Gazebo space workspace.

Run once to (re)create wallpaper.png next to this script. Kept in the repo
so the image is reproducible and nothing is downloaded -- it is drawn
procedurally with PIL, like the ground textures.

    python3 make_wallpaper.py

A dark starfield with a soft nebula glow and a lunar horizon at the
bottom, sized 1920x1080 and dark enough that the light desktop icons and
their labels stay readable on top.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080


def make(path):
    rnd = random.Random(7)

    # 1. vertical gradient: near-black at top easing to a deep blue.
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        f = y / H
        row = (int(6 + 10 * f), int(8 + 14 * f), int(16 + 34 * f))
        for x in range(W):
            px[x, y] = row

    # 2. a soft off-centre nebula glow: drawn big, blurred, added on top.
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.72), int(H * 0.30)
    gd.ellipse([cx - 420, cy - 300, cx + 420, cy + 300], fill=(40, 30, 70))
    gd.ellipse([cx - 250, cy - 180, cx + 250, cy + 180], fill=(70, 45, 95))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    gpx = glow.load()
    for y in range(H):
        for x in range(W):
            br, bg, bb = px[x, y]
            gr, gg, gb = gpx[x, y]
            px[x, y] = (min(255, br + gr), min(255, bg + gg), min(255, bb + gb))

    draw = ImageDraw.Draw(img)

    # 3. stars: many faint, a few bright with a tiny cross flare.
    opx = img.load()
    for _ in range(1400):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.82))
        b = rnd.randint(40, 150)
        r0, g0, b0 = opx[x, y]
        opx[x, y] = (min(255, r0 + b), min(255, g0 + b), min(255, b0 + b))
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.8))
        draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(230, 235, 255))
        if rnd.random() < 0.5:
            draw.line([x - 4, y, x + 4, y], fill=(120, 130, 170))
            draw.line([x, y - 4, x, y + 4], fill=(120, 130, 170))

    # 4. a lunar/planetary horizon arc across the bottom, grey regolith,
    #    with a lit upper rim so it reads as a curved surface.
    horizon_r = int(W * 1.1)
    hx, hy = W // 2, int(H + horizon_r - H * 0.14)
    draw.ellipse([hx - horizon_r, hy - horizon_r, hx + horizon_r, hy + horizon_r],
                 fill=(32, 31, 34))
    # lit rim
    draw.arc([hx - horizon_r, hy - horizon_r, hx + horizon_r, hy + horizon_r],
             start=200, end=340, fill=(120, 118, 125), width=6)

    # surface_y(x): the y of the lunar surface directly below screen x, from
    # the same circle as the horizon. Craters are placed relative to THIS so
    # they always sit ON the curved surface instead of floating above it
    # where the horizon dips near the edges.
    def surface_y(x):
        dx = x - hx
        inside = horizon_r * horizon_r - dx * dx
        return hy - math.sqrt(inside) if inside > 0 else H + 1

    # craters, each a depth below the surface at its x (fdepth) so it hugs
    # the curve. fr is the horizontal radius.
    for (fx, fdepth, fr) in [(0.28, 24, 70), (0.55, 70, 55),
                             (0.78, 150, 46), (0.92, 70, 36)]:
        ex = int(W * fx)
        ey = int(surface_y(ex) + fdepth)
        draw.ellipse([ex - fr, ey - fr // 3, ex + fr, ey + fr // 3], fill=(24, 23, 26))
        draw.arc([ex - fr, ey - fr // 3, ex + fr, ey + fr // 3],
                 start=200, end=340, fill=(80, 78, 84), width=3)

    # 5. a soft title, bottom-left, low-contrast so it never fights icons.
    draw.text((40, H - 54), "ROS 2  .  Gazebo  .  EduBot", fill=(90, 100, 130))

    img.save(path)
    print("wrote", path, img.size)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    make(os.path.join(here, "wallpaper.png"))
