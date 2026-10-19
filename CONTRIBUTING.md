# Contributing

Thanks for your interest in improving this ROS 2 + Gazebo teaching
workspace. It is built for bachelor students with no prior robotics
experience, so the guiding principle for every change is: **keep it
simple, readable, and reproducible.**

## Ground rules

- **Everything runs in the container.** A contributor should need only
  Docker — no local ROS install. If a change needs a new tool, add it to
  `docker/Dockerfile`, not to a "run this on your host first" step.
- **Keep it offline and instant.** Worlds and models load with no network
  and in seconds. Prefer primitives or small vendored assets over large
  downloads; procedural generators (see `src/edu_bringup/models/ground/`)
  are kept in the repo so their output is reproducible.
- **Comment the "why", for a beginner.** The existing files explain the
  reasoning behind non-obvious choices (frame conventions, friction
  values, lifecycle quirks). Match that: a comment should teach, not just
  restate the code.

## Getting set up

```bash
git clone <your-fork>
cd ros2-edu
./docker/up.sh          # builds the image, starts the container, builds the workspace
```

Then open <http://localhost:6902> (VNC password `ros2edu`). See the
[README](README.md) and [docs/usage.md](docs/usage.md) for the full tour.

## Making a change

1. **Branch** off `master`: `git checkout -b my-change`.
2. **Edit** the source on your machine — `src/` is bind-mounted into the
   container, so edits appear inside immediately.
3. **Rebuild** the ROS workspace in the container after changing anything
   under `src/`:
   ```bash
   docker exec ros2-gazebo-edu /workspace/docker/build_ws.sh
   ```
   Python nodes take effect without a rebuild (`--symlink-install`); you
   only need to rebuild when you add a file or change `setup.py`.
4. **Test it for real.** Launch the relevant module and confirm the
   behaviour, not just that nodes start. For simulation/world changes,
   drive the rover and check it behaves; for SLAM/Nav2, send a goal and
   confirm it reaches it.
5. **Regenerate derived assets** if you touched a generator. For example,
   after editing `make_heightmap.py`, also run `make_terrain_mesh.py` and
   commit the updated `heightmap.png` / `terrain.obj`.

## Style

- **SDF / world / XML:** valid XML — never `--` inside an `<!-- -->`
  comment (Gazebo tolerates it, strict parsers do not).
- **Shell / Python / launch files:** keep line endings LF (enforced by
  `.gitattributes`); match the surrounding file's comment density and
  naming.
- **Masses and inertias** must be physically consistent — if you change a
  mass, recompute the inertia from the box/cylinder formula rather than
  leaving a stale value.

## Commit messages

Write a short imperative subject line and a body that explains **why**,
including any measurement that justifies the change (this project values
"measured, not eyeballed" — see the terrain generator comments). Keep each
commit focused on one logical change.

## Opening a pull request

- Describe what changed and how you verified it.
- Keep binary assets small; mesh/image files are tracked as binary via
  `.gitattributes`.
- By contributing, you agree your contributions are licensed under the
  project's [BSD 3-Clause License](LICENSE).

## Reporting issues

Please include: which icon/launch you ran, the world and robot, what you
expected, what happened, and any terminal output. A screenshot of Gazebo
or RViz helps a lot for visual problems.
