#!/usr/bin/env bash
# Open an EXTRA browser-visible screen, so Gazebo, RViz and a terminal
# can each have a monitor instead of fighting over one.
#
#   docker exec ros2-gazebo-edu bash /workspace/docker/extra_screen.sh 2
#   docker exec ros2-gazebo-edu bash /workspace/docker/extra_screen.sh 3
#
# Screen N appears at http://localhost:690N (screen 2 -> 6903, screen
# 3 -> 6904). Open each in its own browser window and drag it to the
# monitor you want. Password is the same throughout: ros2edu.
#
# WHY EXTRA SCREENS RATHER THAN ONE BIGGER ONE
#
# A single virtual screen can only usefully be as large as the monitor
# you view it on; past that the browser scales it back down. Independent
# screens can each be fullscreened on a different physical monitor,
# which is what you actually want when a module has you watching the
# simulation, the ROS-side view and a terminal at once.
#
# Each screen runs its own Xvnc and its own noVNC, separate from the
# base image's :1 / 6901. Nothing here touches the main desktop, so a
# failure leaves it working.
#
# A SUGGESTED SPLIT
#
#   main desktop (6902) : terminals, and the desktop launchers
#   screen 2     (6903) : RViz
#   screen 3     (6904) : Gazebo
#
# Start the simulation with both GUIs off and place them yourself:
#
#   ros2 launch edu_bringup simulation.launch.py gui:=false rviz:=false
#   DISPLAY=:2 rviz2 -d /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz
#   DISPLAY=:3 gz sim -g
#
set -eo pipefail

# Which screen to open. Ports are derived from it rather than listed, so
# a fourth screen needs no new code -- only a port mapping in
# docker-compose.yml.
#
#   screen 2 -> display :2, VNC 5903, noVNC 6903
#   screen 3 -> display :3, VNC 5904, noVNC 6904
DISPLAY_NUM="${1:-${DISPLAY_NUM:-2}}"
case "${DISPLAY_NUM}" in
    ''|*[!0-9]*)
        echo "usage: extra_screen.sh [screen-number]   (2, 3, ...)" >&2
        exit 1 ;;
esac
if [ "${DISPLAY_NUM}" -lt 2 ]; then
    echo "[screen] :0 and :1 belong to the main desktop; use 2 or higher." >&2
    exit 1
fi

VNC_PORT="${EXTRA_VNC_PORT:-$((5901 + DISPLAY_NUM))}"
NOVNC_PORT="${EXTRA_NOVNC_PORT:-$((6901 + DISPLAY_NUM))}"
RES="${EXTRA_RESOLUTION:-1920x1080}"

if [ -z "${HOME}" ]; then
    echo "[screen${DISPLAY_NUM}] HOME is unset; run as the desktop user, not root." >&2
    exit 1
fi

if pgrep -f "Xvnc :${DISPLAY_NUM}" >/dev/null 2>&1; then
    echo "[screen${DISPLAY_NUM}] display :${DISPLAY_NUM} is already running."
    echo "[screen${DISPLAY_NUM}] open http://localhost:${NOVNC_PORT}"
    exit 0
fi

# Reuse the password file the base image already created for :1, so both
# screens share one password. Its location moved between TigerVNC
# versions, so try the known spellings rather than hard-coding one.
PASSWD_FILE=""
for cand in "${HOME}/.config/tigervnc/passwd" "${HOME}/.vnc/passwd"; do
    [ -f "$cand" ] && { PASSWD_FILE="$cand"; break; }
done
if [ -z "${PASSWD_FILE}" ]; then
    echo "[screen${DISPLAY_NUM}] no VNC password file found - has the desktop started?" >&2
    exit 1
fi

