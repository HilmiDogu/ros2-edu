# Module 02 — Gazebo and sensors

**Time:** ~3 hours · **Prerequisite:** [Module 01](01-ros2-basics.md)

---

## What a simulator is for

Real robots are slow to test, expensive to break, and impossible to
rewind. A simulator gives you physics, sensors and a world you can reset
in a second — so you can crash a hundred times before lunch.

**Gazebo** simulates rigid-body physics, and it *renders* what the
sensors would see: a simulated lidar really does trace rays against the
world geometry. The data your code receives has the same shape and the
same failure modes as data from real hardware.

## 1. Run it

Double-click **"02 Gazebo World"**, or:

```bash
ros2 launch edu_bringup simulation.launch.py
```

Two windows open: **Gazebo** (the physics and the 3D world) and **RViz**
(what the *robot* knows). The distinction matters and is the single most
useful idea in this module:

> **Gazebo shows the truth. RViz shows the robot's beliefs.**

Gazebo knows exactly where the robot is, because it put it there. RViz
draws only what the robot has measured and computed. When those two
pictures disagree, you have found a bug — or, in Module 03, drift.

First launch takes 30–60 seconds. There is no GPU in the container, so
Gazebo renders in software.

---

## 2. What just started

Open
[`simulation.launch.py`](../src/edu_bringup/launch/simulation.launch.py).
Five things had to start:

| # | Component | Job |
|---|-----------|-----|
| 1 | `gz sim` | Physics and the 3D world |
| 2 | `create` | Spawns EduBot into the running world |
| 3 | `parameter_bridge` | Copies messages between Gazebo and ROS 2 |
| 4 | `robot_state_publisher` | Broadcasts the robot's transform tree |
| 5 | `rviz2` | Visualises what ROS knows |

A **launch file** exists because starting five programs by hand, in the
right order, with the right arguments, every time, is intolerable.

## 3. The bridge — the key idea

Gazebo and ROS 2 are **two separate messaging systems**. Gazebo uses
Gazebo Transport; ROS 2 uses DDS. They do not talk to each other.

The `parameter_bridge` is the only thing connecting them:

```
   Gazebo Transport            ROS 2 (DDS)
   ────────────────            ───────────
   /scan   (gz.msgs.LaserScan) ──▶ /scan   (sensor_msgs/msg/LaserScan)
   /odom   (gz.msgs.Odometry)  ──▶ /odom   (nav_msgs/msg/Odometry)
   /cmd_vel (gz.msgs.Twist)    ◀── /cmd_vel (geometry_msgs/msg/Twist)
```

The syntax, from the launch file:

```
/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan
     ▲                         ▲
     │                         └── direction
     └── ROS type              
```

**Direction operators — memorise these:**

| Symbol | Direction | Used for |
|--------|-----------|----------|
| `@` | both ways | rarely; costs bandwidth in both directions |
| `[` | Gazebo → ROS | sensor data flowing *out* |
| `]` | ROS → Gazebo | commands flowing *in* |

Getting the bracket backwards is a common and confusing mistake: the
topic exists, `ros2 topic list` shows it, and nothing ever arrives.

**See it yourself:**

```bash
ros2 topic list              # the ROS side
gz topic -l                  # the Gazebo side (different tool!)
```

Topics on the Gazebo side that are not in the bridge simply do not exist
as far as ROS is concerned.

---

## 4. Where the robot comes from

The robot is described **twice**, and students reasonably find this
confusing. The reason:

| File | Format | Read by | Describes |
|------|--------|---------|-----------|
| [`model.sdf`](../src/edu_bringup/models/edubot/model.sdf) | SDF | Gazebo | Physics: mass, inertia, friction, sensors, plugins |
| [`edubot.urdf.xacro`](../src/edu_bringup/models/edubot.urdf.xacro) | URDF | ROS | Kinematics: the link/joint tree for TF and RViz |

Gazebo simulates from the SDF. ROS reasons about the robot from the URDF.
**If you change a dimension in one, change it in the other**, or the
robot RViz draws will drift away from the robot Gazebo simulates.

Open `model.sdf` and read it top to bottom. The structure:

- **`<link>`** — a rigid body. Has `<visual>` (what you see),
  `<collision>` (what physics uses — often simpler), and `<inertial>`
  (mass and how it is distributed).
- **`<joint>`** — connects two links. `revolute` rotates, `fixed` does
  not move.
- **`<sensor>`** — a lidar, camera or IMU attached to a link.
- **`<plugin>`** — the code that makes it behave.

### Inertia matters more than you expect

