#!/usr/bin/env bash
# A plain interactive shell with ROS 2 sourced and ready.
source /opt/ros/jazzy/setup.bash
[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash
export GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models
cd /workspace

cat <<'BANNER'
ROS 2 Jazzy. Useful commands:

  ros2 node list                 which nodes are running
  ros2 topic list                which topics exist
  ros2 topic echo /scan          watch messages on a topic
  ros2 topic hz /scan            how fast a topic publishes
  ros2 topic info /scan -v       types and QoS (QoS mismatches hide here)
  ros2 run rqt_graph rqt_graph   the node graph, drawn

  /workspace/docker/build_ws.sh  rebuild after editing code

BANNER

exec bash --login -i