# Xvnc directly, NOT the `vncserver` wrapper: this base image ships its
# own wrapper that accepts only a display number and rejects the
# geometry/port flags needed here.
#
# -ac disables X host access control on THIS display. Xvnc adds no
# cookie for :2 to ~/.Xauthority, so without it every app started with
# DISPLAY=:2 is refused and never opens a window. The display is still
# behind the VNC password and reachable only inside the container.
echo "[screen${DISPLAY_NUM}] starting Xvnc on :${DISPLAY_NUM} at ${RES}..."
nohup /usr/bin/Xvnc ":${DISPLAY_NUM}" -depth 24 -geometry "${RES}" \
    -rfbport "${VNC_PORT}" -rfbauth "${PASSWD_FILE}" -pn -ac \
    >/tmp/screen${DISPLAY_NUM}_xvnc.log 2>&1 &

sleep 3
if ! pgrep -f "Xvnc :${DISPLAY_NUM}" >/dev/null 2>&1; then
    echo "[screen${DISPLAY_NUM}] Xvnc failed to start:" >&2
    tail -5 /tmp/screen${DISPLAY_NUM}_xvnc.log >&2
    exit 1
fi

export DISPLAY=":${DISPLAY_NUM}"


# A window manager, so windows have title bars and can be moved and
# resized. Without one, apps appear fixed and unmanageable, which
# defeats the point of a second screen.
nohup xfwm4 --display="${DISPLAY}" >/tmp/screen${DISPLAY_NUM}_wm.log 2>&1 &
sleep 1

# Paint the root window. Without this the screen is pure black, which is
# indistinguishable from "this screen is broken" -- the display is
# fine, there is simply nothing drawn on it yet. A solid colour makes it
# obvious the screen is live and waiting for an app.
xsetroot -solid "#1d3a52" 2>/dev/null || true

# A terminal, so the screen is useful the moment you open it rather than
# requiring you to go back to screen 1 to launch anything. xfce4-terminal
# rather than xterm: xterm fails here with a missing-font error.
if command -v xfce4-terminal >/dev/null 2>&1; then
    nohup xfce4-terminal --geometry=100x24+40+40 \
        --title="screen ${DISPLAY_NUM} - DISPLAY=:${DISPLAY_NUM}" \
        >/tmp/screen${DISPLAY_NUM}_term.log 2>&1 &
fi
sleep 1

# noVNC in front of it so a browser can reach the screen.
NOVNC_WEB=""
# /usr/libexec/noVNCdim is where THIS base image puts them; the others
# are the common upstream locations, kept as fallbacks.
for d in /usr/libexec/noVNCdim /usr/share/novnc /usr/local/share/novnc /opt/novnc; do
    [ -d "$d" ] && { NOVNC_WEB="$d"; break; }
done

if [ -z "${NOVNC_WEB}" ]; then
    echo "[screen${DISPLAY_NUM}] noVNC web assets not found." >&2
    echo "[screen${DISPLAY_NUM}] The raw VNC port ${VNC_PORT} still works in a native viewer." >&2
    exit 0
fi

# `python3 -m websockify`, matching how the base image launches its own.
# There is no websockify binary on PATH and the module is not installed
# system-wide: it ships inside the noVNC tree, so PYTHONPATH has to point
# at it or the import fails with "No module named websockify".
export PYTHONPATH="${NOVNC_WEB}/utils/websockify:${PYTHONPATH:-}"
nohup python3 -m websockify --web="${NOVNC_WEB}" "${NOVNC_PORT}" \
    "localhost:${VNC_PORT}" >/tmp/screen${DISPLAY_NUM}_novnc.log 2>&1 &

sleep 2
cat <<EOF

[screen${DISPLAY_NUM}] ready.

  This screen  : http://localhost:${NOVNC_PORT}   (password: ros2edu)
  Main desktop : http://localhost:6902

  Open it in its own browser window and drag it to the monitor you want.

  Put an app here by setting DISPLAY when you start it:

    DISPLAY=:${DISPLAY_NUM} rviz2 -d /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz
    DISPLAY=:${DISPLAY_NUM} gz sim -g

  For a three-screen split, start the simulation headless and place the
  two GUIs yourself:

    ros2 launch edu_bringup simulation.launch.py gui:=false rviz:=false

EOF
