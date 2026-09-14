"""Module 04 - SLAM: build a map while driving through an unknown world.

    Terminal 1:  ros2 launch edu_bringup simulation.launch.py
    Terminal 2:  ros2 launch edu_bringup slam.launch.py
    Terminal 3:  ros2 launch edu_bringup teleop.launch.py

Drive slowly around the arena and watch the map appear in RViz.

SLAM - Simultaneous Localisation And Mapping - solves the chicken-and-egg
problem module 03 ended on: to build a map you need to know where you
are, and to know where you are you need a map. slam_toolbox does both at
once, by matching each new laser scan against the map built so far.

Watch for the moment the robot completes a loop of the arena and the map
visibly snaps into alignment. That is *loop closure*: the algorithm
recognises a place it has seen before and corrects all the accumulated
drift at once. It is the thing odometry alone can never do.

Save your finished map with:
    ros2 run nav2_map_server map_saver_cli -f ~/my_map
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    pkg_edu_bringup = get_package_share_directory('edu_bringup')

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use the Gazebo clock rather than the wall clock')

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

    return LaunchDescription([declare_sim_time, slam, configure, activate])
