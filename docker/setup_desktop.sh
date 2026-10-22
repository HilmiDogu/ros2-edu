#!/usr/bin/env bash
# Reinstall the desktop launcher icons and rebuild the ROS workspace.
#
#   docker exec ros2-gazebo-edu /workspace/docker/setup_desktop.sh
#
# Run this after the container has been RECREATED (docker compose up
# following an image rebuild, or `down` then `up`). The icons and the
# colcon build live in the container's own filesystem, not in the
# bind-mounted /workspace, so recreating the container discards both --
# the desktop then comes up bare, with no numbered icons.
#
# up.sh / up.ps1 already do this; use this script when you restarted the
# container without them.
set -eo pipefail

echo "[setup] installing desktop launchers..."
mkdir -p "$HOME/Desktop"
cp /workspace/docker/desktop/*.desktop "$HOME/Desktop/"
chmod +x "$HOME"/Desktop/*.desktop

# Mark them trusted so Xfce launches them without a warning prompt.
for f in "$HOME"/Desktop/*.desktop; do
    gio set "$f" metadata::xfce-exe-checksum \
        "$(sha256sum "$f" | cut -d' ' -f1)" 2>/dev/null || true
done

# Make sure Xfce actually DRAWS them: on a fresh profile
# /desktop-icons/style is unset, and the default has been observed to
# differ between machines -- identical files, bare desktop on one and a
# full one on another.
#   0 = none, 1 = minimised windows, 2 = file/launcher icons
export DISPLAY="${DISPLAY:-:1}"
xfconf-query -c xfce4-desktop -p /desktop-icons/style \
    -n -t int -s 2 2>/dev/null || true
for prop in show-home show-filesystem show-trash show-removable; do
    xfconf-query -c xfce4-desktop -p "/desktop-icons/file-icons/${prop}" \
        -n -t bool -s false 2>/dev/null || true
done

# Space-themed wallpaper, on every per-monitor/per-workspace backdrop.
WALL=/workspace/docker/desktop/wallpaper.png
if [ -f "$WALL" ]; then
    for p in $(xfconf-query -c xfce4-desktop -l 2>/dev/null | grep 'last-image$'); do
        xfconf-query -c xfce4-desktop -p "$p" -s "$WALL" 2>/dev/null || true
        xfconf-query -c xfce4-desktop -p "${p%last-image}image-style" \
            -n -t int -s 5 2>/dev/null || true
    done
    if ! xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -q 'last-image$'; then
        base=/backdrop/screen0/monitorVNC-0/workspace0
        xfconf-query -c xfce4-desktop -p "$base/last-image" -n -t string -s "$WALL" 2>/dev/null || true
        xfconf-query -c xfce4-desktop -p "$base/image-style" -n -t int -s 5 2>/dev/null || true
    fi
    echo "[setup] wallpaper set"
fi
xfdesktop --reload 2>/dev/null || true

# Lay the icons out fresh, in name order (01, 02, ... 09). xfdesktop keeps
# a saved layout per screen size, and one that predates some icons can
# leave those icons parked off-screen -- 01-04 vanished this way while
# 05 onwards showed. Dropping the saved layouts and arranging puts every
# icon back on screen, top to bottom.
rm -f "$HOME"/.config/xfce4/desktop/icons.screen*.rc
sleep 1
xfdesktop --arrange 2>/dev/null || true

echo "[setup] icons installed:"
ls -1 "$HOME/Desktop"/*.desktop | xargs -n1 basename

# Only build if it has not been built already -- this script is meant to
# be cheap to re-run.
if [ ! -f /workspace/install/setup.bash ]; then
    echo "[setup] workspace not built yet, building..."
    /workspace/docker/build_ws.sh
else
    echo "[setup] workspace already built (run build_ws.sh to rebuild)."
fi

echo "[setup] done."
