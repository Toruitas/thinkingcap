import serial
import time


"""
This code tests sending text data over Bluetooth. This sends data over Serial which the Bluefruit echoes back over BLE.
"""

if __name__ =="__main__":
    ARD_PORT = "/dev/ttyACM0"  # COM3 or /dev/ttyACM0

    ser = serial.Serial(ARD_PORT, baudrate=9600, timeout=1)
    i = 0
    while True:
        ser.write(f"Sent a {i} over serial")
        i += 1
        time.sleep(1)
