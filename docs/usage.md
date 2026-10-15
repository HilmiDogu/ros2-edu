# Usage guide

How to start the workspace, run the examples, and work on the exercises.

---

## 1. Start the workspace

From the project folder on your own machine:

```powershell
.\docker\up.ps1          # Windows PowerShell
```

```bash
./docker/up.sh           # macOS, Linux, or Git Bash on Windows
```

This builds the image (first run only, ~4 GB and 10–20 minutes), starts
the container, installs the desktop icons, and builds the ROS workspace.

Then open **<http://localhost:6902>** in any browser.
Password: **`ros2edu`**

You will land on a Linux desktop with numbered icons.

### If the port is taken

```powershell
$env:NOVNC_PORT=6910; .\docker\up.ps1
```

```bash
NOVNC_PORT=6910 ./docker/up.sh
```

Then use that port in the URL instead.

### Stopping

```bash
docker compose -f docker/docker-compose.yml down
```

Your code is bind-mounted from this folder, so nothing you wrote is lost.

---

## 2. Three ways to run things

### A. Desktop icons — start here

Double-click, in order:

| Icon | What it starts |
|------|----------------|
| **01 Hello ROS 2** | talker + listener together in one window |
| **02 Gazebo World** | the simulation — Gazebo and RViz |
| **03 Teleop** | keyboard driving |
| **04 Navigation** | SLAM mapping |
| **05 Obstacle Avoider** | the robot drives itself |
| **ROS 2 Terminal** | a shell with ROS 2 already sourced |

Each opens a terminal that **stays open after the program exits**, so you
can read any error message rather than watching the window vanish.

### B. A terminal inside the desktop — what you will mostly use

Double-click **ROS 2 Terminal**. ROS 2 and the workspace are already
sourced, so commands work immediately:

```bash
ros2 run edu_py_examples talker
ros2 launch edu_bringup simulation.launch.py
```

**Most modules need several terminals at once** — one for the simulation
and one per node. Open as many ROS 2 Terminal windows as you need; they
all share the same ROS graph.

> If you open a terminal another way (right-click the desktop → *Open
> Terminal Here*), source the workspace yourself first:
> `source /workspace/install/setup.bash`

### C. From your own machine — for quick checks

```powershell
docker exec -it ros2-gazebo-edu bash -lc "ros2 topic list"
```

Handy for inspecting a running system. Anything with a window (Gazebo,
RViz, teleop) must run inside the browser desktop.

---

## 2b. The three screens

The simulation icons spread themselves over three browser windows, so
Gazebo, RViz and your terminals each get room:

| URL | Shows |
|-----|-------|
| <http://localhost:6902> | The desktop — icons and terminals |
| <http://localhost:6903> | RViz (display `:2`) |
| <http://localhost:6904> | Gazebo (display `:3`) |

Open each in its own window, drag it to the monitor you want, **F11** to
fullscreen. The extra screens start automatically when a simulation icon
needs them, and the password is `ros2edu` throughout.

Launching something onto a particular screen yourself is just a matter
of setting `DISPLAY` first:

```bash
DISPLAY=:2 rviz2 -d /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz
DISPLAY=:3 gz sim -g
```

To drive the layout entirely by hand, run the simulation headless and
place both GUIs yourself:

```bash
ros2 launch edu_bringup simulation.launch.py gui:=false rviz:=false
DISPLAY=:3 gz sim -g &
DISPLAY=:2 rviz2 -d /workspace/install/edu_bringup/share/edu_bringup/rviz/edubot.rviz &
```

Screens are processes, not settings — they are gone after
`docker compose down`. A simulation icon brings them back, or start one
directly:

```bash
docker exec ros2-gazebo-edu bash /workspace/docker/extra_screen.sh 2
```

Prefer everything on one screen? Run the launch file directly rather
than using an icon: `ros2 launch edu_bringup simulation.launch.py` puts
Gazebo and RViz on whichever display you ran it from.

## 3. Running each module

### Module 01 — core concepts

Two terminals:

```bash
# Terminal 1
ros2 run edu_py_examples talker

# Terminal 2
ros2 run edu_py_examples listener
```

Also worth running:

```bash
ros2 run edu_py_examples parameter_demo    # then: ros2 param set ...
ros2 run edu_py_examples service_demo      # then: ros2 service call ...
```

### Module 02 — simulation and sensors

```bash
# Terminal 1 — leave this running for modules 02, 03 and 04
ros2 launch edu_bringup simulation.launch.py

# Terminal 2
ros2 run edu_py_examples lidar_monitor
```

Gazebo takes **30–60 seconds** on first launch — it renders in software,
with no GPU. A grey window during that time is normal.

Useful arguments:

```bash
ros2 launch edu_bringup simulation.launch.py rviz:=false   # lighter
ros2 launch edu_bringup simulation.launch.py gui:=false    # no 3D window
```

**Seeing the terrain in 3D.** The flat SLAM map has no height in it. The
rover also carries a 3-D lidar publishing a point cloud, which does: in
RViz, **Add** → **PointCloud2**, set its topic to `/points/points`,
**Reliability Policy** to **Best Effort** (it stays empty otherwise) and
**Color Transformer** to **AxisColor** on axis `Z`. Craters and the
ridge then stand out by colour.

### Module 03 — TF and odometry

With the simulation running:

```bash
ros2 run edu_py_examples tf_listener     # where does the robot think it is?
ros2 run edu_py_examples square_driver   # drives a square, reports the error
ros2 run rqt_tf_tree rqt_tf_tree         # the frame tree, drawn
```

### Module 04 — control and navigation

With the simulation running:

```bash
# Drive it yourself
ros2 launch edu_bringup teleop.launch.py

# Or let it drive itself
ros2 run edu_py_examples obstacle_avoider

# Build a map while driving
ros2 launch edu_bringup slam.launch.py
```

For teleop the keys are `i` forward, `,` back, `j`/`l` turn, `k` stop.
**The teleop window must keep focus** — clicking the Gazebo view takes
focus away, and the robot then holds its last command.

---

## 4. Working on the exercises

```bash
# Your version, with the TODOs to fill in
ros2 run edu_exercises ex01_publisher

# The reference answer, to compare behaviour
ros2 run edu_exercises sol01_publisher
```

Edit the files on your own machine — `src/` is bind-mounted, so changes
appear inside the container instantly. Use VS Code or any editor.

**After editing:**

```bash
# Changed an existing .py file? Just run it again — no rebuild needed.
ros2 run edu_exercises ex01_publisher

# Added a NEW file, or edited setup.py? Rebuild first:
/workspace/docker/build_ws.sh
```

The workspace is built with `--symlink-install`, which is what makes
Python edits take effect without rebuilding.

---

## 5. Inspecting a running system

These work on any ROS system, not just this one, and are the real skill
worth taking away:

```bash
ros2 node list                 # which nodes are running
ros2 topic list                # which topics exist
ros2 topic echo /odom          # watch messages
ros2 topic hz /scan            # how fast is it publishing
ros2 topic info /scan -v       # types and QoS — check here when a topic is silent
ros2 run rqt_graph rqt_graph   # the node graph, drawn
```

Sensor topics need a matching QoS to echo:

```bash
ros2 topic echo /scan --qos-reliability best_effort
```

Stop a runaway robot:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

---

## 6. After a container rebuild

The desktop icons and the compiled workspace live inside the container,
not in your project folder. Recreating the container (`docker compose
down` then `up`, or an image rebuild) discards both.

The container rebuilds them for itself when the desktop starts, so
normally you just **wait 30–60 seconds after first connecting and reload
the browser tab**. Check on it with:

```bash
docker exec ros2-gazebo-edu cat /tmp/autostart_setup.log
```

To force it by hand:

```bash
docker exec ros2-gazebo-edu /workspace/docker/setup_desktop.sh
```

Right-click the desktop → **Reload** if the icons do not appear at once.

---

Something not working? See [troubleshooting.md](troubleshooting.md) —
the QoS and "package not found" entries cover the two most common cases.
