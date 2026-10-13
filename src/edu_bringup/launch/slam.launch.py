"""Module 04 - SLAM: build a map while driving through an unknown world.

    Terminal 1:  ros2 launch edu_bringup simulation.launch.py
    Terminal 2:  ros2 launch edu_bringup slam.launch.py
    Terminal 3:  ros2 launch edu_bringup teleop.launch.py

Drive slowly around the arena and watch the map appear in RViz.

SLAM - Simultaneous Localisation And Mapping - solves the chicken-and-egg
problem module 03 ended on: to build a map you need to know where you
are, and to know where you are you need a map. slam_toolbox does both at
once, by matching each new laser scan against the map built so far.

This launch also opens its own RViz with Fixed Frame = map (the
simulation's RViz uses odom). That matters: raw wheel odometry drifts --
bump a wall and the robot's believed heading can end up ~90 degrees off
reality -- and in the odom frame the robot slowly faces the wrong way
relative to the scan. slam_toolbox publishes a map -> odom correction, so
viewing in map keeps the robot and scan aligned with the world. Pass
rviz:=false to skip it if the simulation RViz is enough.

Watch for the moment the robot completes a loop of the arena and the map
visibly snaps into alignment. That is *loop closure*: the algorithm
recognises a place it has seen before and corrects all the accumulated
drift at once. It is the thing odometry alone can never do -- and until a
loop closes, the map-frame pose is corrected but not yet perfect.

Save your finished map with:
    ros2 run nav2_map_server map_saver_cli -f ~/my_map
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    pkg_edu_bringup = get_package_share_directory('edu_bringup')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo clock rather than the wall clock')
    declare_rviz = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Open an RViz view with Fixed Frame=map, so the robot '
                    'is drawn via the SLAM-corrected pose rather than raw '
                    '(drifting) odometry. Set false if the simulation RViz '
                    'is enough.')

    # async_slam_toolbox_node is a *managed lifecycle* node: it starts
    # 'unconfigured' and subscribes to nothing until it is transitioned to
    # 'active'. Launching it alone (as a plain Node) leaves it inert -- no
    # /scan subscription and no /map ever appears, with no error to
    # explain why. So it must be a LifecycleNode and we must drive the
    # configure -> activate transitions ourselves.
    slam = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
        parameters=[
            os.path.join(pkg_edu_bringup, 'config', 'slam.yaml'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # On startup, request 'configure'.
    configure = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=matches_action(slam),
        transition_id=Transition.TRANSITION_CONFIGURE,
    ))

    # Once it reports 'inactive' (i.e. configure succeeded), request
    # 'activate' -- which is when it subscribes to /scan and starts
    # publishing /map.
    activate = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam,
        start_state='configuring', goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=matches_action(slam),
            transition_id=Transition.TRANSITION_ACTIVATE,
        ))],
    ))

    # RViz showing the SLAM-corrected view. Fixed Frame = map here, unlike
    # the simulation's RViz (Fixed Frame = odom): once slam_toolbox
    # publishes map -> odom, viewing in map cancels the odometry drift, so
    # the robot and scan stay aligned with the world even after the wheels
    # have slipped. A separate config because the base sim has no map frame.
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_edu_bringup, 'rviz', 'slam.rviz')],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    return LaunchDescription(
        [declare_sim_time, declare_rviz, slam, configure, activate, rviz])
