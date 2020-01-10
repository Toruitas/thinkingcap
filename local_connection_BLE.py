import serial
import argparse
import math
import time
import json
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import asyncio
import datetime
from contextvars import ContextVar

import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART

# Osc server constants
IP = "127.0.0.1"
OSC_PORT = 5005

# https://docs.python.org/3.7/library/contextvars.html
# Context Vars work great with asyncio
focused = ContextVar("focused", default=False)  # focused = False
# since focused can be overriden, true focus state is stored in a separate var
mentally_focused = ContextVar("mentally_focused", default=False)
wearing = ContextVar("wearing", default=False)  # wearing = False
hat_running = ContextVar("hat_running", default=False)  # running = True
user_override = ContextVar("user_override", default=False)  # user_override = False
connected = ContextVar("connected", default=False)
last_reading = ContextVar("last_reading", default=datetime.datetime.now())
attention_lvl = ContextVar("attn", default=0.0)  # for storing the current level of attention

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()

def concentration_handler(unused_addr:str, fixed_argument, concentration):
    """
    This is called every time data comes in by the OSC dispatcher.
    https://python-osc.readthedocs.io/en/latest/dispatcher.html
    :param unused_addr: the given address that's associated with this "view"
    :param args: anything extra
    :param concentration: values of concentration
    :return:
    """
    # print("Current attention level: ", concentration)
    # if concentration >= 0.5 and mentally_focused.get() is False:
    #     mentally_focused.set(True)
    #     if not user_override.get():
    #         focused.set(mentally_focused.get())
    #     print("Focused, you bad mofo, you. Look at that.")
    #     return mentally_focused.get()
    # else:
    #     mentally_focused.set(False)
    #     if not user_override.get():
    #         focused.set(mentally_focused.get())
    #     return mentally_focused.get()
    a_s = fixed_argument[0]

    print("Current attention level: ", concentration)
    if concentration >= 0.5:
        a_s.mentally_focused = True
        if not a_s.user_override:
            a_s.focused = a_s.mentally_focused
        # print("Focused, you bad mofo, you. Look at that.")
        # return a_s.mentally_focused
    else:
        a_s.mentally_focused = False
        if not a_s.user_override:
            a_s.focused = a_s.mentally_focused
        # return a_s.mentally_focused


async def loop(uart_conn, device, async_state):
    """
    Main loop of code
    :param uart_conn:  bluetooth connection
    :param device:  bluetooth device, to close if needed
    :param async_state: the state as managed on this server side.
    :return:
    """

    while async_state.hat_running:
        try:
            received_state = uart_conn.read(timeout_sec=60)
            if received_state:
                # connection made, update the variables
                update_server_state(received_state, async_state)
            else:
                update_client_state(uart_conn, async_state)
            await asyncio.sleep(.1)
        finally:
            device.disconnect()


def update_server_state(received_state: str, async_state):
    """
    Takes a new state from the Ard and mirrors it on this server.
    Uses set.state since we're in async land
    :param received_state: string JSON object
    :return: dict object of the state
    """
    # https://stackoverflow.com/questions/26838953/python-read-from-serial-port-and-encode-as-json
    try:
        # The BLUE data packet has some garbage in it. This bit cuts it down to just the JSON we want.
        first_brace = received_state.find("{")
        second_brace = received_state.find("}")  # finds first } which is what we want.
        received_state = received_state[first_brace:second_brace + 1]
        state = json.loads(received_state)
        print(received_state)
    except json.decoder.JSONDecodeError as error:
        print(received_state)  # this just prints whatever the message actually is
        return False  # early return to prevent the rest of the fn from running

    if type(received_state) == dict:
        # hat_running.set(True)
        # connected.set(True)
        # focused.set(state["focused"])
        # wearing.set(state["wearing"])
        # user_override.set(state["userOverride"])
        # last_reading.set(datetime.datetime.now())

        async_state.hat_running = True
        async_state.connected = True
        async_state.focused = received_state["focused"]
        async_state.wearing = received_state["wearing"]
        async_state.user_override = received_state["userOverride"]
        async_state.last_reading = datetime.datetime.now()

        state_dict = context_vars_to_state_dict(async_state)

        # log the update to the console
        print("Server state updated to: ")
        print(state_dict)

        # no real reason to return, but doing anyway
        return state_dict
    else:
        print(received_state)


