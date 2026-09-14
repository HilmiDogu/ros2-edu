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
