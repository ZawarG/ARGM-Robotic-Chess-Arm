import serial

#  (\(\
# ( -.-)
# o_(")(")
# This class is used to implement serial communication with the robot
# It tells the robot to physically move when needed

# Replace 'COM4' with your Arduino's port (e.g., '/dev/ttyUSB0')
# Ensure the baud rate matches the one in your Arduino code
# arduino = serial.Serial(port='COM4', baudrate=115200, timeout=.1)

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

    def announceWinner(self, winner):
        print("This is where robot would announce a winner")
        if self.arduino:
            self.arduino.write(bytes(f"winner:{winner}\n", 'utf-8'))