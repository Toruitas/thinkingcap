import serial
import argparse
import math
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import asyncio
import time
from contextvars import ContextVar

# Arduino constants
ARD_PORT = "/dev/ttyACM0" # COM3 or /dev/ttyACM0
# Osc server constants
IP = "127.0.0.1"
OSC_PORT = 5005

# Context Vars work great with asyncio
focused = ContextVar("focused", default=False)  # focused = False
wearing = ContextVar("wearing", default=False)  # wearing = False
running = ContextVar("running", default=True)  # running = True


def eeg_handler(unused_addr, args, ch1, ch2, ch3, ch4):
    """
    Handles raw electrical data handed over from the 4 electrodes.
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

async def loop1():
    for i in range(10):
        print(f"Loop {i}")
        await asyncio.sleep(1)

async def loop(ser):
    # ser = serial.Serial(ARD_PORT, baudrate=9600, timeout=1)  # timeout 1 second. This resets the Ard when it connects.

    while running.get():
        user_input = input('Test control of Arduino? f for focus; anything else to quit.')

        if user_input == 'f':
            # This should change "focused" to true here and on the Ard.
            # Through setting "focused" on the Ard, it will vibrate, light up, etc.
            focused.set(True)
            ser.write(b'f')

        if user_input != 'f':
            running.set(False)   # shut it down on next loop
            ser.write(b'x')  # o for off.


async def init_main():
    """
    https://docs.python.org/3.7/library/contextvars.html
    https://python-osc.readthedocs.io/en/latest/server.html#async-server
    https://web.archive.org/web/20170809181820/http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers

    :return:
    """
    #ser = serial.Serial(ARD_PORT, baudrate=9600, timeout=1)

    dispatcher = Dispatcher()
    dispatcher.map("/muse/elements/experimental/concentration", concentration_handler, "Concentration")

    # creates a server that's Async.
    server = osc_server.AsyncIOOSCUDPServer((IP, OSC_PORT), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop1()  # Enter main loop of program. This runs and the transport also runs.

    transport.close()  # Clean up serve endpoint


asyncio.run(init_main())


def eeg_process(on:bool):
    """

    :param on:
    :return:
    """
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--ip",
    #                     default="127.0.0.1",
    #                     help="The ip to listen on")
    # parser.add_argument("--port",
    #                     type=int,
    #                     default=5000,
    #                     help="The port to listen on")
    # args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.map("/debug", print)
    # dispatcher.map("/muse/eeg", eeg_handler, "EEG")
    dispatcher.map("/muse/elements/experimental/concentration", eeg_handler, "EEG")

    server = osc_server.AsyncIOOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()


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


