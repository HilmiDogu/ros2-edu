"""SOLUTION 03 - wall follower.

    ros2 run edu_exercises sol03_wall_follower

Then tune it live and watch the trade-off:
    ros2 param set /wall_follower kp 0.5
    ros2 param set /wall_follower kp 3.0
    ros2 param set /wall_follower kp 15.0
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan


class WallFollower(Node):

    def __init__(self):
        super().__init__('wall_follower')

        self.declare_parameter('desired_distance', 1.0)
        self.declare_parameter('forward_speed', 0.3)
        self.declare_parameter('kp', 2.0)
        self.declare_parameter('max_angular', 1.5)

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.scan_sub = self.create_subscription(
            LaserScan, 'scan', self.on_scan, sensor_qos)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)

        self.scan = None
        self.timer = self.create_timer(0.1, self.control_step)
        self.get_logger().info('Wall follower started')

    def on_scan(self, msg):
        self.scan = msg

    def distance_at(self, angle_deg, width_deg=20.0):
        centre = math.radians(angle_deg)
        half_width = math.radians(width_deg) / 2.0

        closest = float('inf')
        for i, distance in enumerate(self.scan.ranges):
            angle = self.scan.angle_min + i * self.scan.angle_increment
            angle = math.atan2(math.sin(angle), math.cos(angle))
            if abs(angle - centre) > half_width:
                continue
            if math.isinf(distance) or math.isnan(distance):
                continue
            closest = min(closest, distance)

        return closest

    def control_step(self):
        cmd = Twist()

        if self.scan is None:
            self.cmd_pub.publish(cmd)
            return

        left = self.distance_at(90.0)
        ahead = self.distance_at(0.0, width_deg=40.0)

        forward_speed = self.get_parameter('forward_speed').value
        desired = self.get_parameter('desired_distance').value
        kp = self.get_parameter('kp').value
        max_angular = self.get_parameter('max_angular').value

        # Inside corner: a wall ahead beats the distance-keeping goal.
        # Without this case the controller happily regulates its distance
        # to the left wall while driving nose-first into the one in front.
        if ahead < 0.8:
            cmd.linear.x = 0.0
            cmd.angular.z = -1.0
            self.cmd_pub.publish(cmd)
            self.get_logger().info('Corner - turning right',
                                   throttle_duration_sec=1.0)
            return

        # No wall within range: curve left to go looking for one.
        if math.isinf(left):
            cmd.linear.x = forward_speed * 0.5
            cmd.angular.z = 0.4
            self.cmd_pub.publish(cmd)
            self.get_logger().info('Lost the wall - searching',
                                   throttle_duration_sec=2.0)
            return

        # The proportional control law.
        error = desired - left
        angular_z = -kp * error

        # Clamping matters: a momentary bad reading would otherwise
        # command an enormous turn rate and spin the robot on the spot.
        angular_z = max(-max_angular, min(max_angular, angular_z))

        cmd.linear.x = forward_speed
        cmd.angular.z = angular_z
        self.cmd_pub.publish(cmd)

        self.get_logger().info(
            f'left={left:.2f}m  error={error:+.2f}  turn={angular_z:+.2f}',
            throttle_duration_sec=1.0)

    def stop_robot(self):
        self.cmd_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = WallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_robot()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
