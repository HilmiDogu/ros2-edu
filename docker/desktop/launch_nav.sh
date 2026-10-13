#!/usr/bin/env bash
# Module 09: Nav2 waypoint navigation.
source /workspace/docker/desktop/_common.sh

echo "Starting Nav2 + SLAM + its own RViz (Fixed Frame = map)."
echo
echo "Requires the simulation (icon 06 Moon or 07 Mars, with the rover)"
echo "running already. This does NOT start the simulation itself."
echo
echo "In the RViz window:"
echo "  * 'Nav2 Goal'  -- click and drag a single goal; the rover plans"
echo "                    a path and drives to it, steering around rocks."
echo "  * Waypoint mode -- use the Nav2 panel to queue several goals and"
echo "                    press Start; the rover visits them in order."
echo
echo "The map is built live by SLAM as the rover drives. The worlds are"
echo "open terrain with no walls, so the costmaps roll along with the"
echo "rover rather than mapping a bounded arena."
echo

ros2 launch edu_bringup navigation.launch.py
hold_open $?
