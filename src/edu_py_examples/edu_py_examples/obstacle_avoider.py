"""Module 04 - the first real robot controller: sense, think, act.

Every autonomous robot, from this 90-line node up to a self-driving car,
runs the same loop:

    sense   read the sensors        (subscribe to /scan)
    think   decide what to do       (the logic in control_step)
    act     command the actuators   (publish to /cmd_vel)

Run the simulation, then:
    ros2 run edu_py_examples obstacle_avoider

The robot drives forward until something is too close, then turns away.
That is all. It is a *reactive* controller: no map, no memory, no plan -
just a direct response to what it sees right now.

Watch it long enough and you will see the limitation: in a corner it can
oscillate, and it will happily drive in circles forever because it has no
idea where it has already been. Fixing that needs a map and a planner,
which is exactly what Nav2 provides in 04-navigation.md.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan


class ObstacleAvoider(Node):
    """Drives forward, turning away from whatever is closest."""

    def __init__(self):
        super().__init__('obstacle_avoider')

        # Tunable from the command line - try it while the robot drives:
        #   ros2 param set /obstacle_avoider forward_speed 0.8
        self.declare_parameter('forward_speed', 0.4)     # m/s
        self.declare_parameter('turn_speed', 0.8)        # rad/s
        self.declare_parameter('stop_distance', 0.9)     # m
        self.declare_parameter('front_angle', 60.0)      # deg, full width

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

        # Deliberately decoupled: the control loop runs at a fixed 10 Hz
        # rather than "whenever a scan arrives". A controller whose rate
        # depends on sensor timing is one that changes behaviour when the
        # sensor does - and it stops commanding entirely if the sensor
        # dies, instead of noticing and stopping on purpose (see below).
        self.timer = self.create_timer(0.1, self.control_step)

        self.get_logger().info('Obstacle avoider running. Ctrl-C to stop.')

    def on_scan(self, msg):
        self.scan = msg

    def min_distance_in_sector(self, centre_deg, width_deg):
        """Closest valid return within a sector, or inf if the sector is clear."""
        centre = math.radians(centre_deg)
        half_width = math.radians(width_deg) / 2.0

        closest = float('inf')
        for i, distance in enumerate(self.scan.ranges):
            angle = self.scan.angle_min + i * self.scan.angle_increment
            angle = math.atan2(math.sin(angle), math.cos(angle))
            if abs(angle - centre) > half_width:
                continue
            if math.isinf(distance) or math.isnan(distance):
                continue
            if distance < self.scan.range_min or distance > self.scan.range_max:
                continue
            closest = min(closest, distance)

        return closest

    def control_step(self):
        """One iteration of sense - think - act."""
        cmd = Twist()

        # --- Safety first ---------------------------------------------
        # No data means stop, not "carry on as before". A robot that keeps
        # executing its last command after its sensor fails is a robot
        # that drives into a wall. This is the habit worth forming early.
        if self.scan is None:
            self.cmd_pub.publish(cmd)  # all-zero Twist == stop
            return

        front_width = self.get_parameter('front_angle').value
        stop_distance = self.get_parameter('stop_distance').value

        front = self.min_distance_in_sector(0.0, front_width)
        left = self.min_distance_in_sector(60.0, 60.0)
        right = self.min_distance_in_sector(-60.0, 60.0)

        # --- Think -----------------------------------------------------
        if front > stop_distance:
            # Clear ahead: drive.
            cmd.linear.x = self.get_parameter('forward_speed').value
            cmd.angular.z = 0.0
        else:
            # Blocked: turn on the spot, towards whichever side has more
            # room. Turning while still moving forward would clip the
            # obstacle we are trying to avoid.
            cmd.linear.x = 0.0
            turn = self.get_parameter('turn_speed').value

            # Positive angular.z is counter-clockwise, i.e. to the left.
            cmd.angular.z = turn if left > right else -turn

            self.get_logger().info(
                f'Blocked at {front:.2f}m - turning '
                f'{"left" if cmd.angular.z > 0 else "right"}',
                throttle_duration_sec=1.0,  # do not flood the log
            )

        # --- Act -------------------------------------------------------
        self.cmd_pub.publish(cmd)

    def stop_robot(self):
        """Publish a zero velocity so the robot does not coast on exit.

        Gazebo's diff-drive plugin holds the last command it received, so
        without this the robot keeps rolling after the node is gone.
        """
        self.cmd_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoider()
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
