"""Module 03 - open-loop control, and why odometry alone is not enough.

This node drives the robot in a square by timing: forward for N seconds,
turn for M seconds, four times. It never looks at a sensor to check
whether any of that actually happened. That is *open-loop* control.

Run the simulation, then:
    ros2 run edu_py_examples square_driver

Watch it in RViz with the odometry trail enabled, and watch the reported
pose from tf_listener. The robot will not come back to exactly where it
started, and the error grows with every lap.

Why? The wheels slip, the timing is approximate, and odometry integrates
its own small errors forever - a wheel that reports one extra millimetre
per turn never un-reports it. This is *drift*, and it is the fundamental
reason robots need external references (a map, a lidar, GPS) rather than
just counting their own wheel rotations.

Module 04 solves exactly this problem with SLAM.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node


class SquareDriver(Node):
    """Drives a square open-loop, reporting the accumulated error."""

    def __init__(self):
        super().__init__('square_driver')

        self.declare_parameter('side_length', 2.0)   # m
        self.declare_parameter('speed', 0.3)         # m/s
        self.declare_parameter('turn_speed', 0.5)    # rad/s

        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.odom_sub = self.create_subscription(
            Odometry, 'odom', self.on_odom, 10)

        side = self.get_parameter('side_length').value
        speed = self.get_parameter('speed').value
        turn_speed = self.get_parameter('turn_speed').value

        # Open-loop durations: distance / speed, and a quarter turn at the
        # commanded rate. Both assume the robot does exactly what it was
        # told, which is precisely the assumption the exercise breaks.
        self.drive_duration = side / speed
        self.turn_duration = (math.pi / 2.0) / turn_speed

        self.state = 'drive'
        self.state_started = self.get_clock().now()
        self.sides_done = 0
        self.start_pose = None
        self.current_pose = None

        self.timer = self.create_timer(0.05, self.control_step)
        self.get_logger().info(
            f'Driving a {side} m square: {self.drive_duration:.1f}s per side, '
            f'{self.turn_duration:.1f}s per turn.')

    def on_odom(self, msg):
        self.current_pose = msg.pose.pose
        if self.start_pose is None:
            self.start_pose = msg.pose.pose

    def elapsed_in_state(self):
        return (self.get_clock().now() - self.state_started).nanoseconds / 1e9

    def control_step(self):
        cmd = Twist()

        if self.state == 'done':
            self.cmd_pub.publish(cmd)
            return

        if self.state == 'drive':
            if self.elapsed_in_state() < self.drive_duration:
                cmd.linear.x = self.get_parameter('speed').value
            else:
                self.state = 'turn'
                self.state_started = self.get_clock().now()

        elif self.state == 'turn':
            if self.elapsed_in_state() < self.turn_duration:
                cmd.angular.z = self.get_parameter('turn_speed').value
            else:
                self.sides_done += 1
                self.get_logger().info(f'Corner {self.sides_done} of 4 complete')

                if self.sides_done >= 4:
                    self.state = 'done'
                    self.report_error()
                else:
                    self.state = 'drive'
                    self.state_started = self.get_clock().now()

        self.cmd_pub.publish(cmd)

    def report_error(self):
        """Compare where the robot started with where it ended up."""
        self.cmd_pub.publish(Twist())  # stop

        if self.start_pose is None or self.current_pose is None:
            self.get_logger().warn('No odometry received - cannot measure error.')
            return

        dx = self.current_pose.position.x - self.start_pose.position.x
        dy = self.current_pose.position.y - self.start_pose.position.y
        error = math.hypot(dx, dy)

        self.get_logger().info('=' * 58)
        self.get_logger().info('Square complete. In theory it returned to the start.')
        self.get_logger().info(
            f'  Offset from start: dx={dx:+.3f} m, dy={dy:+.3f} m')
        self.get_logger().info(f'  Total position error: {error:.3f} m')
        self.get_logger().info('')
        self.get_logger().info('  And that is only the error odometry ADMITS to.')
        self.get_logger().info('  True error vs. Gazebo ground truth is larger:')
        self.get_logger().info('  odometry cannot see its own drift.')
        self.get_logger().info('=' * 58)


def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
