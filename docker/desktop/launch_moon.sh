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

ros2 launch edu_bringup simulation.launch.py world:=moon robot:=rover
hold_open $?
