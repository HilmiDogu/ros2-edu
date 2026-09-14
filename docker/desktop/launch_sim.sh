#!/usr/bin/env bash
# Module 02: the full simulation - Gazebo, the bridge, and RViz.
source /workspace/docker/desktop/_common.sh

echo "Starting Gazebo, the ROS bridge and RViz."
echo
echo "First launch takes 30-60 seconds: Gazebo is rendering in software,"
echo "with no GPU behind it. The window may be grey until it settles."
echo

ros2 launch edu_bringup simulation.launch.py
hold_open $?