def update_client_state(uart_conn, async_state):
    """
    Update the Arduino client.
    https://stackoverflow.com/questions/22275079/pyserial-write-wont-take-my-string
    :return:
    """
    state = context_vars_to_state_dict(async_state)
    state_json = json.dumps(state)  # dump to a JSON string

    uart_conn.write(state_json.encode())  # encode
    # Log to the console
    print("Client state updated to: ")
    print(state_json)


def context_vars_to_state_dict(async_state) -> dict:
    """
    Convenience fn to turn the context variables into a dictionary,
    :return:
    """
    # print(mentally_focused.get())
    # state_dict = {
    #     "focused": focused.get(),
    #     "mentally_focused": mentally_focused.get(),
    #     "wearing": wearing.get(),
    #     "hat_running": hat_running.get(),
    #     "connected": connected.get(),
    #     "user_override": user_override.get(),
    #     "last_reading": last_reading.get()
    # }

    state_dict = {
        "focused": async_state.focused,
        "mentally_focused": async_state.mentally_focused,
        "wearing": async_state.wearing,
        "hat_running": async_state.hat_running,
        "connected": async_state.connected,
        "user_override": async_state.user_override,
        "last_reading": async_state.last_reading
    }

    return state_dict


def make_connection():
    """
    Using the given serial connection, attempts to start reading data. If it tries long enough, it'll time out.
    :param ser:
    :return: True if connected
    Largely ripped from the uart.py example here: https://github.com/adafruit/Adafruit_Python_BluefruitLE/blob/master/examples/uart_service.py
    """
    ble.clear_cached_data()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

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

    try:
        # Wait for service discovery to complete for the UART service.  Will
        # time out after 60 seconds (specify timeout_sec parameter to override).
        print('Discovering services...')
        UART.discover(device)

        # Once service discovery is complete create an instance of the service
        # and start interacting with it.
        uart = UART(device)
        return True, uart, device
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()

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

        # Now wait up to one minute to receive data from the device.
        print('Waiting up to 60 seconds to receive data from the device...')
        received = uart.read(timeout_sec=60)
        if received is not None:
            # Received data, print it out.
            print('Received: {0}'.format(received))
        else:
            # Timeout waiting for data, None is returned.
            print('Received no data!')
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


async def init_main():
    """
    https://python-osc.readthedocs.io/en/latest/server.html#async-server
    https://web.archive.org/web/20170809181820/http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers
    https://addshore.com/2018/06/python3-using-some-shared-state-in-2-async-methods/
    :return:
    """
    # making a super ghetto state to share b/w the two async contexts
    # based on solution in https://addshore.com/2018/06/python3-using-some-shared-state-in-2-async-methods/
    async_state = type('', (), {})()
    async_state.focused = False
    async_state.mentally_focused = False
    async_state.wearing = False
    async_state.hat_running = False
    async_state.user_override = False
    async_state.last_reading = datetime.datetime.now()
    async_state.attention_lvl = 0.0

    # Prepare the serial port
    # make_connection
    ble.initialize()
    connection_made, uart_conn, device = make_connection()

    if connection_made:
        # with the connection made and inital state set, can start the main loops.
        # https://python-osc.readthedocs.io/en/latest/dispatcher.html
        # https://python-osc.readthedocs.io/en/latest/server.html#async-server
        event_loop_local = asyncio.get_event_loop()
        dispatcher = Dispatcher()
        dispatcher.map("/muse/elements/experimental/concentration", concentration_handler, async_state)
        # creates an OSC server that's Async.
        server = osc_server.AsyncIOOSCUDPServer((IP, OSC_PORT), dispatcher, event_loop_local)
        transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

        await loop(uart_conn, device, async_state)  # Enter main loop of program.
        # await ble.run_mainloop_with(loop, uart_conn, device, async_state)

        transport.close()  # Clean up serve endpoint

event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)
asyncio.run(init_main())
