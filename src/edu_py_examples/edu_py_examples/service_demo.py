"""Module 01 - services: asking a question and waiting for an answer.

Topics are a broadcast: you publish and move on, never knowing who
listened. A *service* is a request/response call: one client asks, one
server answers, the client waits for the reply.

Rule of thumb for which to use:
  topic   - continuous streams. Sensor readings, velocity commands, state.
  service - occasional commands with an answer. "Reset the odometry."
            "Take a picture." "Is the gripper calibrated?"
  action  - long-running jobs you want feedback on and may cancel, such as
            "drive to the kitchen". Module 04 uses one via Nav2.

Run the server:
    ros2 run edu_py_examples service_demo

Call it from the command line, with no client code at all:
    ros2 service list
    ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 3, b: 4}"
"""

import rclpy
from example_interfaces.srv import AddTwoInts
from rclpy.node import Node


class ServiceDemo(Node):
    """A service server that adds two integers."""

    def __init__(self):
        super().__init__('service_demo')

        # create_service(srv_type, service_name, callback).
        self.service = self.create_service(
            AddTwoInts,
            'add_two_ints',
            self.on_request,
        )
        self.get_logger().info('Service /add_two_ints ready')

    def on_request(self, request, response):
        """Handle one service call.

        The request fields (a, b) and the response field (sum) come from
        the .srv definition. Inspect it with:
            ros2 interface show example_interfaces/srv/AddTwoInts

        Keep service callbacks fast. The client is blocked until you
        return, so a slow callback here stalls the caller. Anything
        long-running belongs in an action instead.
        """
        response.sum = request.a + request.b
        self.get_logger().info(
            f'Request: {request.a} + {request.b} -> {response.sum}')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ServiceDemo()
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
