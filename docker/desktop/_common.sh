#!/usr/bin/env bash
# Shared preamble for every desktop launcher.
#
# Desktop entries start with a bare environment: none of the shell
# profile that sets up ROS has run, so each launcher must source it
# explicitly. Without this every icon fails with "ros2: command not
# found", which looks like a broken workspace rather than a missing
# environment.
source /opt/ros/jazzy/setup.bash

# Build on demand rather than just complaining. The autostart hook
# normally has this done before anyone can click an icon, but a student
# who is quick off the mark -- or whose container was started without
# up.sh -- would otherwise meet a dead end on their first double-click.
if [ ! -f /workspace/install/setup.bash ]; then
    echo "The ROS workspace has not been built yet. Building it now."
    echo "This takes about 30 seconds, and only happens once."
    echo
    if ! /workspace/docker/build_ws.sh; then
        echo
        echo "The build FAILED. The output above says why."
        read -rp "Press Enter to close..."
        exit 1
    fi
    echo
fi

source /workspace/install/setup.bash

export GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models

# Keep the terminal open after the program exits, so a student can
# actually read the error that killed it.
hold_open() {
    echo
    echo "--- finished (exit code $1) ---"
    read -rp "Press Enter to close this window..."
}

# --- One simulation at a time -------------------------------------------
# Clicking a simulation icon while another is running starts a SECOND of
# everything: two gz servers, two bridges, two RViz. They publish to the
# same topics and the GUI may attach to either, so the symptom is not an
# obvious crash -- it is edits that appear not to take effect, because
# you are looking at the older world. That has cost several debugging
# rounds, so the launchers now clear the field before starting.
#
# Ordered deliberately: the ros2 launch supervisor first, or it restarts
# the children we are about to kill.
stop_running_simulation() {
    if ! pgrep -f "gz sim|parameter_bridge|rviz2" >/dev/null 2>&1; then
        return 0
    fi

    echo "Stopping a simulation that is already running..."
    pkill -f "ros2 launch edu_bringup" 2>/dev/null || true
    sleep 2
    pkill -f "gz sim"          2>/dev/null || true
    pkill -f parameter_bridge  2>/dev/null || true
    pkill -f image_bridge      2>/dev/null || true
    pkill -f robot_state_pub   2>/dev/null || true
    pkill -f rviz2             2>/dev/null || true
    pkill -f slam_toolbox      2>/dev/null || true
    sleep 2

    # SIGKILL whatever ignored the polite request.
    pkill -9 -f "gz sim"         2>/dev/null || true
    pkill -9 -f parameter_bridge 2>/dev/null || true
    pkill -9 -f rviz2            2>/dev/null || true
    sleep 2

    local left
    left=$(pgrep -cf "gz sim" 2>/dev/null || echo 0)
    if [ "${left}" -gt 0 ]; then
        echo "  warning: ${left} Gazebo process(es) would not die."
        echo "  If the simulation looks wrong, restart the container:"
        echo "    docker compose -f docker/docker-compose.yml restart"
    else
        echo "  done."
    fi
    echo
}

# --- Multi-screen placement ---------------------------------------------
# Gazebo and RViz together do not fit comfortably on one screen, so the
# simulation launchers put them on their own displays: RViz on :2
# (http://localhost:6903) and Gazebo on :3 (http://localhost:6904).
#
# Screens are started on demand rather than at boot, so nothing is spent
# on them until something needs one -- and a container restart does not
# leave a student with icons that silently open windows nowhere.

# ensure_screen <n> -- start display :n if it is not already up.
# Liveness is probed with `xrandr -q`: it is read-only and correctly
# reports a dead display, unlike `xsetroot -q`, which is not a real flag
# and fails even against a running screen.
# Returns 0 if the display is usable afterwards, 1 if not.
ensure_screen() {
    local n="$1"
    if DISPLAY=":${n}" xrandr -q >/dev/null 2>&1; then
        return 0        # already running and accepting clients
    fi

    # A dead screen can leave its socket behind; the start script's own
    # "already running" check would then pass while every client is
    # refused. Clear the stale entry before trying.
    if ! pgrep -f "Xvnc :${n}" >/dev/null 2>&1; then
        rm -f "/tmp/.X11-unix/X${n}" "/tmp/.X${n}-lock" 2>/dev/null || true
    fi

    echo "Starting screen ${n} (http://localhost:690$((n+1))) ..."
    bash /workspace/docker/extra_screen.sh "${n}" >/dev/null 2>&1 || true

    # Verify rather than assume: a screen that failed to start must not
    # silently swallow the window we are about to place on it.
    local i
    for i in $(seq 1 15); do
        if DISPLAY=":${n}" xrandr -q >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done

    echo "  could not start screen ${n}; using this screen instead." >&2
    return 1
}

# run_on_screen <n> <command...> -- run a GUI on display :n, falling back
# to the current display if that screen cannot be started.
run_on_screen() {
    local n="$1"; shift
    if ensure_screen "${n}"; then
        DISPLAY=":${n}" "$@" &
    else
        "$@" &
    fi
}
