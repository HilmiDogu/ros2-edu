"""SOLUTION 02 - proximity warner.

    ros2 run edu_exercises sol02_subscriber
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan


class ProximityWarner(Node):

    def __init__(self):
        super().__init__('proximity_warner')

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.subscription = self.create_subscription(
            LaserScan, 'scan', self.on_scan, sensor_qos)

        self.declare_parameter('warn_distance', 1.0)
        self.get_logger().info('Proximity warner started')

    def on_scan(self, msg):
        half_wedge = math.radians(15.0)
        closest = float('inf')

        for i, distance in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            angle = math.atan2(math.sin(angle), math.cos(angle))

            if abs(angle) > half_wedge:
                continue
            # Filtering these out BEFORE comparing is the whole point of
            # the exercise: nan propagates silently through min() and
            # every comparison against it is False.
            if math.isinf(distance) or math.isnan(distance):
                continue

            closest = min(closest, distance)

        warn_distance = self.get_parameter('warn_distance').value
        if closest < warn_distance:
            self.get_logger().warn(
                f'Obstacle ahead: {closest:.2f} m',
                throttle_duration_sec=1.0)


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
