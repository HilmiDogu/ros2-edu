#!/usr/bin/env bash
# Module 04: SLAM mapping.
source /workspace/docker/desktop/_common.sh

# NOT stop_running_simulation: SLAM attaches to the simulation that is
# already running, and killing it would be exactly wrong.

echo "Starting slam_toolbox."
echo
echo "Requires a simulation (icon 02, 06 or 07) running already."
echo

# rviz:=false, because the simulation icons already opened RViz on
# screen 2 and a second window showing the same topics is just clutter.
# That config carries the Map and TerrainCloud displays, so the map
# appears there as it builds.
#
# One thing to do by hand: set Fixed Frame to 'map' in that RViz once
# the map appears. The simulation starts in 'odom' because no map frame
# exists until SLAM publishes one, and RViz shows an error if its fixed
# frame is missing. Viewing in 'map' is what cancels odometry drift --
# in 'odom' the map appears to slide as the robot's estimate wanders.
echo "In the RViz on screen 2 (http://localhost:6903):"
echo "  set Global Options -> Fixed Frame to 'map' once the map appears."
echo
echo "Then drive with icon 03 and watch it build. A full loop of the"
echo "arena triggers loop closure, and the map visibly snaps straight."
echo

ros2 launch edu_bringup slam.launch.py rviz:=false
hold_open $?
