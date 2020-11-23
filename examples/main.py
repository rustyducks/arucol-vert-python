import arucolvert
import time

if __name__ == "__main__":
    av = arucolvert.ArucolVert("/dev/ttyUSB1")
    while True:
        print(av.next_pose())
        time.sleep(0.1)