"""Module 03 - TF2: where is the robot, and where is anything else?

A robot has many coordinate frames. The lidar reports distances in
lidar_link. The wheels move base_link. The map is in map. To ask "where
is that obstacle, relative to the robot's centre?" someone has to convert
between them, and doing that by hand with trigonometry is how bugs are
born.

TF2 is the library that does it. Nodes broadcast the transforms they know
about, TF2 assembles them into a tree, and any node can then ask for the
transform between *any* two frames - even ones never directly connected.

Run the simulation, then:
    ros2 run edu_py_examples tf_listener

Also worth running, for the picture rather than the numbers:
    ros2 run rqt_tf_tree rqt_tf_tree
    ros2 run tf2_tools view_frames      # writes frames.pdf
"""

import math

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener


def yaw_from_quaternion(q):
    """Extract the rotation about Z (yaw) from a quaternion.

    Orientations in ROS are quaternions, not angles: they have four
    components and no gimbal lock. For a robot driving on flat ground,
    only rotation about the vertical axis matters, and this is the
    standard way to reduce one to a single readable heading.
    """
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class TfListener(Node):
    """Reports the robot's pose by querying the TF tree."""

    def __init__(self):
        super().__init__('tf_listener')

        # Every node must agree on sim time, or lookups fail with
        # "requested time is in the future" style errors.
        self.set_parameters([rclpy.parameter.Parameter(
            'use_sim_time', rclpy.Parameter.Type.BOOL, True)])

        # The Buffer stores recent transforms; the TransformListener fills
        # it from /tf and /tf_static in the background. You always need
        # both, and the listener must be kept alive - assigning it to a
        # local variable that goes out of scope is a classic silent
        # failure.
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.timer = self.create_timer(1.0, self.report)
        self.get_logger().info('Querying the odom -> base_link transform ...')

    def report(self):
        try:
            # lookup_transform(target_frame, source_frame, time).
            #
            # Time(): "the latest available", which is what you want for a
            # live readout. Asking for a specific timestamp is stricter and
            # is what you want when pairing a transform with a particular
            # sensor reading.
            transform = self.tf_buffer.lookup_transform(
                'odom', 'base_link', rclpy.time.Time())

        except Exception as exc:
            # Expect this for the first second or two: the buffer starts
            # empty and needs transforms to arrive before it can answer.
            self.get_logger().warn(
                f'Transform not available yet: {exc}', throttle_duration_sec=5.0)
            return

        t = transform.transform.translation
        yaw = yaw_from_quaternion(transform.transform.rotation)

        self.get_logger().info(
            f'base_link in odom:  x={t.x:6.2f}m  y={t.y:6.2f}m  '
            f'heading={math.degrees(yaw):7.1f}deg')


def main(args=None):
    rclpy.init(args=args)
    node = TfListener()
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
