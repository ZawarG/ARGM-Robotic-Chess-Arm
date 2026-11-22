import chess
import rclpy
from rclpy.node import Node

from argm_chess_interfaces.msg import ArmPlan, ArmStep, EngineMove
from src.logic.move_decomposition import decompose

#  (\(\
# ( -.-)
# o_(")(")
# Wraps move_decomposition.decompose() as a ROS node.
# In: an engine move + the position it was chosen in.
# Out: the ordered pick-and-place steps the arm must perform.


def _locationName(location):
    """decompose() yields either a square int (0..63) or an off-board string."""
    if isinstance(location, str):
        return location
    return chess.square_name(location)


class PlannerNode(Node):

    def __init__(self):
        super().__init__('planner_node')

        self.plan_pub = self.create_publisher(ArmPlan, 'arm/steps', 10)
        self.create_subscription(EngineMove, 'game/engine_move', self.onEngineMove, 10)

        self.get_logger().info('Planner ready, waiting on game/engine_move')

    def onEngineMove(self, msg):
        try:
            board = chess.Board(msg.fen)
        except ValueError as e:
            self.get_logger().error(f'Bad FEN "{msg.fen}": {e}')
            return

        try:
            move = chess.Move.from_uci(msg.uci_move)
        except chess.InvalidMoveError:
            self.get_logger().error(f'Bad UCI move "{msg.uci_move}"')
            return

        # decompose() assumes the move is legal in this position: an illegal
        # move would silently produce nonsense steps for the arm to run.
        if move not in board.legal_moves:
            self.get_logger().error(f'Move {msg.uci_move} is not legal in {msg.fen}')
            return

        plan = ArmPlan()
        plan.header.stamp = self.get_clock().now().to_msg()
        plan.uci_move = msg.uci_move
        plan.steps = [
            ArmStep(from_location=_locationName(src), to_location=_locationName(dst))
            for src, dst in decompose(board, move)
        ]

        self.plan_pub.publish(plan)

        readable = ', '.join(f'{s.from_location}->{s.to_location}' for s in plan.steps)
        self.get_logger().info(f'{msg.uci_move}: {readable}')


def main(args=None):
    rclpy.init(args=args)
    node = PlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
