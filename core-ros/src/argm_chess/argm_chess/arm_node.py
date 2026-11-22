import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from argm_chess_interfaces.msg import ArmPlan

#  (\(\
# ( -.-)
# o_(")(")
# Executes an ArmPlan on the physical arm.
#
# With dry_run true (the default) the steps are only logged, so the whole
# pipeline can run on a machine with no arm attached. That is the only way
# to run this inside Docker on macOS, which cannot pass serial devices
# into a container.


class ArmNode(Node):

    def __init__(self):
        super().__init__('arm_node')

        self.declare_parameter('dry_run', True)
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)

        self.dry_run = self.get_parameter('dry_run').value
        self.robot = None

        if self.dry_run:
            self.get_logger().info('Dry run: steps will be logged, not sent to the arm')
        else:
            # Imported lazily: pyserial only has to be usable when we really
            # intend to talk to hardware.
            from src.hardware.robot import RobotController
            port = self.get_parameter('port').value
            baudrate = self.get_parameter('baudrate').value
            self.robot = RobotController(port=port, baudrate=baudrate)

        self.status_pub = self.create_publisher(String, 'arm/status', 10)
        self.create_subscription(ArmPlan, 'arm/steps', self.onPlan, 10)

        self.get_logger().info('Arm ready, waiting on arm/steps')

    def onPlan(self, plan):
        self.publishStatus(f'executing {plan.uci_move}')

        for i, step in enumerate(plan.steps, start=1):
            self.get_logger().info(
                f'step {i}/{len(plan.steps)}: {step.from_location} -> {step.to_location}')
            if self.robot:
                self.robot.movePiece(step.from_location, step.to_location)

        self.publishStatus(f'done {plan.uci_move}')

    def publishStatus(self, text):
        self.status_pub.publish(String(data=text))


def main(args=None):
    rclpy.init(args=args)
    node = ArmNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
