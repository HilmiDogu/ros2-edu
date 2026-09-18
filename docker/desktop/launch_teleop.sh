#!/usr/bin/env bash
# Module 03: keyboard driving.
source /workspace/docker/desktop/_common.sh

echo "Keyboard teleop. THIS WINDOW must keep focus for keys to register."
echo
echo "   i = forward    , = back    j / l = turn    k = STOP"
echo "   q / z = faster / slower"
echo
echo "Start the simulation first (icon 02) if it is not already running."
echo

ros2 run teleop_twist_keyboard teleop_twist_keyboard
hold_open $?