```xml
<inertial>
  <mass>5.0</mass>
  <inertia><ixx>0.0302</ixx> ... </inertia>
</inertial>
```

Wrong inertia is the top cause of robots that jitter, sink through the
floor, or refuse to drive straight. It is not a detail you can leave
approximate.

### The plugins do the work

```xml
<plugin filename="gz-sim-diff-drive-system"
        name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <wheel_separation>0.32</wheel_separation>
  <wheel_radius>0.07</wheel_radius>
```

`DiffDrive` subscribes to `cmd_vel`, converts a velocity command into
wheel rotations, and publishes odometry. Without it the robot is a
sculpture.

Note `wheel_separation` and `wheel_radius`: the plugin uses these to
convert "drive forward at 0.4 m/s" into wheel speeds. If they do not
match the geometry, odometry is wrong from the first millimetre — a
classic real-world calibration bug, reproduced here honestly.

---

## 5. The sensors

### Lidar

```bash
ros2 topic echo /scan --once
```

A wall of numbers. The structure:

```yaml
angle_min: -3.14159      # first ray points backwards
angle_max: 3.14159       # last ray, full circle
angle_increment: 0.0175  # 1 degree between rays
range_min: 0.12          # closer than this is not measurable
range_max: 10.0          # further than this reads as inf
ranges: [1.2, 1.3, inf, inf, 0.8, ...]   # 360 distances, in metres
```

**A LaserScan is not a picture.** It is one array of distances plus the
angles it spans. To know where reading `i` points:

```python
angle = msg.angle_min + i * msg.angle_increment
```

**The trap:** `ranges` contains `inf` (nothing in range) and can contain
`nan` (invalid). `min(msg.ranges)` will happily return `nan`, and every
comparison against `nan` is `False` — so your obstacle check silently
never fires. Filter first, always:

```python
if math.isinf(d) or math.isnan(d):
    continue
```

Run the worked example and watch the numbers change as you drive:

```bash
ros2 run edu_py_examples lidar_monitor
```

### Camera and IMU

```bash
ros2 topic echo /camera_info --once
ros2 topic echo /imu --once
```

In RViz, tick the **Camera** display (off by default — decoding video
over a software-rendered remote desktop is the most expensive thing in
this workspace).

---

## 6. QoS — the silent failure

This costs students more time than anything else in ROS 2, so it gets its
own section.

**Quality of Service** settings must be *compatible* between publisher
and subscriber. If they are not, the connection silently does not form.
No error. No warning. The topic appears in `ros2 topic list`. You just
never receive anything.

| Profile | Meaning | Used by |
|---------|---------|---------|
| `RELIABLE` | Re-send until delivered | Commands, services |
| `BEST_EFFORT` | Send once, accept loss | Sensor data |

A `RELIABLE` **subscriber** cannot receive from a `BEST_EFFORT`
**publisher**. Sensors publish `BEST_EFFORT` — so a subscriber written
with the default settings gets nothing from `/scan`.

**Diagnose it:**

```bash
ros2 topic info /scan -v
```

Read the `Reliability` line under both the publisher and the subscriber.

**Fix it:**

```python
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

sensor_qos = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)
self.create_subscription(LaserScan, 'scan', self.on_scan, sensor_qos)
```

RViz displays have the same setting, in the display's **Topic →
Reliability Policy** dropdown.

---

## 7. Break it on purpose

The fastest way to understand what each piece does is to remove it.

| Try this | What happens | Why |
|----------|--------------|-----|
| `rviz:=false`, then open RViz yourself | No displays configured | RViz config is just a file |
| Kill `parameter_bridge` | ROS topics stop; Gazebo keeps running | The bridge is the only link |
| Kill `robot_state_publisher` | Robot vanishes from RViz, still fine in Gazebo | RViz needs TF to place it |
| Delete the `Sensors` plugin from the world | Lidar publishes nothing | That plugin drives all sensors |
| Change `wheel_radius` to `0.2` in `model.sdf` | Odometry over-reports distance | Plugin maths uses this value |

Restore the file afterwards with `git checkout`.

---

## Exercise

Do [Exercise 02](exercises.md#exercise-02--react-to-a-sensor): warn when
an obstacle is close.

## Checklist

- [ ] Explain why Gazebo and RViz show different things
- [ ] Explain what the bridge does, and read the `[` / `]` syntax
- [ ] Find where a robot's wheel radius is defined
- [ ] Read a `LaserScan`, and filter `inf`/`nan` correctly
- [ ] Diagnose a QoS mismatch with `ros2 topic info -v`

---

**Next:** [Module 03 — TF2 and odometry](03-tf-and-odometry.md)
