#!/usr/bin/env bash
# Shared preamble for every desktop launcher.
#
# Desktop entries start with a bare environment: none of the shell
# profile that sets up ROS has run, so each launcher must source it
# explicitly. Without this every icon fails with "ros2: command not
# found", which looks like a broken workspace rather than a missing
# environment.
source /opt/ros/jazzy/setup.bash

if [ -f /workspace/install/setup.bash ]; then
    source /workspace/install/setup.bash
else
    echo "The workspace has not been built yet."
    echo "Run:  /workspace/docker/build_ws.sh"
    echo
    read -rp "Press Enter to close..."
    exit 1
fi

export GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models

# Keep the terminal open after the program exits, so a student can
# actually read the error that killed it.
hold_open() {
    echo
    echo "--- finished (exit code $1) ---"
    read -rp "Press Enter to close this window..."
}
