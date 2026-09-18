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

ros2 launch edu_bringup simulation.launch.py world:=mars robot:=rover
hold_open $?
