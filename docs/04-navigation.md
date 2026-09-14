# Module 04 — Navigation and control

**Time:** ~3 hours · **Prerequisite:** [Module 03](03-tf-and-odometry.md)

---

This module climbs a ladder. Each rung fixes a limitation of the one
below.

| Rung | Approach | Fixes | Still cannot |
|------|----------|-------|--------------|
| 1 | Teleop | — | Operate without a human |
| 2 | Reactive avoidance | Human in the loop | Reach a goal |
| 3 | Proportional control | Crude on/off behaviour | Know where it is |
| 4 | SLAM | Drift, no map | Plan a route |
| 5 | Nav2 | Everything above | — |

---

## 1. Teleop — a human in the loop

```bash
ros2 launch edu_bringup teleop.launch.py
```

Keys (the window must keep focus):

```
   u  i  o          i / ,   forward / back
   j  k  l          j / l   turn left / right
   m  ,  .          k       STOP
                    q / z   faster / slower
```

Watch what it publishes:

```bash
ros2 topic echo /cmd_vel
```

```yaml
linear:  {x: 0.5, y: 0.0, z: 0.0}    # forward, m/s
angular: {x: 0.0, y: 0.0, z: 0.3}    # turn rate, rad/s
```

**`Twist` is the universal robot command in ROS.** `linear.x` is forward
speed, `angular.z` is turn rate. A differential-drive robot can only use
those two — it cannot slide sideways, so `linear.y` is ignored. Every
controller from here on produces exactly this message.

> **If the robot will not stop:** the teleop window lost focus. Click it
> and press `k`. Gazebo's drive plugin holds the last command it
> received.

---

## 2. Reactive control — sense, think, act

```bash
ros2 run edu_py_examples obstacle_avoider
```

The robot drives itself. Read
[`obstacle_avoider.py`](../src/edu_py_examples/edu_py_examples/obstacle_avoider.py)
— the whole controller is one function:

```python
if front > stop_distance:
    cmd.linear.x = forward_speed        # clear: go
else:
    cmd.linear.x = 0.0                  # blocked: turn
    cmd.angular.z = turn if left > right else -turn
```

Every autonomous robot, from this to a self-driving car, runs the same
loop:

```
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │  SENSE  │ ──▶ │  THINK  │ ──▶ │   ACT   │ ──┐
   └─────────┘     └─────────┘     └─────────┘   │
        ▲                                        │
        └────────────────────────────────────────┘
```

Two design decisions in that file are worth copying into your own code:

**Fixed-rate control.** The loop runs on a 10 Hz timer, not "whenever a
scan arrives". A controller whose rate depends on sensor timing changes
behaviour when the sensor does — and stops commanding entirely if the
sensor dies.

**Fail safe, not fail last.** No data means *stop*:

```python
if self.scan is None:
    self.cmd_pub.publish(Twist())   # all zeros == stop
    return
```

A robot that keeps executing its last command after its sensor fails is a
robot that drives into a wall.

### The limitation

Watch it long enough and it gets stuck oscillating in a corner, and it
revisits the same places forever. It is **purely reactive**: no map, no
memory, no goal. It cannot be asked to go anywhere.

---

## 3. Proportional control

On/off steering is crude. A **proportional controller** steers in
proportion to how wrong things are:

```
error     = desired_distance − measured_distance
angular.z = −kp × error
```

