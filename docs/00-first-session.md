# Before you start: the first hour

For students who have not used Linux, Docker, or a command line before.
Nothing here assumes you have. If you already know your way around a
terminal, skip to [Module 01](01-ros2-basics.md).

Read this once through before touching anything. It is short.

---

## What you are about to do

You will drive a simulated rover across the Moon, watch it build a map
of the terrain with a laser scanner, and then write the code that makes
it drive itself.

None of that runs on your computer directly. It runs inside a **Linux
machine that lives in a window in your browser**. That is the single
strangest idea in this course, so it is worth getting straight first.

---

## The four words you need

You will meet these constantly. You do not need to understand them
deeply yet — you need to stop finding them alarming.

### Linux

Another operating system, like Windows or macOS. Almost all robots run
it. You are not installing it; you are borrowing one.

### Docker

A way of packing a whole computer — operating system, programs, settings
— into a single file that runs anywhere. Someone else already built
ours. You download it once and run it; you never configure it.

This is why the course works identically on your laptop and the one next
to you. There is no "it works on my machine" here.

### ROS 2

The software robots are built from. Not a program you open — a *set of
rules* that lets many small programs talk to each other.

A real robot might run thirty of these at once: one reading the camera,
one planning a route, one driving the motors. ROS 2 is how they
communicate. You will write some of them.

### Gazebo

The simulator. It does the physics — gravity, wheels slipping, a laser
beam bouncing off a rock. It is where your robot actually exists.

---

## The one picture worth having

```
   Your laptop (Windows / macOS)
   │
   └── Docker ─── a Linux machine
                  │
                  ├── Gazebo ......... the robot and the world
                  ├── ROS 2 .......... the robot's software
                  └── a desktop ...... which you see in your browser
```

Your browser is a **window onto that Linux desktop**. When you click
things there, you are clicking inside the Linux machine, not on your own
computer.

Two consequences that confuse everyone once:

- **Your own files are not in there**, except the course folder, which
  is deliberately shared with it.
- **Closing the browser does not stop anything.** The Linux machine
  keeps running. Reopen the tab and it is as you left it.

---

## Getting it running

Two steps, once.

**1. Install Docker.** Follow
[installing-docker.md](installing-docker.md) — it covers Windows, Linux
and macOS separately. **Do this the day before the session**, not on the
morning: it downloads several gigabytes, and thirty people doing that at
once on the same wifi does not work.

**2. Start the workspace.** In the project folder:

```powershell
.\docker\up.ps1
```

Then open **<http://localhost:6902>** in your browser. The password is
`ros2edu`.

The first run takes 10–20 minutes. Later ones take seconds.

If something goes wrong, it is almost certainly in
[troubleshooting.md](troubleshooting.md) already. Look there first —
working out why something broke is most of what this skill actually is,
and you will meet the same handful of causes over and over.

---

## What a terminal is, in two minutes

Much of this course happens in a terminal: a window where you type a
command and the computer does it, instead of clicking.

It feels backwards for about a day, then it feels faster, because you
can say things a menu cannot offer — "run this on the robot, with the
map display on, logging to this file".

Open one by double-clicking **ROS 2 Terminal** on the Linux desktop.
Type:

```bash
ros2 topic list
```

and press Enter. You will get a list of the channels the robot is
currently talking on. You just inspected a running robot.

Five things worth knowing immediately:

| | |
|---|---|
| **Up arrow** | the previous command, so you can edit rather than retype |
| **Tab** | completes a half-typed name — use it constantly |
| **Ctrl+C** | stop whatever is running. Not "copy". Your main exit |
| **Enter** | nothing happens until you press it |
| Red text | usually an error, occasionally just a warning. Read it |

**Read the error.** Programmers do not understand errors on sight; they
read them, and so should you. The answer is usually in the last line.

---

## Your first twenty minutes

Do these in order. Stop after each and look at what happened.

### 1. Make two programs talk

Double-click **01 Hello ROS 2**.

Two programs start. One says something every tenth of a second; the
other hears it and repeats it. They were written separately and never
mention each other — they connect because they agree on a channel name.

That is ROS 2 in one sentence. Everything else is detail.

Press **Ctrl+C** to stop.

### 2. Drive a rover on the Moon

