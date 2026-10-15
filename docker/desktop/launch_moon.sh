#!/usr/bin/env bash
# Space module: the rover on the Moon - Gazebo, the bridge, and RViz.
source /workspace/docker/desktop/_common.sh

echo "Starting the Moon surface with the six-wheel rover, plus RViz."
echo
echo "Lunar gravity (1.62 m/s^2) is set by the world, so the rover drives"
echo "more sluggishly and can slip - that is correct, not a bug."
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
echo "  RViz   -> http://localhost:6903"
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

ros2 launch edu_bringup simulation.launch.py world:=moon robot:=rover gui:=false rviz:=false
hold_open $?
