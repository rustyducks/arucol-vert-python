from enum import Enum

import bitstring
import serial

class ArucolPose:
    def __init__(self, x, y ,theta):
        self.x = x
        self.y = y
        self.theta = theta

    @staticmethod
    def deserialize(bytes):
        s = bitstring.BitStream(bytes)
        theta, x, y = s.unpack('floatle:32, floatle:32, floatle:32')
        return ArucolPose(x, y, theta)

MESSAGE_TYPES = {1: ArucolPose}

class SerialCommunication:
    class RcvState(Enum):
        Idle = 0
        Start1st = 1
        Start2nd = 2
        MsgId = 3
        MsgLen = 4

    def __init__(self, port, baudrate=115200):
        self._serial = serial.Serial(port, baudrate, timeout=0.01)
        self._rcv_state = SerialCommunication.RcvState.Idle
        self._nb_bytes_expected = 1
        self._msg_id = 0
        self._msg_len = 0

    def check_msgs(self):
        while self._serial.in_waiting >= self._nb_bytes_expected:
            if self._rcv_state == SerialCommunication.RcvState.Idle:  # wait for 0XFF
                if ord(self._serial.read()) == 0xFF:
                    self._rcv_state = SerialCommunication.RcvState.Start1st
                else:                                               # fallback to Idle
                    self._rcv_state = SerialCommunication.RcvState.Idle
            elif self._rcv_state == SerialCommunication.RcvState.Start1st:
                if ord(self._serial.read()) == 0xFF:
                    self._rcv_state = SerialCommunication.RcvState.Start2nd
                else:                                               # fallback to Idle
                    self._rcv_state = SerialCommunication.RcvState.Idle
            elif self._rcv_state == SerialCommunication.RcvState.Start2nd:
                self._msg_id = ord(self._serial.read())
                self._rcv_state = SerialCommunication.RcvState.MsgId
            elif self._rcv_state == SerialCommunication.RcvState.MsgId:
                self._msg_len = ord(self._serial.read())
                self._nb_bytes_expected = self._msg_len
                self._rcv_state = SerialCommunication.RcvState.MsgLen
            elif self._rcv_state == SerialCommunication.RcvState.MsgLen:
                payload = self._serial.read(self._msg_len)       # read message content
                if self.check_checksum(self._msg_id, self._msg_len, payload):
                    try:
                        msgClass = MESSAGE_TYPES[self._msg_id]
                    except KeyError:
                        print("message id {} unknown!".format(self._msg_id))
                    msg = msgClass.deserialize(payload)
                    self._nb_bytes_expected = 1
                    self._rcv_state = SerialCommunication.RcvState.Idle
                    return msg                 # We are now synchronised !
                else:
                    return None

    @staticmethod
    def compute_checksum(msg_bytes):
        ck_a = 0
        ck_b = 0
        for c in msg_bytes:
            ck_a = (ck_a + c) % 256
            ck_b = (ck_b + ck_a) % 256
        ck = (ck_a << 8) | ck_b
        return ck

    @staticmethod
    def check_checksum(msg_id, msg_len, payload):
        # reconstruct the message from ID to payload(excluding checksum)
        to_check = chr(msg_id).encode() + chr(msg_len).encode() + payload[:-2]
        ck = SerialCommunication.compute_checksum(to_check)
        s = bitstring.BitStream(payload[-2:])
        rcv_ck, = s.unpack('uintle:16')  # coma to unpack the list as tuple
        if ck == rcv_ck:
            return True
        else:
            return False


