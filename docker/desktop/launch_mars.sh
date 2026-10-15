#!/usr/bin/env bash
# Space module: the rover on Mars - Gazebo, the bridge, and RViz.
source /workspace/docker/desktop/_common.sh

echo "Starting the Mars surface with the six-wheel rover, plus RViz."
echo
echo "Martian gravity (3.72 m/s^2) is set by the world, so the rover"
echo "drives a little more loosely than on Earth - that is correct."
echo
echo "First launch takes 30-60 seconds: Gazebo renders in software, with"
echo "no GPU behind it. The window may be grey until it settles."
echo


# Gazebo and RViz get a screen each rather than overlapping here. The
# simulation itself runs headless; the two GUIs are started separately
# and placed on :3 and :2. If a screen cannot be started the window
# falls back to this one, so a student is never left with nothing.
stop_running_simulation

ensure_screen 3 || true
ensure_screen 2 || true

echo "  Gazebo -> http://localhost:6904"
echo "  RViz   -> http://localhost:6903  (SLAM map builds here)"
echo

cleanup_guis() {
    pkill -f "gz sim -g" 2>/dev/null || true
    pkill -f "rviz2 -d"  2>/dev/null || true
}
trap cleanup_guis EXIT INT TERM

# The GUIs attach to the running simulation, so they are started after it
# has had a moment to come up.
(
    sleep 12
    run_on_screen 3 gz sim -g
    sleep 3
    run_on_screen 2 rviz2 -d         /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz
) &

# SLAM, so the map builds as you drive without needing a second icon.
# rviz:=false: the block above already opened RViz on screen 2, and that
# config carries the Map display.
#
# Started after the GUIs because slam_toolbox activates once and does not
# retry -- if /scan is silent at that moment it sits inert with no error.
(
    sleep 22
    ros2 launch edu_bringup slam.launch.py rviz:=false > /tmp/slam_start.log 2>&1
) &

ros2 launch edu_bringup simulation.launch.py world:=mars robot:=rover gui:=false rviz:=false
hold_open $?
