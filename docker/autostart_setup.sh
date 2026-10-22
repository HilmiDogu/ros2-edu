#!/usr/bin/env bash
# Self-provision the container on every desktop login.
#
# Installed into the Xfce autostart directory by the Dockerfile, so it
# runs once the desktop session comes up -- however the container was
# started (up.sh, up.ps1, `docker compose up -d`, Docker Desktop's play
# button, or a restart after reboot).
#
# Why this exists: the desktop icons and the colcon build live in the
# CONTAINER's filesystem, not in the bind-mounted /workspace. Anyone who
# starts the container without up.sh -- or who recreates it after an
# image rebuild -- gets a bare desktop with no icons and a `ros2 run`
# that cannot find any package. That looks like a broken workspace, and
# it is the first thing a student meets.
#
# Safe and cheap to re-run: it skips the build when one already exists.
set -eo pipefail

LOG=/tmp/autostart_setup.log
exec > >(tee -a "$LOG") 2>&1

echo "[autostart] $(date '+%H:%M:%S') provisioning desktop..."

# --- Desktop icons ------------------------------------------------------
if [ -d /workspace/docker/desktop ]; then
    mkdir -p "$HOME/Desktop"
    cp /workspace/docker/desktop/*.desktop "$HOME/Desktop/" 2>/dev/null || true
    chmod +x "$HOME"/Desktop/*.desktop 2>/dev/null || true

    # Mark them trusted so Xfce launches them without a warning prompt.
    for f in "$HOME"/Desktop/*.desktop; do
        [ -e "$f" ] || continue
        gio set "$f" metadata::xfce-exe-checksum \
            "$(sha256sum "$f" | cut -d' ' -f1)" 2>/dev/null || true
    done
    echo "[autostart] icons installed"

    # Make sure Xfce actually DRAWS them. On a fresh profile
    # /desktop-icons/style is unset, and whether launchers appear is then
    # left to the default -- which has been observed to differ between
    # machines, giving one student a full desktop and another a bare one
    # from identical files. Setting it explicitly removes that variable.
    #   0 = none, 1 = minimised windows, 2 = file/launcher icons
    export DISPLAY="${DISPLAY:-:1}"
    xfconf-query -c xfce4-desktop -p /desktop-icons/style \
        -n -t int -s 2 2>/dev/null || true

    # Hide the stock Home/Filesystem/Trash icons so the numbered course
    # launchers are the only things on the desktop.
    for prop in show-home show-filesystem show-trash show-removable; do
        xfconf-query -c xfce4-desktop -p "/desktop-icons/file-icons/${prop}" \
            -n -t bool -s false 2>/dev/null || true
    done

    # Space-themed desktop wallpaper. The backdrop is configured per
    # monitor AND per workspace, and the property names differ between
    # xfce versions, so set it on every backdrop property that ends in
    # last-image and fix the matching image-style to 'zoomed' (fill the
    # screen). Falls back silently if the image is missing.
    WALL=/workspace/docker/desktop/wallpaper.png
    if [ -f "$WALL" ]; then
        for p in $(xfconf-query -c xfce4-desktop -l 2>/dev/null \
                   | grep 'last-image$'); do
            xfconf-query -c xfce4-desktop -p "$p" -s "$WALL" 2>/dev/null || true
            style="${p%last-image}image-style"
            xfconf-query -c xfce4-desktop -p "$style" -n -t int -s 5 2>/dev/null || true
        done
        # If no backdrop property existed yet (very fresh profile), create
        # one for the current monitor/workspace so there is something to set.
        if ! xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -q 'last-image$'; then
            base=/backdrop/screen0/monitorVNC-0/workspace0
            xfconf-query -c xfce4-desktop -p "$base/last-image" \
                -n -t string -s "$WALL" 2>/dev/null || true
            xfconf-query -c xfce4-desktop -p "$base/image-style" \
                -n -t int -s 5 2>/dev/null || true
        fi
        echo "[autostart] wallpaper set"
    fi

    # Redraw, in case the desktop was already running when this ran.
    xfdesktop --reload 2>/dev/null || true

    # Lay the icons out fresh, in name order (01, 02, ... 09). xfdesktop
    # keeps a saved layout per screen size, and one that predates some
    # icons can leave those icons parked off-screen -- 01-04 vanished this
    # way while 05 onwards showed. Dropping the saved layouts and
    # arranging puts every icon back on screen, top to bottom.
    rm -f "$HOME"/.config/xfce4/desktop/icons.screen*.rc
    sleep 1
    xfdesktop --arrange 2>/dev/null || true
else
    echo "[autostart] WARNING: /workspace/docker/desktop missing."
    echo "[autostart] Is the project directory bind-mounted at /workspace?"
fi

# --- ROS workspace ------------------------------------------------------
# Only build when there is nothing to source. A student who wants a fresh
# build runs docker/build_ws.sh themselves.
if [ ! -f /workspace/install/setup.bash ]; then
    if [ -d /workspace/src ]; then
        echo "[autostart] workspace not built; building (this takes ~30s)..."
        # Never let a build failure abort the desktop session -- a broken
        # build should still leave the student a usable desktop and a log.
        if /workspace/docker/build_ws.sh; then
            echo "[autostart] build finished"
        else
            echo "[autostart] BUILD FAILED. See $LOG"
            echo "[autostart] Re-run by hand: /workspace/docker/build_ws.sh"
        fi
    else
        echo "[autostart] WARNING: /workspace/src missing, nothing to build."
    fi
else
    echo "[autostart] workspace already built"
fi

echo "[autostart] done."
