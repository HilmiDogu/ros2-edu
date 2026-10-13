"""Module 09 - Nav2 waypoint navigation: click goals, the rover drives.

    Terminal 1:  ros2 launch edu_bringup simulation.launch.py world:=moon robot:=rover
    Terminal 2:  ros2 launch edu_bringup navigation.launch.py

Then in the RViz window this launch opens:
  * "Nav2 Goal"      -- click + drag one goal; the rover plans and drives.
  * "Waypoints"      -- queue several goals, press "Start Navigation";
                        the rover visits them in order (a waypoint queue).

This brings up three things on top of the already-running simulation:

  1. SLAM (the existing slam.launch.py, with rviz:=false). Nav2 needs a
     map frame and a map -> odom transform; slam_toolbox provides both,
     live, as the rover drives. We do NOT start a second RViz from SLAM.

  2. The real Nav2 stack -- the same planner_server / controller_server /
     bt_navigator / waypoint_follower used on production robots, each a
     managed lifecycle node, brought to 'active' by a lifecycle_manager.

  3. One RViz (rviz/nav2.rviz, Fixed Frame = map) showing the map, the
     costmaps, the planned path and the Nav2 goal tools.

This launch deliberately does NOT start the simulation -- run
simulation.launch.py (or the Moon/Mars desktop icon) first. Pass
rviz:=false to run headless (for testing via the action API).

Two things about this rover shaped the Nav2 config in config/nav2.yaml,
and are worth knowing if you adapt it:
  * The /cmd_vel bridge into Gazebo takes an UNSTAMPED Twist, so every
    Nav2 node that writes /cmd_vel sets enable_stamped_cmd_vel:false.
  * The DiffDrive plugin caps speed at 0.6 m/s / 1.0 rad/s, so the
    controller's limits stay below that.

The controller's velocity command is remapped straight onto /cmd_vel;
this educational stack leaves out the velocity_smoother and
collision_monitor that a full nav2_bringup would also chain in.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_edu_bringup = get_package_share_directory('edu_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz = LaunchConfiguration('rviz')
    params_file = LaunchConfiguration('params_file')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo clock rather than the wall clock.')
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Open the Nav2 RViz view (Fixed Frame=map). Set false '
                    'to run the navigation stack headless, e.g. for testing '
                    'via the NavigateToPose / FollowWaypoints actions.')
    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_edu_bringup, 'config', 'nav2.yaml'),
        description='Nav2 parameters file.')

    # 1. SLAM provides the live map and the map -> odom transform Nav2
    #    needs. rviz:=false: this launch opens its own Nav2 RViz instead,
    #    so we do not want SLAM's map-only RViz on top of it.
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_edu_bringup, 'launch', 'slam.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'rviz': 'false',
        }.items(),
    )

    # 2. The Nav2 stack. These are plain (non-lifecycle) Node actions; the
    #    lifecycle_manager below drives each through configure -> activate.
    #    Only the nodes an educational waypoint demo needs are started --
    #    no velocity_smoother, collision_monitor or docking_server.
    controller = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        # The controller normally publishes cmd_vel_nav for a downstream
        # velocity_smoother. We have none, so send its command straight to
        # the Gazebo bridge's /cmd_vel.
        remappings=[('cmd_vel', '/cmd_vel')],
    )
    planner = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
    )
    behavior = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[('cmd_vel', '/cmd_vel')],
    )
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
    )
    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
    )

    # The lifecycle_manager configures and activates the nodes above, in
    # order, and keeps them alive. "Managed nodes are active" in its log
    # means the whole stack is ready to accept goals.
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart': True,
            'node_names': [
                'controller_server',
                'planner_server',
                'behavior_server',
                'bt_navigator',
                'waypoint_follower',
            ],
        }],
    )

    # 3. One RViz, Fixed Frame = map, with the Nav2 displays and the
    #    "Nav2 Goal" / "Publish Point" / waypoint tools.
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_edu_bringup, 'rviz', 'nav2.rviz')],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(rviz),
        output='screen',
    )

    return LaunchDescription([
        declare_sim_time, declare_rviz, declare_params,
        slam,
        controller, planner, behavior, bt_navigator, waypoint_follower,
        lifecycle_manager,
        rviz_node,
    ])
