"""Bring up the full simulation: Gazebo + EduBot + the ROS 2 bridge + RViz.

This is the launch file every later module builds on. Run it with:

    ros2 launch edu_bringup simulation.launch.py

Useful arguments:

    rviz:=false      start without RViz (lighter on slow machines)
    gui:=false       run Gazebo headless (no 3D window, sensors still run)
    world:=<name>    load a different world from edu_bringup/worlds
                     (classroom | moon | mars)
    robot:=<name>    which robot to spawn: edubot | rover

The Moon and Mars worlds set their own (reduced) gravity and are the
natural pairing for robot:=rover, but any robot works in any world -- the
robot and the world are independent choices. Example:

    ros2 launch edu_bringup simulation.launch.py world:=mars robot:=rover

What this file actually starts, and why each part is needed:

  1. gz sim          - the physics simulation and its 3D window
  2. spawner         - places the EduBot model into the running world
  3. parameter_bridge- copies messages between Gazebo and ROS 2
  4. robot_state_publisher - broadcasts the robot's TF tree from the URDF
  5. rviz2           - the ROS-side visualisation

Remove any one of them and something visibly breaks; that is the point
of the exercise in docs/02-gazebo-and-sensors.md.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (Command, LaunchConfiguration,
                                  PathJoinSubstitution, PythonExpression)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


# Where the robot starts, in world metres.
#
# NOT (-4,-4): on the sculpted Moon/Mars terrain that point sits on a
# 0.52 m/m slope -- a 27 degree incline inside a crater wall. The rover
# spawned part-way down it and could not climb out, which looks like a
# traction bug rather than a bad spawn. (-4.4,-1.6) measures 0.09 m/m,
# effectively flat, and is 2.2 m clear of the nearest rock.
#
# If you reshape the terrain, re-check this: models/ground has the
# heightmap these numbers were measured from.
SPAWN_X, SPAWN_Y = -4.4, -1.6


def generate_launch_description():
    pkg_edu_bringup = get_package_share_directory('edu_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world = LaunchConfiguration('world')
    robot = LaunchConfiguration('robot')
    use_rviz = LaunchConfiguration('rviz')
    use_gui = LaunchConfiguration('gui')

    declare_world = DeclareLaunchArgument(
        'world', default_value='classroom',
        description='World to load from edu_bringup/worlds, without .sdf: '
                    'classroom | moon | mars')
    declare_robot = DeclareLaunchArgument(
        'robot', default_value='edubot',
        description='Robot to spawn: edubot | rover')
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Start RViz2 alongside the simulation')
    declare_gui = DeclareLaunchArgument(
        'gui', default_value='true',
        description='Show the Gazebo 3D window (false = headless)')

    # Terrain height at the spawn point, read from the same heightmap the
    # mesh is built from. Keeping this in step with make_terrain_mesh.py
    # matters: if the terrain is regenerated with a different VRANGE, the
    # spawn height has to follow or the rover starts underground.
    def _terrain_spawn_z():
        from PIL import Image
        hm = os.path.join(pkg_edu_bringup, 'models', 'ground', 'heightmap.png')
        if not os.path.exists(hm):
            return '0.15'
        SPAN, VRANGE, ZOFF = 30.0, 12.0, -5.4
        img = Image.open(hm).convert('L')
        px, n = img.load(), img.size[0]
        x, y = SPAWN_X, SPAWN_Y
        u = (x + SPAN / 2.0) / SPAN
        v = (SPAN / 2.0 - y) / SPAN          # row 0 is +y
        i = min(max(int(round(u * (n - 1))), 0), n - 1)
        j = min(max(int(round(v * (n - 1))), 0), n - 1)
        z = (px[i, j] / 255.0) * VRANGE + ZOFF
        return f'{z + 0.35:.2f}'             # clearance above the surface

    spawn_z = _terrain_spawn_z()

    world_path = PathJoinSubstitution([pkg_edu_bringup, 'worlds', [world, '.sdf']])

    # -- 1. Gazebo ---------------------------------------------------------
    # -r starts the world unpaused: without it students see a frozen scene
    # and reasonably conclude the simulation is broken.
    # -s runs the server only, for the headless case.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': [world_path, ' -r -v 2'],
            'on_exit_shutdown': 'true',
        }.items(),
        condition=IfCondition(use_gui),
    )

    gz_sim_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': [world_path, ' -r -s -v 2'],
            'on_exit_shutdown': 'true',
        }.items(),
        # UnlessCondition, not IfCondition(['not ', ...]): a condition is
        # evaluated as a literal string, so concatenating 'not ' yields
        # 'not false', which launch rejects outright.
        condition=UnlessCondition(use_gui),
    )

    # -- 2. Spawn the robot -------------------------------------------------
    # The robot is spawned into the world rather than written into the world
    # file, so the same world can be reused with a different robot, and so
    # students can re-spawn without restarting Gazebo.
    # The model file and spawn name follow the robot argument, so the same
    # launch spawns edubot or the rover from models/<robot>/model.sdf.
    robot_sdf = PathJoinSubstitution(
        [pkg_edu_bringup, 'models', robot, 'model.sdf'])
    # Two spawn nodes rather than one, because the right z depends on the
    # world and `world` is a LaunchConfiguration -- not a Python value we
    # can branch on here.
    #
    # classroom is a flat ground plane at z=0, so a small fixed clearance
    # is right. moon and mars use a sculpted mesh whose surface at the
    # spawn point sits metres below zero; dropping the rover from 0.15
    # there makes it fall, bounce and sometimes tunnel through.
    spawn_common = ['-file', robot_sdf, '-name', robot,
                    '-x', str(SPAWN_X), '-y', str(SPAWN_Y)]

    spawn_flat = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=spawn_common + ['-z', '0.15'],
        condition=IfCondition(PythonExpression(
            ["'", world, "' == 'classroom'"])),
        output='screen',
    )

    spawn_terrain = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=spawn_common + ['-z', spawn_z],
        condition=UnlessCondition(PythonExpression(
            ["'", world, "' == 'classroom'"])),
        output='screen',
    )

    # -- 3. The ROS <-> Gazebo bridge ---------------------------------------
    # Gazebo Transport and ROS 2 are two separate messaging systems that do
    # not talk to each other. This bridge is the only thing connecting them.
    #
    # Direction matters, and is the subtlest part of the whole workspace:
    #   @  bidirectional
    #   [  Gazebo  -> ROS   (sensor data flowing out)
    #   ]  ROS     -> Gazebo (commands flowing in)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Commands in: ROS -> Gazebo.
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            # Sensor and state data out: Gazebo -> ROS.
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # 3-D lidar for terrain. A PointCloud2 rather than a
            # LaserScan: it carries the vertical rays that make the
            # craters and ridge visible as shape. SLAM still uses
            # /scan above; this one is purely for seeing.
            # NOTE the topic name. A gpu_lidar publishes TWO topics:
            # <topic> as a LaserScan, and <topic>/points as the point
            # cloud. The sensor's <topic> is 'points', so the cloud is
            # on /points/points. Bridging /points as PointCloudPacked
            # instead is a type mismatch against the LaserScan that
            # actually lives there, and fails silently -- the ROS topic
            # appears in `ros2 topic list` and never carries a message.
            '/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            # Ground truth: what Gazebo actually simulated, as opposed
            # to what the wheels believe. Published by a second
            # OdometryPublisher in the robot SDF so students can see
            # odometry drift away from reality in RViz.
            '/odom_truth@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            # The simulation clock, so every ROS node can run on sim time.
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    # Images go through image_bridge rather than parameter_bridge: it
    # handles the image transport plumbing that plain message conversion
    # does not.
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera'],
        output='screen',
    )

    # -- 4. Robot state publisher -------------------------------------------
    # Reads the URDF and publishes the robot's transform tree. This is what
    # lets RViz draw the robot and place the lidar scan at the right spot.
    # The URDF matching the spawned robot: models/<robot>.urdf.xacro.
    robot_xacro = PathJoinSubstitution(
        [pkg_edu_bringup, 'models', [robot, '.urdf.xacro']])
    robot_description = ParameterValue(
        Command(['xacro ', robot_xacro]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            # Every node must agree to use Gazebo's clock rather than the
            # wall clock, or TF lookups fail with confusing timing errors.
            'use_sim_time': True,
        }],
    )

    # -- 5. RViz -------------------------------------------------------------
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_edu_bringup, 'rviz', 'edubot.rviz')],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        declare_world,
        declare_robot,
        declare_rviz,
        declare_gui,
        gz_sim,
        gz_sim_headless,
        spawn_flat,
        spawn_terrain,
        bridge,
        image_bridge,
        robot_state_publisher,
        rviz,
    ])
