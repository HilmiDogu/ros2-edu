#!/usr/bin/env bash
# Module 04: SLAM mapping.
source /workspace/docker/desktop/_common.sh

echo "Starting slam_toolbox."
echo
echo "Requires the simulation (icon 02) to be running already."
echo "Drive with icon 03 and watch the map build in RViz."
echo "In RViz, set Fixed Frame to 'map' once the map appears."
echo

ros2 launch edu_bringup slam.launch.py
hold_open $?
