# Module 03 — TF2 and odometry

**Time:** ~2 hours · **Prerequisite:** [Module 02](02-gazebo-and-sensors.md)

---

## The problem

The lidar reports "something is 2 metres away, 30° to the left". Two
metres from *what*? The lidar sits 10 cm forward and 9 cm up from the
robot's centre. The robot's centre is somewhere in the room. The room has
its own origin.

Answering "where is that obstacle?" means chaining those relationships
together. Doing it by hand with trigonometry works for two frames and
becomes a bug farm at five.

**TF2** is the library that does it for you. Nodes broadcast the
transforms they know; TF2 assembles them into a tree; any node can then
ask for the transform between *any* two frames, even ones never directly
connected.

## The frames on EduBot

```
map                     the world, fixed. Created by SLAM (Module 04).
 └── odom               where the robot thinks it started.
      └── base_footprint    the robot on the ground
           └── base_link         the robot's body
                ├── lidar_link
                ├── camera_link
                ├── imu_link
                ├── left_wheel
                └── right_wheel
```

Two rules this tree must obey:

1. **One parent per frame.** Two nodes publishing the same
   parent→child transform is the classic "TF tree is broken" bug, and it
   makes RViz flicker between two versions of reality.
2. **It is a tree, not a graph.** No loops.

## 1. See it

With the simulation running:

```bash
ros2 run edu_py_examples tf_listener
```

It prints the robot's pose, obtained by *asking* TF rather than by
subscribing to anything.

For the picture instead of the numbers:

```bash
ros2 run rqt_tf_tree rqt_tf_tree     # live tree diagram
ros2 run tf2_tools view_frames       # writes frames.pdf
```

And in RViz, enable the **TF** display. Every little axis marker is a
frame. It is off by default because with all of them on at once the view
becomes unreadable.

Ask for one transform directly:

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link lidar_link
```

The second never changes — the lidar is bolted on. The first changes
constantly, because that *is* the robot's motion.

---

## 2. Querying TF in code

From [`tf_listener.py`](../src/edu_py_examples/edu_py_examples/tf_listener.py):

```python
self.tf_buffer = Buffer()
self.tf_listener = TransformListener(self.tf_buffer, self)

transform = self.tf_buffer.lookup_transform(
    'odom',                 # target frame — "expressed in"
    'base_link',            # source frame — "the thing I care about"
    rclpy.time.Time())      # Time() == "latest available"
```

Three things that bite beginners:

- **Keep the listener alive.** Assign it to `self`. A `TransformListener`
  in a local variable is garbage-collected and silently stops filling the
  buffer.
- **Expect failure at startup.** The buffer starts empty. Always wrap
  `lookup_transform` in `try`/`except` — the first second of any node's
  life will throw.
- **`use_sim_time` must be `True`** for every node, or lookups fail with
  confusing timing errors. Gazebo's clock and the wall clock are
  different clocks.

### Orientations are quaternions

ROS stores rotation as a quaternion (`x, y, z, w`) — four numbers, no
gimbal lock. For a robot on flat ground, only the heading matters:

```python
def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)
```

---

## 3. Odometry, and why it lies

**Odometry** estimates position by counting wheel rotations. Turn the
left wheel 10 times and the right 10 times, and you moved forward by
10 × circumference.

```bash
ros2 topic echo /odom --once
```

It is cheap, always available, and updates fast. It is also **always
wrong, and gets wronger**.

### See it fail

```bash
ros2 run edu_py_examples square_driver
```

This drives a 2 m square by timing alone — forward for N seconds, turn
for M seconds, four times — and never checks a sensor. That is
**open-loop** control.

Watch in RViz with the **Odometry** display on. The robot will not return
to where it started, and the error grows every lap.

**Why:**

| Cause | Effect |
|-------|--------|
| Wheel slip | Wheel turns, robot does not move — odometry counts it anyway |
| Radius error | 1% wrong radius is 1 cm per metre, forever |
| Timing | Commands do not take effect instantly |
| Integration | Every small error is added to the total and never removed |

That last one is the deep problem. Odometry integrates. An error of one
millimetre per turn is never un-counted — it accumulates without bound.
This is **drift**.

And note what `square_driver` reports at the end: the error *odometry
admits to*. The true error against Gazebo's ground truth is larger,
because odometry cannot see its own drift. **A robot navigating on
odometry alone is always lost — it just does not know it.**

### The fix

You need an external reference: a map, a lidar matching known walls, GPS.
Something that says "no, you are actually *here*". That is Module 04.

---

## 4. The map → odom transform

This is the convention that makes ROS navigation work, and it is worth
understanding before you meet it.

```
map ──▶ odom ──▶ base_link
```

- `odom → base_link` is published by odometry. **Smooth but drifting** —
  never jumps, slowly wrong.
- `map → odom` is published by SLAM or localisation. It is the
  *correction*: "your odometry has drifted 30 cm east, so I am shifting
  the whole odom frame to compensate."

The robot's position in the map is the two chained together. The clever
part: `odom → base_link` stays continuous, so controllers relying on
smooth motion never see a discontinuity, while `map → odom` absorbs every
jump when SLAM corrects itself.

---

## Exercises

1. Run `square_driver` three times. Record the final error each time. Is
   it the same? Why not?
2. Change `side_length` to `4.0`. Does the error double, or worse?
3. In RViz, enable **TF** and watch `lidar_link` move with the robot.
4. Use `tf2_echo` to find the transform from `base_link` to `camera_link`.
   Check it against the URDF.

## Checklist

- [ ] Explain why a robot needs multiple coordinate frames
- [ ] Read a TF tree and spot a missing or duplicated link
- [ ] Look up a transform in Python, handling the startup exception
- [ ] Explain what odometry drift is and why it is unavoidable
- [ ] Explain why `map → odom` exists instead of correcting odom directly

---

**Next:** [Module 04 — Navigation and control](04-navigation.md)
