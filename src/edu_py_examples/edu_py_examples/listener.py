"""Module 01 - the other half of the pair: a subscriber.

Run this alongside the talker:
    ros2 run edu_py_examples listener

The two nodes were written separately, never reference each other, and
were started independently. They connect purely because they agree on a
topic name and a message type. That decoupling is the central idea of
ROS: you can replace the talker with a real sensor and the listener will
neither know nor care.

Try it: kill the talker and watch the listener sit patiently. Restart the
talker and the messages resume. Nothing needed restarting in between.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Listener(Node):
    """Subscribes to /chatter and logs whatever arrives."""

    def __init__(self):
        super().__init__('listener')

        # create_subscription(msg_type, topic, callback, queue_depth).
        #
        # The message type and topic name must match the publisher exactly.
        # A mismatch is the most common beginner bug, and it fails silently:
        # you get no error, just no messages. `ros2 topic info /chatter`
        # shows the publisher and subscriber counts and is how you catch it.
        self.subscription = self.create_subscription(
            String,
            'chatter',
            self.on_message,
            10,
        )
        self.get_logger().info('Listener started, waiting on /chatter')

    def on_message(self, msg):
        """Called by rclpy once per message received."""
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = Listener()
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
