from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import asyncio
import pickle

# Osc server constants
IP = "127.0.0.1"
OSC_PORT = 5005

pickle_path = ""

def concentration_handler(unused_addr:str, concentration):
    """
    This is called every time data comes in by the OSC dispatcher.
    It saves the simple float (0 to 1.0) in concentration.pkl for reading in local_connection_BLE.py
    https://python-osc.readthedocs.io/en/latest/dispatcher.html
    :param unused_addr: the given address that's associated with this "view"
    :param args: anything extra
    :param concentration: values of concentration
    :return:
    """
    print("Current attention level: ", concentration)
    concentration_dict = {"concentration": concentration}
    # now write concentration to a file. Pickle.
    pickle_file = open(pickle_path+"concentration.pkl", 'wb')
    pickle.dump(concentration_dict, pickle_file)
    pickle_file.close()


async def dummy_loop():
    """
    This loop is needed to keep the program running forever.
    :return:
    """
    while True:
        await asyncio.sleep(1)


async def init_main():
    """
    https://python-osc.readthedocs.io/en/latest/server.html#async-server
    https://web.archive.org/web/20170809181820/http://developer.choosemuse.com/research-tools-example/grabbing-data-from-museio-a-few-simple-examples-of-muse-osc-servers
    https://addshore.com/2018/06/python3-using-some-shared-state-in-2-async-methods/
    :return:
    """
    # with the connection made and inital state set, can start the main loops.
    # https://python-osc.readthedocs.io/en/latest/dispatcher.html
    # https://python-osc.readthedocs.io/en/latest/server.html#async-server
    event_loop_local = asyncio.get_event_loop()
    dispatcher = Dispatcher()
    dispatcher.map("/muse/elements/experimental/concentration", concentration_handler)
    # creates an OSC server that's Async.
    server = osc_server.AsyncIOOSCUDPServer((IP, OSC_PORT), dispatcher, event_loop_local)
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    print("OSC server running.")

    await dummy_loop()

    transport.close()  # Clean up server endpoint

event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)
asyncio.run(init_main())  # run the main loop