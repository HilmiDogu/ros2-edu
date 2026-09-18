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

    # Redraw, in case the desktop was already running when this ran.
    xfdesktop --reload 2>/dev/null || true
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
