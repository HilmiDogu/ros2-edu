#!/usr/bin/env bash
# Module 04: SLAM mapping.
source /workspace/docker/desktop/_common.sh

echo "Starting slam_toolbox + its own RViz (Fixed Frame = map)."
echo
echo "Requires the simulation (icon 02, or Moon/Mars) running already."
echo "Drive with icon 03 and watch the map build in the SLAM RViz window."
echo "The map frame is set for you -- the robot stays aligned with the"
echo "scan even after odometry drifts. Drive a full loop to see it snap."
echo

ros2 launch edu_bringup slam.launch.py
hold_open $?
