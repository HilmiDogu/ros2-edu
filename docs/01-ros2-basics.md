# Module 01 — Core ROS 2 concepts

**Time:** ~2 hours · **Prerequisite:** basic Python

---

## Why ROS exists

Imagine building a delivery robot. It needs to read a camera, run object
detection, plan a route, drive motors, monitor a battery, and talk to a
server. Written as one program, that becomes a tangle nobody can test:
change the camera and the route planner stops compiling.

ROS 2 splits it into **nodes** — small independent programs — that talk
over **topics**. Any node can be rewritten, restarted, or moved to
another computer without the others noticing. That is the whole idea, and
everything else is detail.

```
┌──────────┐     /image      ┌──────────┐    /detections   ┌──────────┐
│  camera  │ ──────────────▶ │ detector │ ───────────────▶ │  planner │
└──────────┘                 └──────────┘                  └──────────┘
                                                                 │
                                                          /cmd_vel│
                                                                 ▼
                                                           ┌──────────┐
                                                           │  motors  │
                                                           └──────────┘
```

## The vocabulary

| Term | What it means |
|------|---------------|
| **Node** | One process doing one job |
| **Topic** | A named channel for a stream of messages |
| **Message** | One piece of typed data (`String`, `LaserScan`, `Twist`) |
| **Publisher** | A node that sends on a topic |
| **Subscriber** | A node that receives from a topic |
| **Service** | A request/response call — ask once, get one answer |
| **Action** | A long-running job with feedback, and cancellable |
| **Parameter** | A node's setting, changeable at runtime |

---

## 1. Run the demo

Double-click **"01 Hello ROS 2"** on the desktop, or, in a ROS 2
Terminal:

```bash
ros2 run edu_py_examples talker
```

and in a second terminal:

```bash
ros2 run edu_py_examples listener
```

The talker publishes; the listener prints. They were written separately
and never reference each other.

## 2. Inspect it from outside

This is the part worth internalising. You can examine a running ROS
system without writing any code — which is how you debug robots you did
not build.

```bash
ros2 node list                # which nodes are running
ros2 topic list               # which topics exist
ros2 topic echo /chatter      # watch the messages go past
ros2 topic hz /chatter        # how fast? (should be ~10 Hz)
ros2 topic info /chatter -v   # types, and QoS settings
ros2 interface show std_msgs/msg/String   # what is in this message?
```

See the graph as a picture:

```bash
ros2 run rqt_graph rqt_graph
```

**Try this:** kill the talker with Ctrl-C. The listener keeps waiting,
without error. Restart the talker — messages resume. Nothing needed
restarting. That decoupling is what makes robot systems survivable.

## 3. Publish from the command line

No node needed at all:

```bash
ros2 topic pub /chatter std_msgs/msg/String "{data: 'typed by hand'}"
```

The listener cannot tell the difference. A topic does not care who is on
the other end — which is exactly why you can replace a simulated sensor
with a real one and change nothing else.

---

## 4. Read the code

Open [`talker.py`](../src/edu_py_examples/edu_py_examples/talker.py).
Every ROS 2 Python node has this shape:

```python
rclpy.init(args=args)        # start up the ROS client library
node = MyNode()              # build the node
rclpy.spin(node)             # process callbacks until killed
node.destroy_node()          # clean up
rclpy.shutdown()
```

Note what is **not** there: no `while True` loop. You register callbacks
— a timer, a subscription — and hand control to `rclpy.spin()`, which
calls you back. That is what lets one node serve a timer, three
subscriptions and a service at the same time.

The two lines that matter most:

```python
self.publisher = self.create_publisher(String, 'chatter', 10)
self.timer = self.create_timer(0.1, self.on_timer)
```

That trailing `10` is the **queue depth** — how many messages ROS
buffers if the receiver falls behind. Older messages are dropped once it
fills. For a robot that is usually right: you want the newest sensor
reading, not a backlog of stale ones.

---

## 5. Parameters

Hard-coding a speed means recompiling to change it. Parameters are a
node's settings, adjustable while it runs.

```bash
ros2 run edu_py_examples parameter_demo
```

In another terminal:

```bash
ros2 param list
ros2 param get /parameter_demo publish_rate
ros2 param set /parameter_demo publish_rate 5.0
ros2 param set /parameter_demo message "changed while running"
```

Watch the output react immediately. Read
[`parameter_demo.py`](../src/edu_py_examples/edu_py_examples/parameter_demo.py)
— note that reacting live requires registering
`add_on_set_parameters_callback`. Without it the value updates but the
running timer keeps its old period, which is a genuinely puzzling bug to
meet for the first time.

## 6. Services

Topics broadcast. Services ask a question and wait for an answer.

```bash
ros2 run edu_py_examples service_demo
```

```bash
ros2 service list
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 3, b: 4}"
```

**Choosing between them:**

| Use | When |
|-----|------|
| Topic | Continuous streams — sensor data, velocity commands, state |
| Service | Occasional commands needing an answer — "reset odometry", "take a picture" |
| Action | Long jobs you want feedback on and may cancel — "drive to the kitchen" |

The usual beginner mistake is using a service for streaming data. The
client blocks until the server replies, so a 10 Hz sensor implemented as
a service stalls everything that reads it.

---

## Exercise

Do [Exercise 01](exercises.md#exercise-01--your-first-publisher): publish
a battery level on `/battery`.

```bash
ros2 run edu_exercises ex01_publisher
```

## Checklist

Before moving on, you should be able to:

- [ ] Explain what a node and a topic are, without notes
- [ ] Write a publisher and a subscriber from scratch
- [ ] Use `ros2 topic list`, `echo`, `hz` and `info` to inspect a system
- [ ] Say when to use a topic, a service, or an action
- [ ] Change a running node's behaviour with `ros2 param set`

---

**Next:** [Module 02 — Gazebo and sensors](02-gazebo-and-sensors.md)
