# Educational ROS 2 + Gazebo workspace, GUI-in-the-browser.
#
# ROS 2 Jazzy Jalisco + Gazebo Harmonic on Ubuntu 24.04, with an Xfce
# desktop served over noVNC at http://localhost:6902. Students need a
# browser and nothing else -- no ROS install, no X server, no WSL
# configuration, identical on Windows/macOS/Linux.
#
# IMPORTANT: this Dockerfile does NOT override ENTRYPOINT. The base
# image's ENTRYPOINT (tini -> /dockerstartup/startup.sh) performs the
# user setup and VNC/noVNC bring-up that make the GUI work.
FROM accetto/ubuntu-vnc-xfce-g3:latest

USER 0
ENV DEBIAN_FRONTEND=noninteractive

# ROS 2 tooling assumes a UTF-8 locale; the base image defaults to POSIX.
ENV LANG=C.utf8 \
    LC_ALL=C.utf8

# --- ROS 2 Jazzy + Gazebo Harmonic --------------------------------------
# Gazebo is installed from the ROS package repository via vendor packages
# (`ros-jazzy-ros-gz`), which is the officially supported pairing as of
# Jazzy. Installing gz-harmonic from the separate packages.osrfoundation
# repo alongside it is what produces the classic duplicate-library
# crashes, so we deliberately use ONE apt source for both.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg2 lsb-release ca-certificates software-properties-common \
    && add-apt-repository universe -y \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
         -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
         > /etc/apt/sources.list.d/ros2.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-desktop \
        ros-jazzy-ros-gz \
        ros-jazzy-ros-gz-bridge \
        ros-jazzy-ros-gz-sim \
        ros-jazzy-ros-gz-image \
        ros-jazzy-teleop-twist-keyboard \
        ros-jazzy-joint-state-publisher-gui \
        ros-jazzy-xacro \
        ros-jazzy-tf2-tools \
        ros-jazzy-rqt-common-plugins \
        ros-jazzy-rqt-tf-tree \
        ros-jazzy-rqt-graph \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-pip \
        python3-argcomplete \
        # ament_cmake packages invoke CMake's project(), which fails without
        # a C/C++ toolchain even for a package that compiles nothing. Also
        # what students need the moment they write their first C++ node.
        build-essential \
        cmake \
        git \
        xterm \
        nano \
    && rm -rf /var/lib/apt/lists/*

# --- Navigation stack (module 04) ---------------------------------------
# Split into its own layer: Nav2 + SLAM pull in a large dependency set,
# and keeping them separate means edits to the ROS base layer above do
# not force a rebuild of this one (and vice versa).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-navigation2 \
        ros-jazzy-nav2-bringup \
        ros-jazzy-slam-toolbox \
        ros-jazzy-twist-mux \
    && rm -rf /var/lib/apt/lists/*

# --- Software rendering --------------------------------------------------
# There is no GPU inside the container and no host GL passthrough, so
# Gazebo's Ogre2 renderer must fall back to Mesa's software rasterizer.
# Without these, `gz sim` comes up with a black viewport or dies with an
# "Unable to create the rendering window" error -- the single most common
# way this kind of workspace fails for students.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1-mesa-dri \
        mesa-utils \
        libglu1-mesa \
        libegl1 \
    && rm -rf /var/lib/apt/lists/*
ENV LIBGL_ALWAYS_SOFTWARE=1 \
    GALLIUM_DRIVER=llvmpipe \
    MESA_GL_VERSION_OVERRIDE=3.3 \
    QT_X11_NO_MITSHM=1

# Gazebo's default is to phone home for online model assets on first use.
# In a classroom (flaky wifi, proxies, offline rooms) that turns into a
# multi-minute hang with no error, so the workspace ships its own models
# and we point the resource path at them instead.
ENV GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models \
    GZ_VERSION=harmonic

# Auto-source ROS and the workspace overlay for every shell the student
# opens -- terminals, desktop launchers and `docker exec` alike. Sourcing
# the overlay is guarded because it does not exist until the first build.
RUN printf '%s\n' \
    'source /opt/ros/jazzy/setup.bash' \
    '[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash' \
    'export GZ_SIM_RESOURCE_PATH=/workspace/src/edu_bringup/models' \
    > /etc/profile.d/ros2.sh \
    && cat /etc/profile.d/ros2.sh >> /etc/bash.bashrc

# --- noVNC viewer defaults ----------------------------------------------
# noVNC ships with resize=off, which draws the desktop at its native size
# in a fixed box and leaves the rest of the browser tab empty -- the
# desktop looks like a small window floating in a grey void, and students
# reasonably assume the resolution is wrong.
#
# 'remote' makes the DESKTOP resize itself to the browser window, so it
# fills the tab and re-fits on every resize or F11. ('scale' would
# stretch the image instead: it also fills the tab, but blurs text, which
# matters when you are reading terminal output and RViz labels all day.)
#
# defaults.json is read by noVNC at load and can still be overridden per
# user in the settings panel, unlike mandatory.json which would lock it.
RUN printf '%s\n' \
    '{' \
    '  "resize": "remote",' \
    '  "reconnect": "true",' \
    '  "reconnect_delay": "2000",' \
    '  "quality": "6"' \
    '}' \
    > /usr/libexec/noVNCdim/defaults.json

# --- Self-provisioning on desktop login ---------------------------------
# The desktop icons and the colcon build live in the container's own
# filesystem, not in the bind-mounted /workspace. Anyone who starts the
# container without up.sh -- or recreates it after an image rebuild --
# would otherwise get a bare desktop and a `ros2 run` that finds no
# packages, which reads as a broken workspace rather than a missing
# setup step.
#
# An Xfce autostart entry fixes that: the desktop provisions itself
# however it was started. The script is cheap to re-run and never aborts
# the session on failure.
RUN mkdir -p /etc/xdg/autostart && \
    printf '%s\n' \
    '[Desktop Entry]' \
    'Type=Application' \
    'Name=ROS 2 workspace setup' \
    'Comment=Install desktop launchers and build the colcon workspace' \
    'Exec=/workspace/docker/autostart_setup.sh' \
    'Terminal=false' \
    'NoDisplay=true' \
    'X-GNOME-Autostart-enabled=true' \
    > /etc/xdg/autostart/ros2-edu-setup.desktop

# Following the base image's documented extension pattern.
RUN chmod 666 /etc/passwd /etc/group

WORKDIR /workspace
USER "${HEADLESS_USER_ID}"
