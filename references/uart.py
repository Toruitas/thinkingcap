# https://arduino.stackexchange.com/questions/51548/how-to-send-data-to-adafruit-bluefruit-feather-32u4-over-bluetooth/51584
# https://learn.adafruit.com/bluefruit-nrf52-feather-learning-guide/bleclientuart
# https://learn.adafruit.com/bluefruit-nrf52-feather-learning-guide/bleuart
# https://github.com/adafruit/adafruit-bluefruit-le-desktop
# https://learn.adafruit.com/bluefruit-le-python-library/overview
# https://learn.adafruit.com/introduction-to-bluetooth-low-energy/introduction
# https://www.hackster.io/gerrikoiot/ble-led-controller-feather-32u4-bluefruit-le-mit-app-inv-75163d
# https://docs.ubuntu.com/core/en/stacks/bluetooth/bluez/docs/install-bluez
# Looks like we can install the adafruit BLEU library on the machine and still use the typical C on the Arduino
# https://github.com/adafruit/Adafruit_Python_BluefruitLE/blob/master/examples/uart_service.py
# https://stackoverflow.com/questions/26678457/how-do-i-install-python3-gi-within-virtualenv/43808204#43808204
# https://askubuntu.com/questions/1057832/how-to-install-gi-for-anaconda-python3-6 <--- this finally worked for the damn GI package
# https://forums.adafruit.com/viewtopic.php?t=94337
# https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation

import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART

import json



# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()

send_this = {
    "banana":"rama",
    "super":"fly"
}

# Main function implements the program logic so it can run in a background
# thread.  Most platforms require the main thread to handle GUI events and other
# asyncronous events like BLE actions.  All of the threading logic is taken care
# of automatically though and you just need to provide a main function that uses
# the BLE provider.
def main():
    # Clear any cached data because both bluez and CoreBluetooth have issues with
    # caching data and it going stale.
    ble.clear_cached_data()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print('Disconnecting any connected UART devices...')
    UART.disconnect_devices()

    # Scan for UART devices.
    print('Searching for UART device...')
    try:
        adapter.start_scan()
        # Search for the first UART device found (will time out after 60 seconds
        # but you can specify an optional timeout_sec parameter to change it).
        device = UART.find_device()
        if device is None:
            raise RuntimeError('Failed to find UART device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()

    print('Connecting to device...')
    device.connect()  # Will time out after 60 seconds, specify timeout_sec parameter
                      # to change the timeout.

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    try:
        # Wait for service discovery to complete for the UART service.  Will
        # time out after 60 seconds (specify timeout_sec parameter to override).
        print('Discovering services...')
        UART.discover(device)

        # Once service discovery is complete create an instance of the service
        # and start interacting with it.
        uart = UART(device)

        state_json = json.dumps(send_this)
        # Write a string to the TX characteristic.
        uart.write(state_json.encode())
        print("Sent the state to the device.")

        # Now wait up to one minute to receive data from the device.
        print('Waiting up to 60 seconds to receive data from the device...')
        received = uart.read(timeout_sec=60)
        first_brace = received.find("{")
        second_brace = received.find("}")  # finds first
        received = received[first_brace:second_brace+1]
        # garbage_starts = received.find("Ñ")

        # Ñ ÅKéB4} Ñ ÅKéB4}
        # print(received[:garbage_starts])
        print(received)
        state = json.loads(received)
        print(state)
        if received is not None:
            # Received data, print it out.
            print('Received: {0}'.format(state))
        else:
            # Timeout waiting for data, None is returned.
            print('Received no data!')
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


# Initialize the BLE system.  MUST be called before other BLE calls!
ble.initialize()

# Start the mainloop to process BLE events, and run the provided function in
# a background thread.  When the provided main function stops running, returns
# an integer status code, or throws an error the program will exit.
ble.run_mainloop_with(main)