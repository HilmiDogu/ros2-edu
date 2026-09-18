# Troubleshooting

Work down the list. Most problems are one of the first five.

---

## Getting started

### The browser shows nothing at localhost:6902

```bash
docker ps                       # is the container running?
docker logs ros2-gazebo-edu     # what did it say?
```

If the container is not listed, it exited. The logs will say why. If it
is running but the page will not load, give it another 30 seconds — the
desktop takes a moment on first start.

### It asks for a password

`ros2edu`. It is set by `VNC_PW` in
[`docker-compose.yml`](../docker/docker-compose.yml).

### "port is already allocated" when starting

Something else on your machine is using port 6902. Pick another one —
no file needs editing:

```bash
NOVNC_PORT=6910 VNC_PORT=5910 docker compose -f docker/docker-compose.yml up -d
```

```powershell
$env:NOVNC_PORT=6910; $env:VNC_PORT=5910; .\docker\up.ps1
```

Then open `http://localhost:6910` instead. To see what is holding the
port:

```bash
docker ps --format '{{.Names}}\t{{.Ports}}'    # another container?
```

```powershell
netstat -ano | Select-String ':6902'           # any process
```

### No icons on the desktop, and `ros2 run` finds nothing

These two always appear together, and they have one cause: the desktop
icons and the compiled workspace live in the **container's** filesystem,
not in the cloned project folder. A container that was started without
`up.sh` / `up.ps1` — or recreated after an image rebuild — has neither.

The container provisions itself on desktop login, so the usual fix is
simply to **wait 30–60 seconds and reload the browser tab**: the icons
appear once the background build finishes. Watch its progress with

```bash
docker exec ros2-gazebo-edu cat /tmp/autostart_setup.log
```

If they still do not appear, do it by hand:

```bash
docker exec ros2-gazebo-edu /workspace/docker/setup_desktop.sh
```

Then right-click the desktop → **Reload**.

If that reports the workspace is built but `ros2 run` still fails, the
build itself is broken — rerun it and read the error:

```bash
docker exec ros2-gazebo-edu /workspace/docker/build_ws.sh
```

> **Older images.** Self-provisioning arrived after the first release. If
> `/tmp/autostart_setup.log` does not exist, your image predates it:
> rebuild with `docker compose -f docker/docker-compose.yml build`, or
> just keep using `setup_desktop.sh` after each start.

### The build fails downloading packages

Usually a network hiccup or a proxy. Just re-run it — Docker caches
completed layers, so it resumes rather than starting over:

```bash
./docker/up.sh
```

Behind a corporate proxy, configure it in Docker Desktop's settings
first.

---

## The simulation

### Gazebo opens but the screen is black or grey

Wait 60 seconds. There is no GPU in the container, so Gazebo renders in
software and the first frame is slow.

If it is still black, confirm the software renderer is active:

```bash
docker exec ros2-gazebo-edu bash -lc 'echo $LIBGL_ALWAYS_SOFTWARE; glxinfo | head -3'
```

`LIBGL_ALWAYS_SOFTWARE` must be `1`.

### Everything is frozen — the robot will not move at all

The world is paused. Press the **play** button at the bottom-left of the
Gazebo window. The launch file passes `-r` to start unpaused, so this
usually means Gazebo was started by hand without it.

### The simulation is painfully slow

Check the real-time factor at the bottom of the Gazebo window. Below
about 0.3 makes the course unpleasant.

In order of effectiveness:

1. **Close RViz** (`rviz:=false`) — it is the most expensive window.
2. **Give Docker more CPU.** Docker Desktop → Settings → Resources.
   Four cores or more.
3. **Turn off the camera display** in RViz.
4. **Loosen the physics step** in
   [`classroom.sdf`](../src/edu_bringup/worlds/classroom.sdf):
   `max_step_size` from `0.001` to `0.004`.

### The robot falls through the floor, or jitters

Almost always bad inertia values in `model.sdf`. Mass and inertia must be
physically plausible and consistent with the geometry.

---

## ROS 2

### "package not found" / "executable not found"

