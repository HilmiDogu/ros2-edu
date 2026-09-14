# ROS 2 cheat sheet

The commands worth memorising. Print this page.

---

## Inspecting a running system

```bash
ros2 node list                    # which nodes are running
ros2 node info /node_name         # its topics, services, parameters

ros2 topic list                   # which topics exist
ros2 topic list -t                # ...with their message types
ros2 topic echo /topic            # watch messages go past
ros2 topic echo /topic --once     # just one
ros2 topic hz /topic              # publishing rate
ros2 topic bw /topic              # bandwidth
ros2 topic info /topic -v         # types AND QoS  ← check this when a topic is silent

ros2 service list
ros2 action list
```

**Sensor topics need a matching QoS to echo:**

```bash
ros2 topic echo /scan --qos-reliability best_effort
```

`--qos-reliability` is an `echo` flag only. `ros2 topic hz` and `bw` take
no QoS options — they subscribe best-effort already, so they work on
sensor topics unchanged.

## Making things happen

```bash
ros2 run <package> <executable>
ros2 launch <package> <file.launch.py>
ros2 launch <package> <file.launch.py> arg:=value

ros2 topic pub /chatter std_msgs/msg/String "{data: 'hello'}"
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"     # STOP the robot

ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 1, b: 2}"
```

## Parameters

```bash
ros2 param list
ros2 param get /node param_name
ros2 param set /node param_name 5.0
ros2 param dump /node              # save all of them to YAML
```

## Message definitions

```bash
ros2 interface show sensor_msgs/msg/LaserScan
ros2 interface list
```

## TF

```bash
ros2 run tf2_ros tf2_echo odom base_link     # one transform, live
ros2 run tf2_tools view_frames               # writes frames.pdf
ros2 run rqt_tf_tree rqt_tf_tree             # live tree diagram
```

## Graphical tools

```bash
ros2 run rqt_graph rqt_graph          # the node graph
rviz2                                 # visualisation
ros2 run rqt_plot rqt_plot            # plot a numeric topic over time
ros2 run rqt_console rqt_console      # filterable log viewer
```

## Recording and replaying

```bash
ros2 bag record -a                    # record everything
ros2 bag record /scan /odom           # record specific topics
ros2 bag play <bag_directory>
ros2 bag info <bag_directory>
```

Bags are how robotics debugging actually works: record a failure once,
then replay it as often as you need.

## Gazebo

```bash
gz sim <world.sdf>          # launch a world
gz sim -r <world.sdf>       # ...and start it running (not paused)
gz sim -s <world.sdf>       # server only, no GUI
gz topic -l                 # Gazebo topics — NOT the same as ROS topics
gz topic -e -t /topic       # echo a Gazebo topic
gz model --list
```

## Building

```bash
cd /workspace
colcon build --symlink-install         # build everything
colcon build --packages-select edu_py_examples    # build one package
source install/setup.bash               # required in every new terminal

/workspace/docker/build_ws.sh           # the shortcut used here
```

`--symlink-install` means edits to Python nodes take effect **without a
rebuild**. You only need to rebuild when adding a file or changing
`setup.py`.

---

## Message types you will actually use

| Type | Contents |
|------|----------|
| `std_msgs/msg/String` | `data` |
| `std_msgs/msg/Float32` | `data` |
| `geometry_msgs/msg/Twist` | `linear.x` (m/s), `angular.z` (rad/s) |
| `geometry_msgs/msg/Pose` | `position` (x,y,z), `orientation` (quaternion) |
| `sensor_msgs/msg/LaserScan` | `ranges[]`, `angle_min`, `angle_increment` |
| `sensor_msgs/msg/Image` | `data[]`, `width`, `height`, `encoding` |
| `sensor_msgs/msg/Imu` | `orientation`, `angular_velocity`, `linear_acceleration` |
| `nav_msgs/msg/Odometry` | `pose`, `twist`, with covariances |
| `nav_msgs/msg/OccupancyGrid` | `data[]` — the map |

---

## Node boilerplate

```python
import rclpy
from rclpy.node import Node


class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.pub = self.create_publisher(MsgType, 'topic', 10)
        self.sub = self.create_subscription(MsgType, 'topic', self.on_msg, 10)
        self.timer = self.create_timer(0.1, self.on_timer)

    def on_msg(self, msg):
        ...

    def on_timer(self):
        ...


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
```

## Sensor QoS — copy this exactly

Needed for every sensor subscription. Without it you receive nothing, and
get no error explaining why.

```python
from rclpy.qos import (QoSProfile, QoSReliabilityPolicy,
                       QoSHistoryPolicy, QoSDurabilityPolicy)

sensor_qos = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
)
self.create_subscription(LaserScan, 'scan', self.on_scan, sensor_qos)
```

## Reading a laser scan safely

```python
import math

for i, distance in enumerate(msg.ranges):
    angle = msg.angle_min + i * msg.angle_increment
    angle = math.atan2(math.sin(angle), math.cos(angle))   # normalise

    if math.isinf(distance) or math.isnan(distance):
        continue        # ALWAYS filter: nan poisons every comparison
    ...
```
