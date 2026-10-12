"""Module 03 - watch the robot's belief diverge from reality.

Run the simulation, then:
    ros2 run edu_py_examples collision_monitor

Drive the robot into a wall and watch what it reports.

WHAT THIS NODE IS FOR

A robot has two different answers to "where am I?":

  /odom        what the WHEELS say. Integrated from wheel rotation, so
               it is smooth, always available -- and wrong the moment a
               wheel turns without the robot moving.
  /odom_truth  what Gazebo actually simulated. A real robot cannot know
               this; a simulator can, which is exactly why simulators
               are useful for learning.

Drive into a wall and the two diverge in the most instructive way
possible: the wheels keep turning, odometry keeps counting, and the robot
goes nowhere. This node makes that visible three ways at once --

  * a terminal warning, so you cannot miss it
  * /collision_flags  (std_msgs/Bool), for your own code to react to
  * an RViz marker on /collision_markers at the robot's true position

WHY IT MATTERS

Everything downstream of odometry inherits its lies. The SLAM module
feeds odometry to a scan matcher as a starting guess; a guess that claims
two metres of travel that never happened is worse than no guess at all.
Detecting slip is the first step to not trusting it.
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Bool, String
from visualization_msgs.msg import Marker


class CollisionMonitor(Node):
    """Compares commanded motion, wheel odometry and ground truth."""

    def __init__(self):
        super().__init__('collision_monitor')

        # How far the two estimates may disagree before we call it slip.
        # Both are in metres per second, compared over one check period.
        self.declare_parameter('slip_threshold', 0.08)
        # Ignore slip while the robot is barely moving: at a standstill
        # the two estimates differ by noise alone and we would cry wolf.
        self.declare_parameter('min_commanded_speed', 0.05)
        self.declare_parameter('check_period', 0.5)

        self.cmd = Twist()
        self.odom = None          # wheel-based belief
        self.truth = None         # what Gazebo simulated
        self.prev_odom_xy = None
        self.prev_truth_xy = None
        # Where each frame started, so drift is measured as a difference
        # in distance travelled rather than as a difference in position.
        self.odom_origin = None
        self.truth_origin = None
        self.in_collision = False

        self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        # Ground truth is published by the second OdometryPublisher in
        # the robot's SDF. If this topic never arrives the node still
        # works -- it just cannot compare, and says so.
        self.create_subscription(Odometry, 'odom_truth', self.on_truth, 10)

        self.flag_pub = self.create_publisher(Bool, 'collision_flags', 10)
        self.text_pub = self.create_publisher(String, 'collision_text', 10)
        self.marker_pub = self.create_publisher(Marker, 'collision_markers', 10)

        period = self.get_parameter('check_period').value
        self.timer = self.create_timer(period, self.check)

        self.warned_no_truth = False
        self.get_logger().info(
            'Collision monitor running. Drive into a wall to see it fire.')

    def on_cmd(self, msg):
        self.cmd = msg

    def on_odom(self, msg):
        self.odom = msg

    def on_truth(self, msg):
        self.truth = msg

    @staticmethod
    def _xy(odom):
        return (odom.pose.pose.position.x, odom.pose.pose.position.y)

    @staticmethod
    def _speed(now, prev, dt):
        """Distance covered between two samples, as a speed."""
        if prev is None or dt <= 0.0:
            return None
        return math.dist(now, prev) / dt

    def check(self):
        dt = self.get_parameter('check_period').value

        if self.odom is None:
            return

        if self.truth is None:
            if not self.warned_no_truth:
                self.get_logger().warn(
                    'No /odom_truth yet. Ground truth comes from the robot '
                    'SDF; rebuild the workspace if you just pulled.')
                self.warned_no_truth = True
            return

        odom_xy = self._xy(self.odom)
        truth_xy = self._xy(self.truth)

        odom_speed = self._speed(odom_xy, self.prev_odom_xy, dt)
        truth_speed = self._speed(truth_xy, self.prev_truth_xy, dt)

        self.prev_odom_xy = odom_xy
        self.prev_truth_xy = truth_xy

        if odom_speed is None or truth_speed is None:
            return      # first sample: nothing to compare against yet

        commanded = abs(self.cmd.linear.x)
        threshold = self.get_parameter('slip_threshold').value
        min_speed = self.get_parameter('min_commanded_speed').value

        # Slip is the wheels claiming progress the world did not grant.
        # Comparing odometry against truth (rather than command against
        # truth) is what isolates it: a robot that was never commanded to
        # move is not slipping, it is parked.
        slipping = (commanded > min_speed
                    and (odom_speed - truth_speed) > threshold)

        self.publish_flag(slipping)

        if slipping and not self.in_collision:
            self.in_collision = True
            detail = (f'wheels report {odom_speed:.2f} m/s, '
                      f'robot actually moving {truth_speed:.2f} m/s')
            self.get_logger().warn(f'CONTACT / WHEEL SLIP: {detail}')
            self.get_logger().warn(
                '  Odometry is now wrong, and stays wrong: the error it '
                'just accumulated is never un-counted.')
            self.publish_text(detail)
            self.publish_marker(truth_xy, hit=True)

        elif not slipping and self.in_collision:
            self.in_collision = False
            self.get_logger().info('Clear - rolling freely again.')
            self.publish_marker(truth_xy, hit=False)

        # The running divergence, whether or not we are slipping right
        # now. This is the number module 03 is really about.
        #
        # Measured as DISPLACEMENT from each frame's own origin, not as
        # the gap between the two positions: odom starts at zero wherever
        # the robot happens to be, while truth is in world coordinates,
        # so a robot spawned at x=-4 shows a 4 m "error" before it has
        # moved at all. Comparing how far each thinks it has travelled
        # removes that offset and leaves the real drift.
        if self.odom_origin is None:
            self.odom_origin = odom_xy
            self.truth_origin = truth_xy

        odom_travelled = math.dist(odom_xy, self.odom_origin)
        truth_travelled = math.dist(truth_xy, self.truth_origin)
        drift = abs(odom_travelled - truth_travelled)

        if drift > 0.1:
            self.get_logger().info(
                f'odometry thinks it has gone {odom_travelled:.2f} m; '
                f'it has really gone {truth_travelled:.2f} m '
                f'(off by {drift:.2f} m)',
                throttle_duration_sec=5.0)

    def publish_flag(self, value):
        msg = Bool()
        msg.data = bool(value)
        self.flag_pub.publish(msg)

    def publish_text(self, detail):
        msg = String()
        msg.data = detail
        self.text_pub.publish(msg)

    def publish_marker(self, xy, hit):
        """A sphere at the robot's TRUE position when contact is detected."""
        marker = Marker()
        # 'world' is the ground-truth frame published by the SDF's second
        # OdometryPublisher; the marker belongs where the robot really is,
        # not where odometry imagines it.
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'collision'
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD if hit else Marker.DELETE
        marker.pose.position.x = xy[0]
        marker.pose.position.y = xy[1]
        marker.pose.position.z = 0.3
        marker.pose.orientation.w = 1.0
        marker.scale.x = marker.scale.y = marker.scale.z = 0.4
        marker.color.r = 1.0
        marker.color.g = 0.1
        marker.color.b = 0.1
        marker.color.a = 0.8
        self.marker_pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = CollisionMonitor()
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
