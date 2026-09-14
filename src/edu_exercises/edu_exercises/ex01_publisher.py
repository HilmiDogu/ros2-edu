"""EXERCISE 01 - write your first publisher.

GOAL
    Publish the robot's "battery level" on a topic called /battery, as a
    std_msgs/Float32, at 1 Hz. Start at 100.0 and drop by 0.5 each time.

BEFORE YOU START
    Read edu_py_examples/talker.py. This exercise is deliberately the
    same shape - you are filling in the parts that file demonstrates.

RUN IT
    cd /workspace && colcon build --symlink-install && source install/setup.bash
    ros2 run edu_exercises ex01_publisher

CHECK YOUR WORK
    ros2 topic list                 # /battery should be there
    ros2 topic echo /battery        # values counting down from 100.0
    ros2 topic hz /battery          # should report about 1.0

STUCK?
    The full answer is in edu_exercises/solutions/ex01_publisher.py.
    Try for fifteen minutes before you open it.
"""

import rclpy
from rclpy.node import Node

# TODO 1: import the message type.
#   Battery level is a single decimal number, so use Float32 from
#   std_msgs.msg. The import line looks exactly like the String import in
#   talker.py, with the type name changed.


class BatteryPublisher(Node):

    def __init__(self):
        super().__init__('battery_publisher')

        # TODO 2: create the publisher.
        #   self.publisher = self.create_publisher(<type>, '<topic>', 10)
        #   The topic must be named 'battery'.

        # TODO 3: create a timer that calls self.on_timer once a second.
        #   self.timer = self.create_timer(<period_in_seconds>, self.on_timer)

        # TODO 4: initialise the battery level to 100.0.

        self.get_logger().info('Battery publisher started')

    def on_timer(self):
        # TODO 5: build the message, publish it, and log it.
        #   msg = Float32()
        #   msg.data = <the current level>
        #   self.publisher.publish(msg)
        #   self.get_logger().info(f'Battery: {msg.data:.1f}%')

        # TODO 6: decrease the level by 0.5, but do not let it go below 0.
        #   max() is the tidy way to put a floor under a value.
        pass


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
