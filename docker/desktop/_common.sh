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
