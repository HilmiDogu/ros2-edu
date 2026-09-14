"""Module 01 - parameters: changing a node's behaviour without editing it.

Parameters are a node's settings. They can be set on the command line, in
a launch file, or from a YAML file - and changed while the node runs.

Run it:
    ros2 run edu_py_examples parameter_demo

Inspect and change it live, from another terminal:
    ros2 param list
    ros2 param get /parameter_demo message
    ros2 param set /parameter_demo publish_rate 5.0
    ros2 param set /parameter_demo message "changed while running"

Watch the node's output react immediately. This is why robot code does
not hard-code speeds, gains or frame names: the same binary has to run on
a simulated robot and three different real ones.
"""

import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from std_msgs.msg import String


class ParameterDemo(Node):
    """Publishes a configurable message at a configurable rate."""

    def __init__(self):
        super().__init__('parameter_demo')

        # Parameters must be declared before use. The second argument is
        # the default, which also fixes the parameter's type: declaring
        # 1.0 (not 1) is what makes publish_rate a double, and
        # `ros2 param set ... 5` would then be rejected as an int.
        self.declare_parameter('message', 'configure me from the CLI')
        self.declare_parameter('publish_rate', 2.0)

        self.publisher = self.create_publisher(String, 'configured_chatter', 10)

        rate = self.get_parameter('publish_rate').value
        self.timer = self.create_timer(1.0 / rate, self.on_timer)

        # Registering a callback is what makes a parameter change take
        # effect live. Without it, `ros2 param set` would update the stored
        # value but the running timer would keep its old period - a
        # genuinely confusing bug to meet for the first time.
        self.add_on_set_parameters_callback(self.on_parameter_change)

        self.get_logger().info(
            f'Started. rate={rate} Hz, message="{self.get_parameter("message").value}"')

    def on_timer(self):
        msg = String()
        msg.data = self.get_parameter('message').value
        self.publisher.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')

    def on_parameter_change(self, params):
        """Validate and apply parameter changes as they arrive."""
        for param in params:
            if param.name == 'publish_rate':
                # Reject nonsense before it divides by zero below.
                if param.value <= 0.0:
                    self.get_logger().warn('publish_rate must be positive; rejected')
                    return SetParametersResult(successful=False)

                # Rebuild the timer at the new period.
                self.destroy_timer(self.timer)
                self.timer = self.create_timer(1.0 / param.value, self.on_timer)
                self.get_logger().info(f'publish_rate is now {param.value} Hz')

            elif param.name == 'message':
                self.get_logger().info(f'message is now "{param.value}"')

        return SetParametersResult(successful=True)


def main(args=None):
    rclpy.init(args=args)
    node = ParameterDemo()
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
