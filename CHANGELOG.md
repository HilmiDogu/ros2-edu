# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Dates are in YYYY-MM-DD.

## [Unreleased]

### Added
- BSD 3-Clause `LICENSE` and a `CONTRIBUTING.md` describing the
  container-first, offline, reproducible workflow.

### Changed
- Relicensed the project from Apache-2.0 to BSD-3-Clause consistently
  across the README, all `package.xml` files and both `setup.py` files.
  The vendored Falling Rock meshes keep their original OpenRobotics CC-BY
  licence.

### Fixed
- `up.sh` / `up.ps1` no longer hang at "waiting for the desktop": they
  probe noVNC directly instead of waiting for a log line that current
  versions of the base image no longer print.
- `up.ps1` now installs the desktop launchers instead of failing silently
  (CRLF and PowerShell 5.1 quoting both broke the bash snippet), and
  stops if that step fails.
- `up.sh` works from Git Bash on Windows, which was rewriting container
  paths such as `/workspace/docker/build_ws.sh`; its shebang is now on
  the first line.

## [0.4.0] - 2026-10-15

Usability pass: a more comfortable desktop, better-reading terrain, and
onboarding for students starting from nothing.

### Added
- Three-screen desktop layout: Gazebo and RViz each get their own noVNC
  screen instead of overlapping in one narrow tab, driven from the
  desktop icons, with the layout documented.
- A 3-D lidar so RViz can show the terrain itself, not just the flat map.
- No-go hills and sharper craters in the terrain, plus a space backdrop
  (stars, Earth, a visible sun).
- A Docker install guide and a first-session guide for students new to
  all of this; README rewritten to address the student directly.
- New README images.

### Changed
- The noVNC desktop now fills the browser tab, and the desktop is larger
  with an optional second screen (given its own background and terminal).
- Halved the terrain relief so the rover can actually drive on it, and
  retuned the terrain so it reads as terrain; the rover is kept out of
  the opening shot.
- SLAM now starts with the rover, views in the map frame, and the rover
  spawns on level ground.

### Fixed
- Capped WSL2 and container memory so the noVNC desktop stops freezing on
  Windows.
- Fixed the rover camera and a rendering flicker.
- The desktop icons now stop any previous simulation before starting a
  new one.

## [0.3.0] - 2026-10-13

Terrain, physics and autonomy overhaul.

### Added
- Open 3-D heightmap terrain for the Moon and Mars worlds: rolling hills
  and drivable craters, with the boundary walls removed so the rover
  roams freely.
- Nav2 waypoint navigation — click goals in RViz and the rover plans a
  path and drives to them, avoiding obstacles; with a desktop icon.
- Ground-truth odometry and a collision / wheel-slip monitor that shows
  how wheel odometry drifts from reality.
- A dedicated "Rover Camera" desktop icon, more craters and rocks, a
  space desktop wallpaper, and Gazebo/RViz screenshots in the README.

### Changed
- Terrain is collided against a mesh rather than a heightmap (reliable in
  Gazebo's physics engine), and the rover was made ~100 kg so it plants
  on the ground.
- Grippier wheel and terrain friction to approximate compacted regolith
  so the rover no longer slides, while still being able to turn.
- SLAM opens its own RViz in the map frame to show the drift-corrected
  pose.

### Fixed
- Rover rotational wheel slip that was corrupting the SLAM map.
- Rover falling through / tunnelling out of the terrain while driving.
- Rover launching into the air on rough terrain in low gravity.
- The laser scan collapsing toward the robot (TF published too slowly for
  the sensor rate).
- Documented why the shorter crater is invisible to the 2-D lidar (a
  deliberate teaching point, not a bug).

## [0.2.0] - 2026-09-18

Robustness and documentation.

### Added
- The container provisions itself (desktop icons, workspace build) on
  desktop login, however it was started.
- A diagnostic for missing desktop icons, full README setup docs covering
  every icon, and a troubleshooting section.

### Changed
- Set the Xfce desktop-icon style explicitly so icons appear consistently
  across machines.
- Gave the Moon and Mars ground planes explicit (grippy) friction.

### Fixed
- The rover can now turn, and the lidar no longer scans its own mast.
- Rotate the wheel geometry rather than the wheel link frame, so Gazebo
  and RViz agree on how the wheels spin.

## [0.1.0] - 2026-09-14

Initial educational workspace.

### Added
- Containerised ROS 2 Jazzy + Gazebo Harmonic environment, viewed in a
  browser over noVNC.
- EduBot differential-drive robot, the classroom world, and the
  simulation bringup launch files.
- Worked example nodes for modules 01–04 and student exercises with
  reference solutions.
- Module guides, usage instructions and reference material.
- Selectable Moon and Mars worlds and a six-wheel Perseverance-style
  rover, with textured ground and realistic rock meshes.

### Fixed
- SLAM map sliding with the robot, caused by a split TF tree (base_link
  had two parents); fixed to a single-parent chain.
