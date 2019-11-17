import serial

PORT = "COM3"
FOCUSED = False
WEARING = False
RUNNING = True

if __name__ == "__main__":
    ser = serial.Serial(PORT, baudrate = 9600, timeout=1)  # timeout 1 second. This resets the Ard when it connects.

    while RUNNING:
        user_input = input('Test control of Arduino? f for focus; anything else to quit.')

        if user_input == 'f':
            # This should change "focused" to true here and on the Ard.
            # Through setting "focused" on the Ard, it will vibrate, light up, etc.
            FOCUSED = True
            ser.write(b'f')

        if user_input != 'f':
            RUNNING = False  # shut it down on next loop
            ser.write(b'x')  # o for off.