Two causes, in order of likelihood:

```bash
# 1. The workspace is not sourced in THIS terminal
source /workspace/install/setup.bash

# 2. The workspace is not built
/workspace/docker/build_ws.sh
```

Every new terminal needs the workspace sourced. The desktop launchers do
it for you; a shell you opened yourself does it via the profile.

If you added a *new* node file, you must also add it to `setup.py` under
`console_scripts` **and rebuild**. Forgetting that is the usual reason a
brand-new node "does not exist".

### A topic exists but `echo` prints nothing

This is almost always a **QoS mismatch** — the most common silent failure
in ROS 2.

```bash
ros2 topic info /scan -v
```

Compare `Reliability` between the publisher and subscriber. Sensors
publish `BEST_EFFORT`; a default (`RELIABLE`) subscriber will not match
and receives nothing, with no error.

```bash
# echo with a matching profile:
ros2 topic echo /scan --qos-reliability best_effort
```

In code, pass a `QoSProfile` — see
[`lidar_monitor.py`](../src/edu_py_examples/edu_py_examples/lidar_monitor.py).
In RViz, set the display's **Reliability Policy** to **Best Effort**.

### My subscriber callback never fires

In order:

1. **QoS mismatch** — see above.
2. **Topic name.** `ros2 topic list`. Is it `/scan` or `/robot/scan`?
   A leading `/` makes it absolute; without one it is relative to the
   node's namespace.
3. **Message type.** `ros2 topic info /scan`. Must match exactly.
4. **Nothing is publishing.** Check the bridge is running.

### Nothing publishes after Gazebo starts

The bridge is not running, or the topic is not in its list.

```bash
gz topic -l          # the Gazebo side
ros2 topic list      # the ROS side
```

A topic present in the first but not the second is missing from the
bridge configuration in
[`simulation.launch.py`](../src/edu_bringup/launch/simulation.launch.py).

---

## TF and RViz

### RViz shows "No transform from [x] to [odom]"

1. Is `robot_state_publisher` running? `ros2 node list`
2. Is the **Fixed Frame** a frame that exists? Before SLAM runs there is
   no `map` frame — use `odom`.
3. Are transforms arriving? `ros2 topic echo /tf --once`

### The lidar scan appears in the wrong place, or not at all

The scan's `frame_id` does not exist in the TF tree. Check it:

```bash
ros2 topic echo /scan --once --qos-reliability best_effort | grep frame_id
```

It must match a link in the URDF. This is what `<gz_frame_id>` in
`model.sdf` sets.

### TF lookups fail with timing errors

Every node must use simulation time:

```python
parameters=[{'use_sim_time': True}]
```

Gazebo's clock and the wall clock are different clocks. Mixing them
produces "requested time is in the future" and similar.

### The robot model does not appear in RViz

The URDF failed to parse. Test it directly:

```bash
xacro /workspace/src/edu_bringup/models/edubot.urdf.xacro
```

Any error prints here.

---

## Control

### The robot will not stop moving

Gazebo's drive plugin holds the last command it received. Send a zero:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

This is why every controller in this workspace publishes a zero `Twist`
on shutdown.

### Keyboard teleop does nothing

The teleop window must have focus. Clicking Gazebo's 3D view takes focus
away.

### Two things are fighting over the robot

Both are publishing to `/cmd_vel` and the robot receives an interleaved
mess. Stop one. (Real systems solve this with `twist_mux`, which
arbitrates by priority.)

---

## Still stuck?

Gather this before asking:

```bash
ros2 node list
ros2 topic list
ros2 topic info <the topic> -v
docker logs --tail 50 ros2-gazebo-edu
```

Reset everything to a known-good state:

```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
docker exec ros2-gazebo-edu /workspace/docker/build_ws.sh
```

If a rebuild of the workspace is misbehaving, delete the build artefacts
and start clean:

```bash
docker exec ros2-gazebo-edu bash -lc 'rm -rf /workspace/build /workspace/install /workspace/log'
docker exec ros2-gazebo-edu /workspace/docker/build_ws.sh
```
