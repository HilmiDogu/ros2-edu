#!/usr/bin/env bash
# Module 01: talker and listener, side by side in one window.
source /workspace/docker/desktop/_common.sh

echo "Starting the talker and the listener together."
echo "The listener prints what the talker publishes on /chatter."
echo "Ctrl-C stops both."
echo

# The listener runs in the background so both share this terminal; the
# trap makes a single Ctrl-C take the pair down rather than orphaning it.
ros2 run edu_py_examples listener &
listener_pid=$!
trap 'kill "${listener_pid}" 2>/dev/null' EXIT INT TERM

ros2 run edu_py_examples talker
hold_open $?
