# ROS 2 + Gazebo — an educational workspace

A hands-on introduction to robotics with **ROS 2 Jazzy** and **Gazebo
Harmonic**, built for bachelor students with no prior robotics
experience.

Everything runs in a container and is visible in a **web browser**. There
is no ROS installation, no Linux virtual machine, no X server to
configure, and no difference between Windows, macOS and Linux.

---

## Getting started

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/)
and nothing else.

```bash
git clone <this-repository>
cd ros2-gazebo-edu-max

./docker/up.sh          # macOS / Linux / Git Bash on Windows
.\docker\up.ps1         # Windows PowerShell
```

The first run downloads and builds roughly 4 GB and takes 10–20 minutes.
Later runs start in seconds.

Then open **<http://localhost:6902>** in any browser.
The VNC password is `ros2edu`.

You will land on a Linux desktop with numbered icons. Double-click them
in order — **01 Hello ROS 2** first, then **02 Gazebo World**.

Prefer typing? Double-click **ROS 2 Terminal** (ROS is already sourced)
and run:

```bash
ros2 run edu_py_examples talker              # module 01
ros2 launch edu_bringup simulation.launch.py # module 02
```

### Space: the Moon and Mars

Two extra worlds ship a six-wheel **Perseverance-style rover** on a
lunar or Martian surface, each with that body's real surface gravity
(Moon 1.62, Mars 3.72 m/s²). Double-click **06 Moon Rover** or **07 Mars
Rover**, or type:

```bash
ros2 launch edu_bringup simulation.launch.py world:=moon robot:=rover
ros2 launch edu_bringup simulation.launch.py world:=mars robot:=rover
```

The rover keeps the exact frames, topics and differential-drive
interface as EduBot, so every module (teleop, SLAM, the example nodes)
works with it unchanged. `world:=` and `robot:=` are independent, so you
can also drive EduBot on Mars or the rover in the classroom. To drive it
(icon **03 Teleop**) or map it (icon **04 Navigation**), just start the
Moon or Mars simulation first, then those icons attach to it.

### Seeing the sensor and SLAM messages

With a simulation running, in a **ROS 2 Terminal**:

```bash
ros2 topic list                 # every topic being published
ros2 topic hz /scan             # how fast the lidar publishes
ros2 topic echo /scan --once    # one lidar message
ros2 topic echo /odom --once    # where the robot thinks it is
ros2 topic echo /map --once --field info   # the SLAM map's size/resolution
```

`ros2 run edu_py_examples lidar_monitor` prints a friendly summary of the
lidar instead of the raw message. For a live visual, the Gazebo and RViz
windows in the desktop show the scan, camera, TF tree and the SLAM map as
it builds (set RViz's *Fixed Frame* to `map` once mapping starts).

The [usage guide](docs/usage.md) covers every module, the exercises, and
how to re-run your own code after editing.

To shut everything down:

```bash
docker compose -f docker/docker-compose.yml down
```

Your files are not in the container — they are bind-mounted from this
folder, so edits you make on your own machine (in VS Code, say) appear
inside immediately, and nothing is lost when the container stops.

---

## The modules

Work through these in order. Each builds on the one before.

| # | Module | You will learn |
|---|--------|----------------|
| 01 | [Core ROS 2 concepts](docs/01-ros2-basics.md) | Nodes, topics, publishers and subscribers, services, parameters, the `ros2` CLI |
| 02 | [Gazebo and sensors](docs/02-gazebo-and-sensors.md) | Robot description (SDF/URDF), worlds, the ROS↔Gazebo bridge, lidar, camera, IMU, RViz |
| 03 | [TF2 and odometry](docs/03-tf-and-odometry.md) | Coordinate frames, transform trees, odometry, and why it drifts |
| 04 | [Navigation and control](docs/04-navigation.md) | Teleop, reactive control, proportional control, SLAM, autonomous navigation |

Supporting material:

- [Usage guide](docs/usage.md) — how to start it and run every example
- [Exercises](docs/exercises.md) — the hands-on tasks, with solutions
- [Troubleshooting](docs/troubleshooting.md) — when something does not work
- [Cheat sheet](docs/cheatsheet.md) — the commands worth memorising
- [Instructor guide](docs/instructors.md) — scheduling, assessment, known friction

---

## What is in the box

```
ros2-gazebo-edu-max/
├── docker/                  Container setup — students rarely touch this
│   ├── Dockerfile           ROS 2 Jazzy + Gazebo Harmonic + noVNC desktop
│   ├── docker-compose.yml
│   ├── up.sh / up.ps1       One-command start
│   ├── build_ws.sh          Rebuild the ROS workspace
│   ├── setup_desktop.sh     Reinstall icons after a container rebuild
│   └── desktop/             The double-click launchers on the desktop
│
├── src/
│   ├── edu_bringup/         Simulation: robot, world, launch files, RViz
│   │   ├── models/          EduBot as SDF (for Gazebo) and URDF (for ROS)
│   │   ├── worlds/          The classroom arena
│   │   ├── launch/          simulation, teleop, slam
│   │   ├── config/          slam_toolbox parameters
│   │   └── rviz/            The RViz display setup
│   │
│   ├── edu_py_examples/     Worked, complete, heavily commented nodes
│   │   └── edu_py_examples/
│   │       ├── talker.py            01 — publisher
│   │       ├── listener.py          01 — subscriber
│   │       ├── parameter_demo.py    01 — parameters
│   │       ├── service_demo.py      01 — services
│   │       ├── lidar_monitor.py     02 — reading a sensor
│   │       ├── tf_listener.py       03 — querying the TF tree
│   │       ├── square_driver.py     03 — open-loop control and drift
│   │       └── obstacle_avoider.py  04 — sense–think–act
│   │
│   └── edu_exercises/       Your turn: TODO skeletons
│       ├── edu_exercises/   The files you edit
│       └── solutions/       The reference answers
│
└── docs/                    The module guides
```

## The robot

**EduBot** is deliberately simple: a box, two driven wheels, a caster,
and three sensors.

| Part | Detail |
|------|--------|
| Drive | Differential (two independently driven wheels) |
| Size | 0.40 × 0.25 × 0.10 m, 5 kg |
| Lidar | 360 samples, 360° field of view, 10 m range, 10 Hz |
| Camera | 320 × 240 RGB, 15 Hz |
| IMU | 50 Hz |

You can read its entire description in one sitting:
[`model.sdf`](src/edu_bringup/models/edubot/model.sdf).

## Editing code

Edit files on your own machine with any editor. Then, in the container:

```bash
/workspace/docker/build_ws.sh
```

The workspace is built with `--symlink-install`, so **changes to Python
nodes take effect without rebuilding** — just restart the node. You only
need a rebuild when you add a new file or change `setup.py`.

---

## For instructors

- Roughly 8–12 contact hours of material across the four modules.
- Every module ends with exercises; each exercise has a reference
  solution under `src/edu_exercises/solutions/`.
- The whole environment is pinned and reproducible: every student gets
  byte-identical software, which removes the "works on my machine"
  problem from grading entirely.
- To add a module, add a node to `edu_py_examples`, register it in
  `setup.py`, and add a guide under `docs/`.

## Credits

The Moon and Mars worlds use the **Falling Rock** meshes by OpenRobotics
from [Gazebo Fuel](https://app.gazebosim.org/OpenRobotics), licensed
CC-BY. They are vendored under `src/edu_bringup/models/rock1` and
`rock6` so the worlds load offline.

## Licence

Apache-2.0.
