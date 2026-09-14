# Exercises

Three exercises, one per difficulty step. Each has a skeleton with TODO
markers in `src/edu_exercises/edu_exercises/` and a reference answer in
`src/edu_exercises/solutions/`.

**How to use the solutions:** try for fifteen minutes first. If you are
stuck, run the solution to see the *behaviour* you are aiming at, then go
back to your own code. Read the solution's source last.

**After editing**, if you only changed code inside an existing file:

```bash
ros2 run edu_exercises ex01_publisher      # just re-run it
```

The workspace uses `--symlink-install`, so Python edits take effect
immediately. Rebuild only when you add a file or change `setup.py`:

```bash
/workspace/docker/build_ws.sh
```

---

## Exercise 01 — Your first publisher

**Module:** [01](01-ros2-basics.md) · **Difficulty:** ●○○

Publish a simulated battery level on `/battery` as a
`std_msgs/msg/Float32`, at 1 Hz, starting at 100.0 and dropping by 0.5
each tick.

**File:** [`ex01_publisher.py`](../src/edu_exercises/edu_exercises/ex01_publisher.py)
**Reference:** [`talker.py`](../src/edu_py_examples/edu_py_examples/talker.py)

```bash
ros2 run edu_exercises ex01_publisher
```

**Check your work:**

```bash
ros2 topic list                 # /battery is listed
ros2 topic echo /battery        # counts down from 100.0
ros2 topic hz /battery          # about 1.0
```

**Extensions:**

1. Stop at 0 instead of going negative (`max()` is the tidy way).
2. Log a warning below 20%.
3. Make the drain rate a parameter, and change it live with
   `ros2 param set`.

<details>
<summary>Hint — the message type</summary>

`from std_msgs.msg import Float32`. Same shape as the `String` import in
`talker.py`, with the type name changed.
</details>

---

## Exercise 02 — React to a sensor

**Module:** [02](02-gazebo-and-sensors.md) · **Difficulty:** ●●○

Subscribe to `/scan` and warn whenever something is closer than 1.0 m
directly ahead.

**File:** [`ex02_subscriber.py`](../src/edu_exercises/edu_exercises/ex02_subscriber.py)
**Reference:** [`lidar_monitor.py`](../src/edu_py_examples/edu_py_examples/lidar_monitor.py)

```bash
# Terminal 1
ros2 launch edu_bringup simulation.launch.py
# Terminal 2
ros2 run edu_exercises ex02_subscriber
# Terminal 3 — drive at a wall
ros2 launch edu_bringup teleop.launch.py
```

**Check your work:** the warning fires as you approach a wall and stops
when you back away.

**The two traps in this exercise:**

1. **QoS.** If your callback *never* fires, this is why. Sensors publish
   `BEST_EFFORT`; a default subscriber will not match and receives
   nothing, silently. Copy the `QoSProfile` from `lidar_monitor.py`.
2. **`inf` and `nan`.** `min(msg.ranges)` can return `nan`, and every
   comparison against `nan` is `False` — so your check never fires and
   nothing looks wrong. Filter before comparing.

**Extensions:**

1. Report *which direction* is blocked (left / ahead / right).
2. Make the warning distance a parameter.
3. Publish a `Bool` on `/obstacle_detected` as well as logging.

<details>
<summary>Hint — finding the forward wedge</summary>

For each index, compute `angle = msg.angle_min + i * msg.angle_increment`,
normalise it with `math.atan2(math.sin(a), math.cos(a))`, and keep only
those with `abs(angle) <= math.radians(15)`.
</details>

---

## Exercise 03 — Wall follower (capstone)

**Module:** [04](04-navigation.md) · **Difficulty:** ●●●

Keep the robot driving at a fixed distance from the wall on its left,
using proportional control.

**File:** [`ex03_wall_follower.py`](../src/edu_exercises/edu_exercises/ex03_wall_follower.py)
**Reference:** [`obstacle_avoider.py`](../src/edu_py_examples/edu_py_examples/obstacle_avoider.py)

This is the first exercise that closes a real control loop. It combines
everything: sensor input with correct QoS, a fixed-rate control timer,
parameters, and publishing commands.

**The control law:**

```
error     = desired_distance − measured_left_distance
angular.z = −kp × error
```

Too far from the wall → negative error → positive `angular.z` → turns
left, towards the wall. Too close → turns away.

```bash
ros2 run edu_exercises ex03_wall_follower
```

**Four cases your controller must handle** — the last two are what
separates a working controller from a demo:

| Case | Required behaviour |
|------|--------------------|
| No scan yet | Publish zero. Never run on stale data |
| Wall at the target distance | Drive straight |
| Wall ahead (inside corner) | Stop forward motion, turn right hard |
| No wall on the left (`inf`) | Curve left to go looking for one |

Without the corner case, the robot dutifully regulates its distance to
the left wall while driving nose-first into the one in front.

**Then tune it — this is the real lesson:**

```bash
ros2 param set /wall_follower kp 0.5     # sluggish, drifts off slowly
ros2 param set /wall_follower kp 3.0     # crisp, tracks well
ros2 param set /wall_follower kp 15.0    # unstable, oscillates wildly
```

Find the largest `kp` that still looks smooth. Every feedback controller
in engineering lives on this dial — too little and it never arrives, too
much and it overshoots and rings.

**Always clamp your output:**

```python
angular_z = max(-max_angular, min(max_angular, angular_z))
```

**Extensions:**

1. Follow the wall on the *right* instead. What changes, and why?
2. Add a derivative term: `angular.z = -(kp*error + kd*(error - last_error))`.
   Does it reduce the oscillation at high `kp`?
3. Make the forward speed proportional to clearance ahead — fast in open
   space, slow near obstacles.
4. Detect that the robot has returned to its starting point, and stop.

---

## Going further

Open-ended projects, in rough order of difficulty:

1. **Explorer.** Drive to the largest unexplored area instead of
   wandering. (This is roughly how frontier exploration works.)
2. **A new sensor.** Add a second lidar, or a downward sonar, to
   `model.sdf`. Bridge it, and display it in RViz.
3. **A new world.** Build a maze in `worlds/`. Can your wall follower
   solve it?
4. **Line following.** Use the camera rather than the lidar. Add a
   coloured stripe to the world and follow it with OpenCV.
5. **Multi-robot.** Spawn two EduBots in namespaces and have them avoid
   each other.
