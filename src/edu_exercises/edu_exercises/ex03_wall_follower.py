"""EXERCISE 03 (capstone) - closed-loop control: follow a wall.

GOAL
    Keep the robot driving forward at a fixed distance from the wall on
    its left, using a proportional controller.

    Unlike the obstacle avoider, this is not a reaction - it is a
    *regulator*. It has a target (the desired distance), it measures the
    error, and it steers in proportion to that error, continuously.

THE CONTROL LAW
    error      = desired_distance - measured_left_distance
    angular.z  = -kp * error

    If the robot is too far from the wall, the error is negative, so
    angular.z is positive and it turns left, towards the wall. Too close,
    and it turns away. kp sets how hard it corrects.

RUN IT
    Terminal 1:  ros2 launch edu_bringup simulation.launch.py
    Terminal 2:  ros2 run edu_exercises ex03_wall_follower

    Drive the robot near a wall first (with teleop) so it has something
    to follow.

EXPERIMENT - this is the real lesson
    ros2 param set /wall_follower kp 0.5    # sluggish: drifts off slowly
    ros2 param set /wall_follower kp 3.0    # snappy, tracks well
    ros2 param set /wall_follower kp 15.0   # unstable: oscillates wildly

    Every feedback controller in engineering has this trade-off. Too
    little gain and it never gets there; too much and it overshoots and
    rings. Find the largest kp that still looks smooth.

STUCK?
    edu_exercises/solutions/ex03_wall_follower.py
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

        self.declare_parameter('desired_distance', 1.0)  # m from the wall
        self.declare_parameter('forward_speed', 0.3)     # m/s
        self.declare_parameter('kp', 2.0)                # proportional gain
        self.declare_parameter('max_angular', 1.5)       # rad/s clamp

        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.scan_sub = self.create_subscription(
            LaserScan, 'scan', self.on_scan, sensor_qos)

        # TODO 1: create the publisher for Twist messages on 'cmd_vel'.

        self.scan = None
        self.timer = self.create_timer(0.1, self.control_step)
        self.get_logger().info('Wall follower started')

    def on_scan(self, msg):
        self.scan = msg

    def distance_at(self, angle_deg, width_deg=20.0):
        """Closest valid reading in a wedge centred on angle_deg.

        Provided for you - it is the same helper as in the worked
        examples. 0 deg is ahead, +90 deg is left.
        """
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
            if distance < self.scan.range_min or distance > self.scan.range_max:
                continue
            closest = min(closest, distance)

        return closest

    def control_step(self):
        cmd = Twist()

        # TODO 2: safety. If self.scan is None, publish the empty (zero)
        #   cmd and return. Never let the robot run on stale commands.

        # TODO 3: measure. Get the distance to the wall on the LEFT
        #   (90 degrees) and the distance straight AHEAD (0 degrees).

        # TODO 4: handle the inside corner. If the distance ahead is less
        #   than 0.8 m, a wall is blocking the path: stop going forward
        #   (linear.x = 0.0) and turn right hard (negative angular.z,
        #   about -1.0), then publish and return. Without this the robot
        #   drives straight into every corner while dutifully regulating
        #   its distance to the left-hand wall.

        # TODO 5: handle losing the wall. If the left distance is inf,
        #   there is no wall to follow. Drive gently forward and curve
        #   left to search for one, then publish and return.

        # TODO 6: the proportional control law.
        #   error = desired_distance - left_distance
        #   angular_z = -kp * error
        #
        #   Then CLAMP it to +/- max_angular before publishing:
        #     angular_z = max(-max_angular, min(max_angular, angular_z))
        #   An unclamped controller commands absurd turn rates the moment
        #   the measurement jumps, and the robot spins on the spot.

        # TODO 7: set cmd.linear.x to forward_speed, cmd.angular.z to your
        #   clamped value, and publish.
        pass

    def stop_robot(self):
        # TODO 8: publish an empty Twist so the robot does not keep
        #   rolling after you press Ctrl-C.
        pass


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
