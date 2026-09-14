# Instructor guide

Notes for running this workspace as a taught course.

---

## Before the first session

**Ask students to run `docker/up.sh` the night before.** The first build
downloads roughly 4 GB. Thirty students doing that simultaneously on
lecture-hall wifi will consume the entire session.

If your room has poor connectivity, build the image once and distribute
it:

```bash
docker save ros2-gazebo-edu:jazzy | gzip > ros2-edu-image.tar.gz
# students:
docker load < ros2-edu-image.tar.gz
```

**Minimum machine:** 8 GB RAM, 4 CPU cores, 15 GB free disk. It runs on
less, but Gazebo renders in software and the simulation gets slow enough
to be distracting.

Have students check Docker Desktop → Settings → Resources and allocate at
least 4 CPUs.

## Suggested schedule

| Session | Content | Hours |
|---------|---------|-------|
| 1 | Module 01 + Exercise 01 | 2 |
| 2 | Module 02 + Exercise 02 | 3 |
| 3 | Module 03 | 2 |
| 4 | Module 04 + Exercise 03 | 3 |
| 5 | Open project | 2–4 |

Total 12–14 hours. Modules 01 and 02 can be compressed if students
already know Python and basic networking; Module 04 cannot — the tuning
exercise needs time for students to actually play with `kp`.

## The three ideas that matter

If students leave with only three things, make them these:

1. **Decoupling.** Nodes communicate through named topics and know
   nothing about each other. This is why you can swap simulation for real
   hardware without changing controller code — demonstrate it by killing
   the talker while the listener keeps running.

2. **Gazebo shows truth; RViz shows belief.** Everything about state
   estimation follows from this distinction. Module 03's drift
   demonstration is the payoff — make sure nobody skips `square_driver`.

3. **Feedback and gain.** The `kp` tuning in Exercise 03 is the same
   trade-off as every controller in engineering. Have students call out
   their chosen values; the spread makes the point better than a lecture.

## Known friction points

Budget time for these — they catch nearly every cohort:

| Issue | Where it bites | Mitigation |
|-------|----------------|------------|
| **QoS mismatch** | Exercise 02 | Cover it explicitly before they start. It fails *silently* — students assume their code is wrong |
| **`nan` in laser ranges** | Exercise 02 | Same. `nan` comparisons are always `False`, so the check never fires |
| **Forgetting `setup.py`** | Any new node | A new file needs an entry in `console_scripts` **and** a rebuild |
| **Unsourced terminal** | Constantly | "package not found" almost always means this |
| **Teleop focus** | Module 04 | The window must keep focus; clicking Gazebo steals it |

## Assessment ideas

**Formative** — each module has a checklist students can self-assess
against.

**Summative** — some options that are hard to solve by copying:

1. *Modify the robot.* Add a second lidar at the rear, bridge it, show it
   in RViz. Tests understanding of SDF, the bridge, and TF together.
2. *Fix the broken robot.* Hand out a `model.sdf` with the wheel radius
   wrong and ask students to diagnose why odometry over-reports distance.
   Excellent discriminator — it requires connecting the plugin maths to
   observed behaviour.
3. *Extend the controller.* Add a derivative term to the wall follower
   and demonstrate, with a plot, that it reduces oscillation at high
   `kp`.
4. *Build and map a world.* Author a maze, then map it with SLAM and
   navigate it with Nav2.

For (2), the cleanest injected fault is changing `<wheel_radius>` in the
`DiffDrive` plugin block while leaving the visual geometry correct — the
robot looks right and drives right, but odometry is wrong, so RViz and
Gazebo disagree. That is exactly the real-world calibration bug.

## Extending the workspace

To add a module:

1. Write the node in `src/edu_py_examples/edu_py_examples/`.
2. Register it in that package's `setup.py` under `console_scripts`.
3. Add the exercise skeleton in `src/edu_exercises/edu_exercises/` and
   the answer in `src/edu_exercises/solutions/`, registering both.
4. Write `docs/NN-topic.md` and link it from the README table.
5. If it needs a desktop icon, add a `.desktop` file and a launcher
   script in `docker/desktop/`.

To add a world: drop the `.sdf` in `src/edu_bringup/worlds/` and launch
with `world:=yourname`.

## Reproducibility

Every student runs byte-identical software, which removes "works on my
machine" from grading entirely. For a course you will re-run across
years, pin the base image to a digest rather than `:latest` in the
`FROM` line of [`docker/Dockerfile`](../docker/Dockerfile):

```dockerfile
FROM accetto/ubuntu-vnc-xfce-g3@sha256:<digest>
```

Otherwise a future rebuild may pick up a changed base image. ROS 2 Jazzy
itself is supported until May 2029.
