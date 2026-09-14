"""SOLUTION 01 - battery publisher.

Run the reference solution with:
    ros2 run edu_exercises sol01_publisher

Compare it with your own version. A different-looking answer that passes
the checks in the exercise header is still a correct answer.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class BatteryPublisher(Node):

    def __init__(self):
        super().__init__('battery_publisher')

        self.publisher = self.create_publisher(Float32, 'battery', 10)
        self.timer = self.create_timer(1.0, self.on_timer)
        self.level = 100.0

        self.get_logger().info('Battery publisher started')

    def on_timer(self):
        msg = Float32()
        msg.data = self.level
        self.publisher.publish(msg)
        self.get_logger().info(f'Battery: {msg.data:.1f}%')

        # max(0.0, ...) stops the level running away into negative numbers
        # once it reaches empty.
        self.level = max(0.0, self.level - 0.5)


def main(args=None):
    rclpy.init(args=args)
    node = BatteryPublisher()
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
