"""EXERCISE 02 - subscribe to a real sensor and react to it.

GOAL
    Subscribe to the lidar on /scan and print a warning whenever anything
    is closer than 1.0 m directly in front of the robot.

BEFORE YOU START
    Read edu_py_examples/lidar_monitor.py. It shows the QoS profile you
    need and how to turn a ranges index into an angle.

RUN IT
    Terminal 1:  ros2 launch edu_bringup simulation.launch.py
    Terminal 2:  ros2 run edu_exercises ex02_subscriber
    Terminal 3:  ros2 run teleop_twist_keyboard teleop_twist_keyboard

    Drive towards a wall and watch your warning fire.

CHECK YOUR WORK
    The warning appears as you approach a wall, and stops when you back
    away. If it NEVER fires, check the QoS - see TODO 1.

THE TRAP IN THIS EXERCISE
    scan.ranges contains inf (nothing in range) and can contain nan
    (invalid reading). min(scan.ranges) will happily return nan and your
    comparison will then be False forever, silently. Filter first.

STUCK?
    edu_exercises/solutions/ex02_subscriber.py
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan


class ProximityWarner(Node):

    def __init__(self):
        super().__init__('proximity_warner')

        # TODO 1: build the sensor QoS profile.
        #   Sensor topics are published BEST_EFFORT. A default (RELIABLE)
        #   subscriber will not match, and you will receive NOTHING with
        #   no error message at all. Copy the QoSProfile from
        #   lidar_monitor.py.
        #
        #   sensor_qos = QoSProfile(
        #       reliability=QoSReliabilityPolicy.BEST_EFFORT,
        #       durability=QoSDurabilityPolicy.VOLATILE,
        #       history=QoSHistoryPolicy.KEEP_LAST,
        #       depth=10,
        #   )

        # TODO 2: subscribe to 'scan' with LaserScan, calling self.on_scan,
        #   and pass sensor_qos as the last argument instead of a plain 10.

        self.declare_parameter('warn_distance', 1.0)
        self.get_logger().info('Proximity warner started')

    def on_scan(self, msg):
        # TODO 3: find the closest valid reading in the 30 deg wedge
        #   straight ahead (that is, -15 deg to +15 deg).
        #
        #   For each index i in msg.ranges:
        #     - compute its angle: msg.angle_min + i * msg.angle_increment
        #     - normalise it:      math.atan2(math.sin(a), math.cos(a))
        #     - skip it unless abs(angle) <= math.radians(15)
        #     - skip inf and nan  (math.isinf / math.isnan)
        #     - keep the smallest survivor

        # TODO 4: if that distance is below the 'warn_distance' parameter,
        #   log a warning with the measured distance in it. Pass
        #   throttle_duration_sec=1.0 so a 10 Hz scan does not produce ten
        #   identical lines a second.
        pass


def main(args=None):
    rclpy.init(args=args)
    node = ProximityWarner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
