#!/usr/bin/env bash
# Module 04: autonomous obstacle avoidance.
source /workspace/docker/desktop/_common.sh

echo "Starting the obstacle avoider. The robot drives itself."
echo "Requires the simulation (icon 02) to be running already."
echo

ros2 run edu_py_examples obstacle_avoider
hold_open $?