Do [Exercise 03](exercises.md#exercise-03--wall-follower), then run the
solution and tune it live:

```bash
ros2 run edu_exercises sol03_wall_follower

ros2 param set /wall_follower kp 0.5     # sluggish — drifts off slowly
ros2 param set /wall_follower kp 3.0     # crisp — tracks the wall well
ros2 param set /wall_follower kp 15.0    # unstable — oscillates wildly
```

**This trade-off is universal.** Too little gain and the system never
gets there; too much and it overshoots and rings. Every feedback
controller in engineering — cruise control, a thermostat, a drone's
attitude loop — lives on this dial. The P in PID is this term; the I and
D terms address the steady-state error and the ringing you just produced.

Always **clamp** the output:

```python
angular_z = max(-max_angular, min(max_angular, angular_z))
```

Without it, one bad measurement commands an absurd turn rate and the
robot spins on the spot.

---

## 4. SLAM — building a map

Module 03 ended on a chicken-and-egg problem: to build a map you need to
know where you are; to know where you are you need a map.

**SLAM** — Simultaneous Localisation And Mapping — does both at once, by
matching each new laser scan against the map built so far.

```bash
# Terminal 1
ros2 launch edu_bringup simulation.launch.py
# Terminal 2
ros2 launch edu_bringup slam.launch.py
# Terminal 3
ros2 launch edu_bringup teleop.launch.py
```

In RViz, set **Fixed Frame** to `map` once the map appears, and enable
the **Map** display.

Drive slowly around the arena. The map builds as you go:

- **White** — free space, the lidar saw through it
- **Black** — occupied, the lidar hit something
- **Grey** — unknown, never observed

**Watch for loop closure.** When you complete a full circuit of the
arena, the map will visibly *snap* into alignment. The algorithm
recognised a place it had seen before and corrected all the accumulated
drift at once. That single moment is what odometry alone can never do,
and it is worth driving a full lap to see.

Save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

Read [`slam.yaml`](../src/edu_bringup/config/slam.yaml). The parameters
worth knowing:

| Parameter | Effect |
|-----------|--------|
| `resolution: 0.05` | 5 cm per map cell. Finer costs memory and CPU |
| `max_laser_range: 10.0` | Trust readings to here. Beyond the sensor's real range invents detail |
| `minimum_travel_distance` | How far to move before processing a new scan |
| `do_loop_closing: true` | The drift correction described above |

---

## 5. Nav2 — autonomous navigation

Nav2 is the full stack: give it a goal pose and it plans a route, follows
it, and avoids obstacles that were not on the map.

With the simulation and SLAM running:

```bash
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
```

In RViz, use the **2D Goal Pose** tool and click where the robot should
go. It plans a path and drives there.

What is happening underneath:

| Component | Job |
|-----------|-----|
| **Global planner** | Route from here to the goal, using the map |
| **Local planner** | Immediate velocity commands, avoiding what the lidar sees now |
| **Costmaps** | The map, inflated by the robot's radius, so paths keep clearance |
| **Recoveries** | What to do when stuck: back up, spin, clear the costmap |
| **BT Navigator** | A behaviour tree sequencing all of the above |

Nav2 is driven by an **action**, not a topic — because "drive to the
kitchen" takes time, reports progress, and may need cancelling. That is
the third communication pattern from Module 01, finally in its natural
habitat.

Send a goal from the command line:

```bash
ros2 action list
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0}}}}"
```

---

## Exercises

1. Tune `kp` on the wall follower until it tracks smoothly with minimal
   oscillation. Write down the value.
2. Map the entire arena with SLAM and save it. How long did a full lap
   take?
3. Make the obstacle avoider smarter: instead of a fixed turn rate, turn
   harder the closer the obstacle is.
4. Give Nav2 a goal on the far side of the divider wall. Watch the
   planned path. Then drive a box in front of the robot with teleop while
   it navigates, and watch the local planner react.

## Checklist

- [ ] Explain what a `Twist` message commands
- [ ] Write a reactive controller that fails safe
- [ ] Explain the trade-off in choosing a proportional gain
- [ ] Explain what SLAM solves and what loop closure is
- [ ] Explain why navigation is an action and not a topic

---

**You have finished the course.** Where to go next:

- **ros2_control** — the standard way to drive real hardware
- **Behaviour trees** — how Nav2 sequences decisions
- **Perception** — cameras, point clouds, object detection
- **MoveIt 2** — the same ideas applied to robot arms

Put EduBot in a new world, give it a new sensor, or write a controller
that explores the arena unaided. The workspace is yours to break.
