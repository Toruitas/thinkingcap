"""Small example OSC server

This program listens to several addresses, and prints some information about
received packets.
"""
import argparse
import math
import numpy as np
import pyeeg

from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client


def normalize(L, trucs):
    for i in range(4):
        L[i] = (L[i] - trucs[i][0]) / trucs[i][1]
    return L


def compute_baseline(signal, time, newData):
    if signal.shape[0] <= (time * 220):
        signal = np.vstack((signal, newData))
    if signal.shape[0] == (time * 220):  # une minute de eeg
        print("creating baseline...")
        for i in range(4):
            baseline.append([np.mean(signal[:, i]), np.std(signal[:, i])])
        print(baselineSet)
        print(signal.shape)
        signal = np.array([]).reshape(0, 4)
        print(signal.shape)
        print('Done')
    return signal


def handler(unused_addr, args, ch1, ch2, ch3, ch4):
    baseline = args[1]  # on recupere la baseline
    baselineSet = len(baseline) == 0
    L = [ch1, ch2, ch3, ch4]
    if baselineSet:
        args[0] = compute_baseline(args[0], 10, L)

    if not baselineSet:
        args[0] = np.vstack((args[0], normalize(L, baseline)))  # On ajoute les nouvelles valeurs EEG
        data = args[0]
        buf = np.mean(data[-3 * 220:], axis=1)
        print(data.shape)
        value = pyeeg.dfa(buf.ravel())
        client.send_message("/puredata/dfa", value)


if __name__ == "__main__":
    Parser = argparse.ArgumentParser()
    Parser.add_argument("--clientip", default="192.168.0.199",
                        help="The ip of the OSC server")
    Parser.add_argument("--clientport", type=int, default=5005,
                        help="The port the OSC server is listening on")
    Parser.add_argument("--serverip",
                        default="127.0.0.1", help="The ip to listen on")
    Parser.add_argument("--serverport",
                        type=int, default=5005, help="The port to listen on")
    Args = Parser.parse_args()

    client = udp_client.SimpleUDPClient(Args.clientip, Args.clientport)

    baseline = []
    L = np.array([]).reshape(0, 4)
    dispatcher = dispatcher.Dispatcher()
    # dispatcher.map("/muse/eeg", print)
    dispatcher.map("/muse/eeg", handler, L, baseline)

    server = osc_server.ThreadingOSCUDPServer(
        (Args.serverip, Args.serverport), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()