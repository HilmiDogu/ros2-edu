#!/usr/bin/env bash
# Build the colcon workspace inside the container.
#
#   docker exec ros2-gazebo-edu /workspace/docker/build_ws.sh
#
# Safe to re-run: students call this after editing an exercise.
set -eo pipefail

# NOT set -u. The ROS setup scripts reference variables that are unset on
# a first source (AMENT_TRACE_SETUP_FILES and friends), so `set -u` aborts
# the build before colcon is ever reached.
source /opt/ros/jazzy/setup.bash
cd /workspace

# --symlink-install so that edits to Python nodes take effect without a
# rebuild -- students change a file, re-run the launch file, done. This
# is the single biggest tightener of the edit-test loop for this course.
colcon build --symlink-install --event-handlers console_direct+

echo
echo "[build] done. Open a NEW terminal (or run 'source /workspace/install/setup.bash')."
