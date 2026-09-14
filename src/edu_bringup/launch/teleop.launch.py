"""Module 03 - drive the robot from the keyboard.

    ros2 launch edu_bringup teleop.launch.py

teleop_twist_keyboard must own a real terminal, because it reads
individual keypresses. A launch file cannot give it one, so this opens an
xterm for it - which is also why this launch file exists at all rather
than being one more node in simulation.launch.py.

Keys, once the xterm has focus:

    u  i  o        i / ,  forward / back
    j  k  l        j / l  rotate left / right
    m  ,  .        k      STOP
                   q / z  increase / decrease speed

The window must be focused for keys to register. Clicking the 3D view in
Gazebo takes focus away, and the robot then keeps its last command - the
usual reason a student reports "it will not stop".
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    teleop = ExecuteProcess(
        cmd=[
            'xterm',
            '-fa', 'Monospace', '-fs', '11',
            '-geometry', '80x26',
            '-title', 'EduBot teleop - keep this window focused',
            '-e', 'ros2 run teleop_twist_keyboard teleop_twist_keyboard',
        ],
        output='screen',
    )

    return LaunchDescription([teleop])
