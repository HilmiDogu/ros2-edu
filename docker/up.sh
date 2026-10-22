#!/usr/bin/env bash
# Build and start the educational ROS 2 + Gazebo workspace.
#
#   ./docker/up.sh
#
# Then open http://localhost:6902 (VNC password: ros2edu).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
compose_file="${here}/docker-compose.yml"
container=ros2-gazebo-edu

# Git Bash on Windows rewrites arguments that look like POSIX paths, so
# `docker exec ... /workspace/docker/build_ws.sh` reached the container
# as C:/.../Git/workspace/... and failed. Container commands go through
# this wrapper, which turns that off; host paths such as compose_file
# still need converting, so it is not set globally. Ignored on Linux
# and macOS.
in_container() {
    MSYS_NO_PATHCONV=1 docker exec "${container}" "$@"
}

# Host ports. Defaults avoid 6901/5901, which another noVNC container
# may already hold. Override for this run:  NOVNC_PORT=6910 ./docker/up.sh
export NOVNC_PORT="${NOVNC_PORT:-6902}"
export VNC_PORT="${VNC_PORT:-5902}"

echo "[up] building image (first run downloads ~4GB, allow 10-20 min)..."
docker compose -f "${compose_file}" build

echo "[up] starting container..."
docker compose -f "${compose_file}" up -d

echo "[up] waiting for the desktop..."
# Probe noVNC itself rather than grepping `docker logs` for a startup
# line: the base image is :latest, and newer versions no longer print
# "noVNC started on TCP port" to stdout, which left this loop waiting
# forever on a desktop that was already up. 6901 is the in-container
# port, so this works whatever NOVNC_PORT the host side was mapped to.
until in_container curl -sf -o /dev/null http://localhost:6901/vnc.html 2>/dev/null; do
    if ! docker ps --filter "name=${container}" --format '{{.Status}}' | grep -q Up; then
        echo "[up] container exited unexpectedly:" >&2
        docker logs --tail 40 "${container}" >&2
        exit 1
    fi
    sleep 2
done

echo "[up] installing desktop launchers..."
# Copied into the desktop user's home rather than launched from the
# bind-mounted /workspace, so they behave like normal desktop entries.
# They exist because the noVNC clipboard does not bridge to the host:
# anything a student would otherwise have to retype by hand in the
# browser GUI is a double-click instead.
in_container bash -lc '
    set -e
    mkdir -p "$HOME/Desktop"
    cp /workspace/docker/desktop/*.desktop "$HOME/Desktop/"
    chmod +x "$HOME"/Desktop/*.desktop
    for f in "$HOME"/Desktop/*.desktop; do
        gio set "$f" metadata::xfce-exe-checksum "$(sha256sum "$f" | cut -d" " -f1)" 2>/dev/null || true
    done
'

echo "[up] building the ROS 2 workspace (colcon)..."
in_container bash -lc '/workspace/docker/build_ws.sh'

cat <<EOF

[up] ready.

  Open:  http://localhost:${NOVNC_PORT}      (VNC password: ros2edu)

  On the browser desktop, double-click:
    "01 Hello ROS 2"      - talker/listener, the core pub/sub demo
    "02 Gazebo World"     - EduBot in Gazebo + RViz2, lidar and camera
    "03 Teleop"           - drive the robot with the keyboard
    "04 Navigation"       - Nav2 autonomous navigation with SLAM
    "Terminal"            - a shell with ROS 2 already sourced

  Stop with:   docker compose -f docker/docker-compose.yml down
EOF
