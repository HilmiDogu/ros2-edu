#!/usr/bin/env bash
# Show the rover's camera feed in its own window.
source /workspace/docker/desktop/_common.sh

echo "Opening the rover's camera view (/camera)."
echo
echo "This is what the rover sees looking forward from its mast."
echo "A simulation (icon 02, 06 or 07) must be running already."
echo

# rqt_image_view opens a standalone window and lets you pick the topic from
# a dropdown; pass /camera so it starts on the rover's camera directly.
ros2 run rqt_image_view rqt_image_view /camera
hold_open $?
