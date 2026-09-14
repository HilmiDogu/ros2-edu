"""Module 01 - the smallest useful ROS 2 node: a publisher.

A *node* is one process that does one job. This one publishes a text
message onto a *topic* called 'chatter', ten times a second.

Run it:
    ros2 run edu_py_examples talker

Then, in a second terminal, watch the messages arrive without writing any
code at all:
    ros2 topic echo /chatter

That command is worth remembering: every topic in ROS 2 can be inspected
from the command line, which is how you debug a robot you did not write.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):
    """Publishes a counter onto /chatter at 10 Hz."""

    def __init__(self):
        # The string passed to super().__init__ is the node's name. It is
        # what shows up in `ros2 node list` and in the rqt_graph view.
        super().__init__('talker')

        # create_publisher(msg_type, topic_name, queue_depth).
        #
        # The queue depth (10) is how many messages ROS will buffer if the
        # subscriber is slower than the publisher. Older messages are
        # dropped once it is full - a robot usually wants the newest
        # sensor reading, not a backlog of stale ones.
        self.publisher = self.create_publisher(String, 'chatter', 10)

        # A timer is how a node does something periodically. Note what we
        # are NOT doing: there is no `while True` loop here. The node hands
        # control to rclpy, which calls us back. That is what lets one node
        # serve timers, subscriptions and services at the same time.
        timer_period = 0.1  # seconds -> 10 Hz
        self.timer = self.create_timer(timer_period, self.on_timer)

        self.count = 0
        self.get_logger().info('Talker started, publishing on /chatter')

    def on_timer(self):
        """Called by rclpy every 0.1 s."""
        msg = String()
        msg.data = f'Hello ROS 2! count = {self.count}'
        self.publisher.publish(msg)

        # get_logger() writes to the ROS log, not to plain stdout. It is
        # timestamped, it says which node it came from, and it can be
        # captured by tooling - always prefer it over print().
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count += 1


def main(args=None):
    # This four-line shape is the same in essentially every ROS 2 Python
    # node you will ever write.
    rclpy.init(args=args)
    node = Talker()
    try:
        # spin() blocks and processes callbacks until the node is killed.
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Ctrl-C is the normal way to stop a node; do not report it as a
        # crash.
        pass
    finally:
        node.destroy_node()
        # Guarded because rclpy may already have shut down during Ctrl-C.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
