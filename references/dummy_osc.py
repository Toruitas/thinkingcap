"""Small example OSC client
This program sends 10 random values between 0.0 and 1.0 to the /filter address,
waiting for 1 seconds between each value.
"""
import argparse
import random
import time

from pythonosc import osc_message_builder
from pythonosc import udp_client

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--ip", default="127.0.0.1",
    #                     help="The ip of the OSC server")
    # parser.add_argument("--port", type=int, default=5005,
    #                     help="The port the OSC server is listening on")
    # args = parser.parse_args()

    client = udp_client.SimpleUDPClient("127.0.0.1", 5005)

    from pythonosc import osc_message_builder
    from pythonosc import udp_client

    # client = udp_client.UDPClient('localhost', 5005)
    msg = osc_message_builder.OscMessageBuilder(address="/muse/elements/experimental/concentration")
    msg = msg.build()
    print('Sending')
    client.send(msg)

    for x in range(10):
        client.send_message("/muse/elements/experimental/concentration", random.random())
        time.sleep(1)