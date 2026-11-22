import serial

#  (\(\
# ( -.-)
# o_(")(")
# This class is used to implement serial communication with the robot
# It tells the robot to physically move when needed

# Replace 'COM4' with your Arduino's port (e.g., '/dev/ttyUSB0')
# Ensure the baud rate matches the one in your Arduino code
# arduino = serial.Serial(port='COM4', baudrate=115200, timeout=.1)

# Move(uci) → [PickPlace(from, to), ...]
#   normal:     [pick e2 → place e4]
#   capture:    [pick d5 → place bin_k, pick e4 → place d5]   # remove victim FIRST
#   castle:     [pick e1 → place g1, pick h1 → place f1]
#   en passant: [pick d5 → place bin_p, pick e5 → place d6]
#   promotion:  [pick e7 → place bin_p, pick queen_bin → place e8]

class RobotController:
    def __init__(self, port='COM4', baudrate=115200):
        try:
            self.arduino = serial.Serial(port=port, baudrate=baudrate, timeout=.1)
            print(f"Robot connected on {port}")
        except Exception as e:
            print(f"Robot hardware not connected: {e}")
            self.arduino = None

    def movePiece(self, from_square, to_square):
        print("This is where robot would physically make the move")
        if self.arduino:
            self.arduino.write(bytes(f'from: {from_square} to: {to_square} \n', 'utf-8')) 

    def executePlan(self, steps):
        # steps is the ordered list from move_decomposition.decompose()
        for from_square, to_square in steps:
            self.movePiece(from_square, to_square)

    def announceWinner(self, winner):
        print("This is where robot would announce a winner")
        if self.arduino:
            self.arduino.write(bytes(f"winner:{winner}\n", 'utf-8'))