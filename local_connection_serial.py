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

# Arduino constants for dev
ARD_PORT = "/dev/ttyACM0" # COM3 or /dev/ttyACM0
# Osc server constants
IP = "127.0.0.1"
OSC_PORT = 5005

# Context Vars work great with asyncio
focused = ContextVar("focused", default=False)  # focused = False
wearing = ContextVar("wearing", default=False)  # wearing = False
hat_running = ContextVar("hat_running", default=False)  # running = True
user_override = ContextVar("user_override", default=False)  # user_override = False
connected = ContextVar("connected", default=False)
last_reading = ContextVar("last_reading", default=datetime.datetime.now())
attention_lvl = ContextVar("attn", default=0.0)  # for storing the current level of attention


def eeg_handler(unused_addr, args, ch1, ch2, ch3, ch4):
    """
    Handles raw electrical data handed over from the 4 electrodes. Not needed in current version.
    :param unused_addr:
    :param args:
    :param ch1: Left ear
    :param ch2: Left forehead
    :param ch3: Right forehead
    :param ch4: Right ear
    :return:
    """
    print("EEG (uV) per channel: ", ch1, ch2, ch3, ch4)


def concentration_handler(unused_addr, args, concentration):
    """
    This is called every time data comes in by the OSC dispatcher.
    :param unused_addr: the given address that's associated with this "view"
    :param args: anything extra
    :param concentration: values of concentration
    :return:
    """
    print("Current attention level: ", concentration)
    if concentration >= 0.5:
        focused.set(True)
        print("Focused, you bad mofo, you. Look at that.")


async def loop1():
    for i in range(10):
        print(f"Loop {i}")
        await asyncio.sleep(1)


async def loop(ser):

    while hat_running.get():
        # user_input = input('Test control of Arduino? f for focus; anything else to quit.')
        #
        # if user_input == 'f':
        #     # This should change "focused" to true here and on the Ard.
        #     # Through setting "focused" on the Ard, it will vibrate, light up, etc.
        #     focused.set(True)
        #     ser.write(b'f')
        #
        # if user_input != 'f':
        #     hat_running.set(False)   # shut it down on next loop
        #     ser.write(b'x')  # o for off.

        state = ser.readline()
        state = str(state)
        if state:
            # connection made, update the variables
            update_server_state(state)
        else:
            update_client_state(ser)
        await asyncio.sleep(50)


def update_server_state(state: str) -> dict:
    """
    Takes a new state from the Ard and mirrors it on this server.
    Uses set.state since we're in async land
    :param state: string JSON object
    :return: dict object of the state
    """
    # https://stackoverflow.com/questions/26838953/python-read-from-serial-port-and-encode-as-json
    print(state)
    state = json.loads(state)

    hat_running.set(True)
    connected.set(True)
    focused.set(state["focused"])
    wearing.set(state["wearing"])
    user_override.set(state["user_override"])
    last_reading.set(datetime.datetime.now())

    state_dict = context_vars_to_state_dict()

    # log the update to the console
    print("Server state updated to: ")
    print(state_dict)

    # no real reason to return, but doing anyway
    return state_dict


def update_client_state(ser):
    """
    Update the Arduino client.
    https://stackoverflow.com/questions/22275079/pyserial-write-wont-take-my-string
    :return:
    """
    state = context_vars_to_state_dict()
    state_json = json.dumps(state)  # dump to a JSON string

    ser.write(state_json.encode())  # encode
    # Log to the console
    print("Client state updated to: ")
    print(state_json)


def context_vars_to_state_dict() -> dict:
    """
    Convenience fn to turn the context variables into a dictionary,
    :return:
    """
    state_dict = {
        "focused": focused.get(),
        "wearing": wearing.get(),
        "hat_running": hat_running.get(),
        "connected": connected.get(),
        "user_override": user_override.get(),
        "last_reading": last_reading.get()
    }

    return state_dict


def make_connection(ser):
    """
    Using the given serial connection, attempts to start reading data. If it tries long enough, it'll time out.
    :param ser:
    :return: True if connected
    """
    print("making a connection")
    while not hat_running.get():
        state = ser.readline()
        if state:
            # connection made, update the variables
            update_server_state(state)
            print("Connected to Thinking Cap. Don't let your dreams be dreams!")
            return True
        # if timeout todo: make a timeout here for connections.


async def init_main():
    """
    https://docs.python.org/3.7/library/contextvars.html
    https://python-osc.readthedocs.io/en/latest/server.html#async-server
    https://web.archive.org/web/20170809181820/http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers

    :return:
    """
    # Prepare the serial port
    # make_connection
    ser = serial.Serial(ARD_PORT, baudrate=9600, timeout=1)
    connection_made = make_connection(ser)

    if connection_made:

        # with the connection made and inital state set, can start the main loops.

        dispatcher = Dispatcher()
        dispatcher.map("/muse/elements/experimental/concentration", concentration_handler, "Concentration")

        # creates a server that's Async.
        server = osc_server.AsyncIOOSCUDPServer((IP, OSC_PORT), dispatcher, asyncio.get_event_loop())
        transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

        await loop(ser)  # Enter main loop of program. This runs and the transport also runs.

        transport.close()  # Clean up serve endpoint


asyncio.run(init_main())


# def eeg_process(on:bool):
#     """
#
#     :param on:
#     :return:
#     """
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument("--ip",
#     #                     default="127.0.0.1",
#     #                     help="The ip to listen on")
#     # parser.add_argument("--port",
#     #                     type=int,
#     #                     default=5000,
#     #                     help="The port to listen on")
#     # args = parser.parse_args()
#
#     dispatcher = Dispatcher()
#     dispatcher.map("/debug", print)
#     # dispatcher.map("/muse/eeg", eeg_handler, "EEG")
#     dispatcher.map("/muse/elements/experimental/concentration", eeg_handler, "EEG")
#
#     server = osc_server.AsyncIOOSCUDPServer(
#         (args.ip, args.port), dispatcher)
#     print("Serving on {}".format(server.server_address))
#     server.serve_forever()


# if __name__ == "__main__":
#     ser = serial.Serial(ARD_PORT, baudrate = 9600, timeout=1)  # timeout 1 second. This resets the Ard when it connects.
#
#     while running:
#         user_input = input('Test control of Arduino? f for focus; anything else to quit.')
#
#         if user_input == 'f':
#             # This should change "focused" to true here and on the Ard.
#             # Through setting "focused" on the Ard, it will vibrate, light up, etc.
#             focused = True
#             ser.write(b'f')
#
#         if user_input != 'f':
#             running = False  # shut it down on next loop
#             ser.write(b'x')  # o for off.


