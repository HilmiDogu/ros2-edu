# ROS 2 + Gazebo — an educational workspace

A hands-on introduction to robotics with **ROS 2 Jazzy** and **Gazebo
Harmonic**, built for bachelor students with no prior robotics
experience.

Everything runs in a container and is visible in a **web browser**. There
is no ROS installation, no Linux virtual machine, no X server to
configure, and no difference between Windows, macOS and Linux.

| Gazebo — the rover on the Moon | RViz — the SLAM map and laser scan |
|---|---|
| ![The six-wheel rover on the cratered Moon terrain in Gazebo, with scattered boulders](docs/images/gazebo-moon.png) | ![RViz showing the SLAM occupancy map building, the rover and its laser scan in the map frame](docs/images/rviz-slam.png) |

*Both windows run side by side on the in-browser desktop. Gazebo is the
simulated world; RViz shows what the robot senses and the map it builds.*

---

## Getting started

You need [Docker](https://www.docker.com/products/docker-desktop/) and
nothing else — no ROS, no Linux install, no Python.

**Don't have Docker yet?** Follow
[docs/installing-docker.md](docs/installing-docker.md) first — step-by-step
for Windows, Linux and macOS, including the WSL memory limit Windows
users must set. Do it the day before, not at the start of the session:
the first run downloads several GB.

Already have it? Make sure Docker is **running** before you start.

### 1. Clone and start

```powershell
git clone <this-repository>
cd ros2-gazebo-edu-max

.\docker\up.ps1          # Windows PowerShell
```
> **PowerShell refuses to run the script?** If you see *"cannot be
> loaded because running scripts is disabled on this system"*, allow
> scripts for this window only, then run it again:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
> ```

```bash
git clone <this-repository>
cd ros2-gazebo-edu-max

./docker/up.sh           # macOS, Linux, or Git Bash on Windows
```

That one command does everything: builds the image, starts the
container, installs the desktop icons, and builds the ROS workspace.

The first run downloads roughly 4 GB and takes **10–20 minutes**. Later
runs start in seconds.

> **Port already in use?** Another container may hold 6902. Pick your own:
> `$env:NOVNC_PORT=6910; .\docker\up.ps1` (PowerShell) or
> `NOVNC_PORT=6910 ./docker/up.sh` (bash), then use that port below.

> **On Windows, do this once first.** Docker runs inside a WSL2 virtual
> machine that will otherwise claim up to half your RAM and stall the
> simulation. Copy the supplied limits and restart WSL:
>
> ```powershell
> copy docker\wslconfig-example.ini $env:USERPROFILE\.wslconfig
> wsl --shutdown
> ```
>
> Then restart Docker Desktop. Skipping this is the usual reason noVNC
> freezes mid-simulation — see
> [troubleshooting](docs/troubleshooting.md#windows-novnc-freezes-and-vmmemwsl-eats-all-the-memory).

### 2. Open the desktop

Go to **<http://localhost:6902>** in any browser.
The VNC password is **`ros2edu`**.

You will land on a Linux desktop with numbered icons.

### 3. Click an icon

| Icon | What it starts | Needs a simulation running first? |
|------|----------------|-----------------------------------|
| **01 Hello ROS 2** | Talker + listener in one window — the pub/sub demo | No |
| **02 Gazebo World** | EduBot in the classroom, with RViz, lidar and camera | No — this *is* the simulation |
| **03 Teleop** | Keyboard driving | **Yes** — 02, 06 or 07 |
| **04 Navigation** | SLAM mapping with slam_toolbox | **Yes** — 02, 06 or 07 |
| **05 Obstacle Avoider** | The robot drives itself, avoiding obstacles | **Yes** — 02, 06 or 07 |
| **06 Moon Rover** | Six-wheel rover on open Moon terrain — hills, drivable craters, scattered boulders, gravity 1.62 m/s² | No — this *is* the simulation |
| **07 Mars Rover** | Six-wheel rover on open Mars terrain — same, gravity 3.72 m/s² | No — this *is* the simulation |
| **ROS 2 Terminal** | A shell with ROS 2 and the workspace already sourced | No |

**Start with 01, then 02.** Icons 03–05 attach to a simulation that is
already running, so start 02 (or 06 / 07) first and leave it open.

Each icon opens a terminal that **stays open after the program exits**,
so you can read any error rather than watching the window vanish.

> Gazebo takes **30–60 seconds** to appear on first launch. There is no
> GPU in the container, so it renders in software. A grey window during
> that time is normal.

### Three screens, one per window

Gazebo, RViz and a terminal do not fit comfortably together on one
screen, so **02 Gazebo World**, **06 Moon Rover** and **07 Mars Rover**
spread themselves across three:

| Open in your browser | Shows |
|----------------------|-------|
| <http://localhost:6902> | The desktop: icons and terminals |
| <http://localhost:6903> | **RViz** |
| <http://localhost:6904> | **Gazebo** |

Open each in its own browser window and drag it to whichever monitor you
want, then press **F11** to fullscreen it. One double-click sets all
three up — the extra screens start themselves when an icon needs them.

The other icons (teleop, navigation, the camera) stay on the main
desktop, since each is a single window.

> **Only see 6902?** The extra screens start on demand, so they exist
> only once a simulation icon has been clicked. If one still will not
> load, start it by hand:
>
> ```powershell
> docker exec ros2-gazebo-edu bash /workspace/docker/extra_screen.sh 2
> docker exec ros2-gazebo-edu bash /workspace/docker/extra_screen.sh 3
> ```

To put something on a particular screen yourself, set `DISPLAY` when you
launch it:

```bash
DISPLAY=:2 rviz2        # screen 2, port 6903
DISPLAY=:3 gz sim -g    # screen 3, port 6904
```

Screens are processes, not settings: they do not survive
`docker compose down`. Clicking a simulation icon brings them back.

### Prefer typing?

Double-click **ROS 2 Terminal** — ROS is already sourced — and run:

```bash
ros2 run edu_py_examples talker                 # module 01
ros2 launch edu_bringup simulation.launch.py    # module 02
ros2 run teleop_twist_keyboard teleop_twist_keyboard   # drive it
```

Most modules want **several terminals at once**: one for the simulation,
one per node. Open as many ROS 2 Terminal windows as you need — they all
share the same ROS graph.

### If the desktop has no icons

The icons and the compiled workspace live inside the **container**, not
in the cloned folder, so a container started without `up.sh` / `up.ps1`
has neither. The container installs them itself on desktop login, so
usually you just wait ~30 seconds and **reload the browser tab**.

To force it:

```bash
docker exec ros2-gazebo-edu /workspace/docker/setup_desktop.sh
```

Then right-click the desktop → **Reload**. One gotcha: a `git pull` that
adds a new icon only reaches a *running* container after you rerun that
command (or restart the container).

### A worked example: drive the rover on Mars, and map it

1. Double-click **07 Mars Rover**. Wait for Gazebo (~40 s).
2. Double-click **03 Teleop**. **Keep that window focused** and press
   `i` to drive forward, `j` / `l` to turn, `k` to stop.
3. Double-click **04 Navigation** to start SLAM, and watch the map build
   in RViz as you drive.

> **Two things that catch everyone.** In RViz, set **Fixed Frame** to
> `map` once mapping starts — leaving it on `odom` makes the map appear
> to slide along with the robot. And if the robot will not stop, the
> teleop window lost focus (clicking Gazebo steals it): click it again
> and press `k`.

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

**The rover's eye view** is already in RViz: the *Image* display (bottom
left) shows the `/camera` feed — what the rover sees looking forward from
its mast. It is live as you drive. To see only that, run
`ros2 run rqt_image_view rqt_image_view /camera` in a ROS 2 Terminal.

The [usage guide](docs/usage.md) covers every module, the exercises, and
how to re-run your own code after editing.

### Stopping and restarting

```bash
docker compose -f docker/docker-compose.yml down     # stop
docker compose -f docker/docker-compose.yml up -d    # start again
```

Your files are not in the container — they are bind-mounted from this
folder, so edits you make on your own machine (in VS Code, say) appear
inside immediately, and nothing is lost when the container stops.

The icons and the compiled workspace *do* live in the container, but it
rebuilds them for itself on the next desktop login, so restarting costs
you nothing but the ~30 seconds of that first build.

---

## The modules

Work through these in order. Each builds on the one before.

| # | Module | You will learn |
|---|--------|----------------|
| 00 | [**Before you start**](docs/00-first-session.md) | What Linux, Docker, ROS 2 and Gazebo are, a first terminal, and twenty minutes of driving — **start here if any of those words are new** |
| 01 | [Core ROS 2 concepts](docs/01-ros2-basics.md) | Nodes, topics, publishers and subscribers, services, parameters, the `ros2` CLI |
| 02 | [Gazebo and sensors](docs/02-gazebo-and-sensors.md) | Robot description (SDF/URDF), worlds, the ROS↔Gazebo bridge, lidar, camera, IMU, RViz |
| 03 | [TF2 and odometry](docs/03-tf-and-odometry.md) | Coordinate frames, transform trees, odometry, and why it drifts |
| 04 | [Navigation and control](docs/04-navigation.md) | Teleop, reactive control, proportional control, SLAM, autonomous navigation |

Supporting material:

- [Installing Docker](docs/installing-docker.md) — Windows, Linux and macOS, from scratch
- [First session](docs/00-first-session.md) — for students new to Linux, Docker or the terminal
- [Usage guide](docs/usage.md) — how to start it and run every example
- [Exercises](docs/exercises.md) — the hands-on tasks, with solutions
- [Troubleshooting](docs/troubleshooting.md) — when something does not work
- [Cheat sheet](docs/cheatsheet.md) — the commands worth memorising

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
│   ├── autostart_setup.sh   Runs on desktop login: icons + first build
│   └── desktop/             The double-click launchers on the desktop
│
├── src/
│   ├── edu_bringup/         Simulation: robots, worlds, launch, RViz
│   │   ├── models/          Each robot twice: SDF (Gazebo) + URDF (ROS)
│   │   │   ├── edubot/      Two-wheel classroom robot
│   │   │   ├── rover/       Six-wheel Perseverance-style rover
│   │   │   └── rock1, rock6, ground/   Terrain assets for Moon/Mars
│   │   ├── worlds/          classroom.sdf, moon.sdf, mars.sdf
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

## The robots

Two robots, **the same interface**. Both publish `/scan`, `/odom`,
`/imu`, `/camera` and the same TF frames, and both take `/cmd_vel`, so
every module and example node works with either one unchanged.

### EduBot — the teaching robot

Deliberately simple: a box, two driven wheels, a caster, three sensors.

| Part | Detail |
|------|--------|
| Drive | Differential (two independently driven wheels) |
| Size | 0.40 × 0.25 × 0.10 m, 5 kg |
| Lidar | 360 samples, 360° field of view, 10 m range, 10 Hz |
| Camera | 320 × 240 RGB, 15 Hz |
| IMU | 50 Hz |

You can read its entire description in one sitting:
[`model.sdf`](src/edu_bringup/models/edubot/model.sdf).

### Rover — the six-wheel Perseverance-style rover

Same sensors and the same differential-drive interface, but six driven
wheels, a rocker-bogie-style deck and a camera mast.

| Part | Detail |
|------|--------|
| Drive | Six-wheel skid steer, all wheels powered |
| Size | 0.60 × 0.40 × 0.12 m, 8 kg |
| Sensors | Identical to EduBot (lidar on the deck, camera on the mast) |

### Robots and worlds are independent

`world:=` and `robot:=` are separate choices, so you can drive EduBot on
Mars or the rover in the classroom:

```bash
ros2 launch edu_bringup simulation.launch.py world:=mars robot:=rover
ros2 launch edu_bringup simulation.launch.py world:=moon robot:=edubot
```

| World | Gravity | Contains |
|-------|---------|----------|
| `classroom` | 9.8 m/s² | Walled 12 × 12 m arena with pillars and a divider |
| `moon` | 1.62 m/s² | Lunar regolith, craters, rocks, a ridge |
| `mars` | 3.72 m/s² | Martian surface, rocks, a ridge |

## Editing code

Edit files on your own machine with any editor. Then, in the container:

```bash
/workspace/docker/build_ws.sh
```

The workspace is built with `--symlink-install`, so **changes to Python
nodes take effect without rebuilding** — just restart the node. You only
need a rebuild when you add a new file or change `setup.py`.

---

## How long it takes

Roughly 8–12 hours across the four modules, plus the exercises. There is
no rush and no need to do it in one sitting — the container picks up
where you left off.

<sub>Running this as a taught course? See
[docs/instructors.md](docs/instructors.md).</sub>

## Credits

The Moon and Mars worlds use the **Falling Rock** meshes by OpenRobotics
from [Gazebo Fuel](https://app.gazebosim.org/OpenRobotics), licensed
CC-BY. They are vendored under `src/edu_bringup/models/rock1` and
`rock6` so the worlds load offline.

## Licence

Apache-2.0.
