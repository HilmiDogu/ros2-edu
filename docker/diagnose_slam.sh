#!/usr/bin/env bash
# Measure SLAM map stability in one world.
#
#   docker exec ros2-gazebo-edu bash /workspace/docker/diagnose_slam.sh <world> [robot]
#
# Drives a fixed sequence of curves with SLAM running and reports the
# map->odom correction after each one. That transform is SLAM's running
# estimate of how far odometry has drifted: it should settle to a small,
# slowly-changing value. Large swings between curves mean the scan
# matcher cannot find a consistent orientation -- which is what makes the
# map appear to spin around the robot in RViz.
#
# Run it once per world and compare. A world whose geometry scan-matches
# well (flat walls) against one that may not (scattered rocks) tells you
# whether the fault is in the robot or in the terrain.
set -eo pipefail

WORLD="${1:-classroom}"
ROBOT="${2:-rover}"
LOGDIR=/tmp/slamdiag
mkdir -p "$LOGDIR"

source /opt/ros/jazzy/setup.bash
source /workspace/install/setup.bash
export GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models

cleanup() {
    pkill -9 -f "gz sim"           2>/dev/null || true
    pkill -9 -f "ros2 launch"      2>/dev/null || true
    pkill -9 -f parameter_bridge   2>/dev/null || true
    pkill -9 -f slam_toolbox       2>/dev/null || true
    pkill -9 -f robot_state_pub    2>/dev/null || true
    pkill -9 -f image_bridge       2>/dev/null || true
    sleep 4
}

echo "=============================================="
echo " SLAM stability: world=${WORLD} robot=${ROBOT}"
echo "=============================================="
cleanup

cd /tmp
nohup ros2 launch edu_bringup simulation.launch.py \
    "world:=${WORLD}" "robot:=${ROBOT}" gui:=false rviz:=false \
    > "${LOGDIR}/sim.log" 2>&1 &

# Wait for the bridge to actually produce a scan rather than guessing a
# sleep: a sim that is still loading reports no data and the whole run
# then measures nothing.
echo -n "waiting for /scan "
for i in $(seq 1 60); do
    if timeout 3 ros2 topic hz /scan --window 3 2>/dev/null | grep -q "average rate"; then
        echo " up after ~$((i*2))s"; break
    fi
    echo -n "."; sleep 2
done

echo "--- what the lidar sees (a wall of 'inf' means nothing to match on) ---"
timeout 8 ros2 run edu_py_examples lidar_monitor 2>&1 | sed -n '2,3p'

nohup ros2 launch edu_bringup slam.launch.py > "${LOGDIR}/slam.log" 2>&1 &
echo -n "waiting for /map "
for i in $(seq 1 40); do
    if timeout 4 ros2 topic echo /map --once --field info >/dev/null 2>&1; then
        echo " up after ~$((i*2))s"; break
    fi
    echo -n "."; sleep 2
done

# map->odom yaw. Identity while SLAM agrees with odometry; it moves when
# SLAM corrects drift. Big jumps = the matcher is lost.
yaw() {
    timeout 6 ros2 run tf2_ros tf2_echo map odom 2>/dev/null \
        | grep -m1 "RPY (degree)" \
        | sed 's/.*\[//; s/\].*//' | awk -F, '{printf "%7.2f", $3}'
}
drive() {
    timeout "$1" ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
        "{linear: {x: $2}, angular: {z: $3}}" >/dev/null 2>&1 || true
}

echo
echo "--- map->odom yaw (degrees) after each leg ---"
printf "  at rest        : %s\n" "$(yaw)"
drive 8 0.35  0.4 ; printf "  curve left     : %s\n" "$(yaw)"
drive 8 0.35 -0.4 ; printf "  curve right    : %s\n" "$(yaw)"
drive 8 0.40  0.5 ; printf "  curve left     : %s\n" "$(yaw)"
drive 6 0.40  0.0 ; printf "  straight       : %s\n" "$(yaw)"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" >/dev/null 2>&1 || true
sleep 4
printf "  settled        : %s\n" "$(yaw)"

echo
echo "A stable map holds these within a few degrees of each other."
echo "Swings of tens of degrees mean the scan matcher is losing lock."
cleanup
