"""Module 02 - reading a real sensor: what a laser scan actually contains.

Start the simulation first:
    ros2 launch edu_bringup simulation.launch.py

Then, in another terminal:
    ros2 run edu_py_examples lidar_monitor

This node prints a live text picture of what the lidar sees. Drive the
robot around (module 03) and watch the numbers change as it approaches a
wall - the point is to connect the 3D picture in Gazebo to the array of
floats a robot program actually receives.

A LaserScan is not a picture. It is one array of distances, `ranges`,
plus the angles that array spans. Reading index i means computing its
angle yourself:

    angle_of_ranges[i] = angle_min + i * angle_increment
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan


class LidarMonitor(Node):
    """Summarises /scan as a text readout, once a second."""

    def __init__(self):
        super().__init__('lidar_monitor')

        # Sensor data uses BEST_EFFORT reliability: for a 10 Hz scan it is
        # better to drop a late message than to re-send it. The publisher
        # (the Gazebo bridge) uses this profile, and a RELIABLE subscriber
        # would not match it - you would get no data and no error, the
        # single most common "why is my topic empty?" cause in ROS 2.
        sensor_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.subscription = self.create_subscription(
            LaserScan, 'scan', self.on_scan, sensor_qos)

        self.latest = None
        # Throttle the printing: the scan arrives at 10 Hz, which is far
        # too fast to read in a terminal.
        self.timer = self.create_timer(1.0, self.report)
        self.get_logger().info('Waiting for /scan ...')

    def on_scan(self, msg):
        self.latest = msg

    def sector_distance(self, scan, centre_deg, width_deg=30):
        """Return the closest valid reading in a sector around centre_deg.

        Angles are in the lidar's frame: 0 deg is straight ahead, +90 deg
        is to the left, -90 deg to the right.
        """
        centre = math.radians(centre_deg)
        half_width = math.radians(width_deg) / 2.0

        closest = float('inf')
        for i, distance in enumerate(scan.ranges):
            angle = scan.angle_min + i * scan.angle_increment

            # Normalise to [-pi, pi] so the comparison works across the
            # wrap-around behind the robot.
            angle = math.atan2(math.sin(angle), math.cos(angle))
            if abs(angle - centre) > half_width:
                continue

            # inf means "nothing within range", nan means "invalid reading".
            # Both are normal in real lidar data, and both will poison any
            # min()/mean() you compute without filtering them out first.
            if math.isinf(distance) or math.isnan(distance):
                continue
            if distance < scan.range_min or distance > scan.range_max:
                continue

            closest = min(closest, distance)

        return closest

    def report(self):
        if self.latest is None:
            self.get_logger().warn(
                'No scan yet. Is the simulation running, and the bridge up?')
            return

        scan = self.latest
        left = self.sector_distance(scan, 90)
        front = self.sector_distance(scan, 0)
        right = self.sector_distance(scan, -90)
        behind = self.sector_distance(scan, 180)

        def fmt(d):
            return '  --  ' if math.isinf(d) else f'{d:5.2f}m'

        self.get_logger().info(
            f'rays={len(scan.ranges):4d}  '
            f'front={fmt(front)}  left={fmt(left)}  '
            f'right={fmt(right)}  behind={fmt(behind)}')


def main(args=None):
    rclpy.init(args=args)
    node = LidarMonitor()
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
