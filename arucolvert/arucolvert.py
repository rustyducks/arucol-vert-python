import time

from .communication import SerialCommunication

class ArucolVert:
    def __init__(self, serial_port, serial_baudrate=115200):
        self._communication = SerialCommunication(serial_port, serial_baudrate)

    def next_pose(self):
        while True:
            msg = self._communication.check_msgs()
            if msg is not None:
                return msg.x, msg.y, msg.theta
            time.sleep(0.001)