Double-click **06 Moon Rover** and wait — **30 to 60 seconds**. There is
no graphics card in there, so the view is drawn in software, and it is
slow to start. A grey window is normal.

Three browser windows end up in play:

| Open this | You see |
|-----------|---------|
| <http://localhost:6902> | the desktop, where you click things |
| <http://localhost:6903> | **RViz** — what the robot *believes* |
| <http://localhost:6904> | **Gazebo** — what is *actually* happening |

That split is the most useful idea in the course, so look at both.
Gazebo is the truth. RViz is the robot's opinion, assembled from its
sensors. When they disagree, something interesting is happening.

### 3. Drive it

Double-click **03 Teleop**. **Keep that window focused** — if you click
Gazebo, the keys stop reaching it and the rover carries on with its last
order.

```
  i = forward     , = back
  j = turn left   l = turn right
  k = STOP
```

Drive into a crater wall and hold the key down. Watch RViz: the rover
keeps advancing there, while in Gazebo it is stuck with its wheels
spinning.

Nothing is broken. The wheels *are* turning, and the robot counts wheel
turns to work out where it is. It has no way to know it is not moving.

This is **odometry drift**, and it is why robots cannot simply count
wheel rotations. Module 03 is about it.

### 4. Watch it build a map

The map builds in RViz as you drive — the SLAM system started
automatically with the rover.

Drive slowly in a loop. Grey is unknown, white is empty space the laser
has seen through, black is something solid.

Now complete a full circuit back to where you started. At some point the
map **snaps** into alignment. The robot recognised a place it had seen
before and corrected all its accumulated error at once.

That moment is called *loop closure*, and it is the thing counting wheel
turns can never do. Module 04 is about it.

---

## How to work through the course

Four modules, in order. Each builds on the last.

| | | Time |
|---|---|---|
| [01](01-ros2-basics.md) | Nodes, topics, the ROS 2 command line | ~2 h |
| [02](02-gazebo-and-sensors.md) | Robots, worlds, sensors | ~3 h |
| [03](03-tf-and-odometry.md) | Coordinate frames; why odometry lies | ~2 h |
| [04](04-navigation.md) | Control, SLAM, autonomous navigation | ~3 h |

Each ends with exercises in [exercises.md](exercises.md): a file with
gaps marked `TODO`, and a worked solution beside it.

**Try for fifteen minutes before opening the solution.** Then run the
solution to see what it is *meant* to do, go back to yours, and read the
solution's code last. Reading it first feels efficient and teaches
almost nothing.

---

## Four things that will go wrong

Not might. Will. Everyone hits these, so recognise them rather than
losing an afternoon.

### "I ran it and nothing happened"

The commonest cause by far is a **QoS mismatch**. Sensor data is sent in
a mode that prioritises speed over guaranteed delivery, and a program
that asks for guaranteed delivery receives *nothing at all* — with no
error, ever.

```bash
ros2 topic info /scan -v
```

Compare the `Reliability` lines. Module 02 explains it properly.

### "package not found"

Either you have not told this terminal where the course code is:

```bash
source /workspace/install/setup.bash
```

or you added a new file and have not rebuilt:

```bash
/workspace/docker/build_ws.sh
```

The desktop icons do the first for you. A terminal you opened another
way does not.

### "My change did nothing"

Did you stop the old simulation before starting a new one? Two copies
running at once means you may be looking at the old one. The simulation
icons now stop the previous one for you, but a simulation you started by
typing does not.

### The robot will not stop

The teleop window lost focus. Click it and press `k`. Failing that, from
any terminal:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"
```

---

## What you are actually learning

Not "how to use this workspace". The simulated rover is a device for
teaching things that are true of all robots:

- Software built from **small independent parts that talk over named
  channels** — so you can replace the simulation with real hardware and
  change nothing else.
- **Sensors lie, and robots must cope.** Odometry drifts. Lasers return
  nonsense. Good robot code assumes this.
- **The difference between what a robot believes and what is true** —
  which is the whole of localisation, mapping and navigation.

Those transfer to any robot, any language, any framework.

---

Ready. Start with [Module 01](01-ros2-basics.md).

Lost? [troubleshooting.md](troubleshooting.md) covers everything that
has gone wrong for anyone so far.
Forgotten a command? [cheatsheet.md](cheatsheet.md) is one page.
