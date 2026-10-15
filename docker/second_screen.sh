#!/usr/bin/env bash
# Open a SECOND browser-visible screen, so Gazebo and RViz can each have
# a monitor instead of fighting over one.
#
#   docker exec ros2-gazebo-edu bash /workspace/docker/second_screen.sh
#
# Then open http://localhost:6903 in another browser window and drag it
# to your other monitor. Password is the same: ros2edu.
#
# WHY A SECOND SCREEN RATHER THAN JUST A BIGGER ONE
#
# One virtual screen can only usefully be as large as the monitor you
# view it on; past that the browser scales it back down. Two independent
# screens can each be fullscreened on a different physical monitor,
# which is what you actually want when a module has you watching the
# simulation, the ROS-side view and a terminal at the same time.
#
# This runs its own Xvnc on display :2 with its own noVNC on 6903,
# separate from the base image's :1 / 6901. It never touches the first
# screen, so a failure here leaves the normal desktop working.
set -eo pipefail

DISPLAY_NUM="${DISPLAY_NUM:-2}"
VNC_PORT="${SECOND_VNC_PORT:-5903}"
NOVNC_PORT="${SECOND_NOVNC_PORT:-6903}"
RES="${SECOND_RESOLUTION:-1920x1080}"

if [ -z "${HOME}" ]; then
    echo "[screen2] HOME is unset; run as the desktop user, not root." >&2
    exit 1
fi

if pgrep -f "Xvnc :${DISPLAY_NUM}" >/dev/null 2>&1; then
    echo "[screen2] display :${DISPLAY_NUM} is already running."
    echo "[screen2] open http://localhost:${NOVNC_PORT}"
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
    echo "[screen2] no VNC password file found - has the desktop started?" >&2
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
echo "[screen2] starting Xvnc on :${DISPLAY_NUM} at ${RES}..."
nohup /usr/bin/Xvnc ":${DISPLAY_NUM}" -depth 24 -geometry "${RES}" \
    -rfbport "${VNC_PORT}" -rfbauth "${PASSWD_FILE}" -pn -ac \
    >/tmp/second_screen_xvnc.log 2>&1 &

sleep 3
if ! pgrep -f "Xvnc :${DISPLAY_NUM}" >/dev/null 2>&1; then
    echo "[screen2] Xvnc failed to start:" >&2
    tail -5 /tmp/second_screen_xvnc.log >&2
    exit 1
fi

export DISPLAY=":${DISPLAY_NUM}"


# A window manager, so windows have title bars and can be moved and
# resized. Without one, apps appear fixed and unmanageable, which
# defeats the point of a second screen.
nohup xfwm4 --display="${DISPLAY}" >/tmp/second_screen_wm.log 2>&1 &
sleep 1

# Paint the root window. Without this the screen is pure black, which is
# indistinguishable from "the second screen is broken" -- the display is
# fine, there is simply nothing drawn on it yet. A solid colour makes it
# obvious the screen is live and waiting for an app.
xsetroot -solid "#1d3a52" 2>/dev/null || true

# A terminal, so the screen is useful the moment you open it rather than
# requiring you to go back to screen 1 to launch anything. xfce4-terminal
# rather than xterm: xterm fails here with a missing-font error.
if command -v xfce4-terminal >/dev/null 2>&1; then
    nohup xfce4-terminal --geometry=100x24+40+40 \
        --title="screen 2 - DISPLAY=:${DISPLAY_NUM}" \
        >/tmp/second_screen_term.log 2>&1 &
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
    echo "[screen2] noVNC web assets not found." >&2
    echo "[screen2] The raw VNC port ${VNC_PORT} still works in a native viewer." >&2
    exit 0
fi

# `python3 -m websockify`, matching how the base image launches its own.
# There is no websockify binary on PATH and the module is not installed
# system-wide: it ships inside the noVNC tree, so PYTHONPATH has to point
# at it or the import fails with "No module named websockify".
export PYTHONPATH="${NOVNC_WEB}/utils/websockify:${PYTHONPATH:-}"
nohup python3 -m websockify --web="${NOVNC_WEB}" "${NOVNC_PORT}" \
    "localhost:${VNC_PORT}" >/tmp/second_screen_novnc.log 2>&1 &

sleep 2
cat <<EOF

[screen2] ready.

  Second screen : http://localhost:${NOVNC_PORT}   (password: ros2edu)
  First screen  : http://localhost:6902

  Put an app on the second screen by setting DISPLAY when you start it:

    # first screen: the simulation, without RViz
    ros2 launch edu_bringup simulation.launch.py rviz:=false

    # second screen: RViz with a whole monitor to itself
    DISPLAY=:${DISPLAY_NUM} rviz2 -d /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz

EOF
