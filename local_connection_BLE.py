import json
import asyncio
import os
import time
import pickle
import requests
import random
import serial

import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART

async_state = type('', (), {})()
async_state.focused = False
async_state.focused_prev = False   # reduplication of some Arduino code
async_state.connected = False
async_state.mentally_focused = False
async_state.wearing = False
async_state.hat_running = False
async_state.user_override = False
async_state.last_reading = time.time()
async_state.attention_lvl = 0.0
async_state.running_focus_avg = []

slack_state = type('', (), {})()
slack_state.slack_do_update = False
slack_state.slack_updated = time.time()
slack_state.slack_update_period = 10  # 900 seconds = 15 minutes is about right. Even 10 minutes feels too spammy.
slack_state.slack_hooks_path = os.environ["SLACK_HOOKS_PATH"]
slack_state.username = "Stuart"
slack_state.target_rate = 0.99

sync_state_seconds = 0.250  # 250ms between updates. Same on the Arduino. BLE isn't as fast as Serial, evidently.
pickle_path = ""

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()

# Serial for updating the Boss Box Bot
ARD_PORT = "/dev/ttyACM0" # COM3 or /dev/ttyACM0


def update_slack(ser):
    """
    https://stackoverflow.com/questions/11322430/how-to-send-post-request

    This function only fires every so often.
    It sends a message to Slack letting everybody in the channel know what kind of focused state you're in. Oh yes,
    it's even worse than the open office. Now you can't even hide your brain.

    This also updates the Boss Box Bot.

    :return:
    """
    slack_state.slack_do_update = False
    # potential messages
    slack_messages = {
        "focused": [
            {"text": f"{slack_state.username} is focused and working super hard!"},
            {"text": f"@boss, take a look at {slack_state.username}. Just look at him go."},
            {"text": f"{slack_state.username} is way too important to fire."},
            {"text": f"{slack_state.username} is in the zone. Don't touch!"},
            {"text": f"{slack_state.username} is a model worker. Look at him. ARE YOU THAT GOOD?!"},
        ],
        "unfocused": [
            {"text": f"{slack_state.username} is open for watercooler conversations!"},
            {"text": f"@boss, take a look at {slack_state.username}. Slacking again."},
            {"text": f"{slack_state.username}'s time is about up at this office."},
            {"text": f"@{slack_state.username}, please see the boss for an evaluation."},
            {"text": f"Why is {slack_state.username} even here? This is the productivity of a drunk chimp."},
        ]
    }
    # choose the batch to randomly select from
    if async_state.focused:
        message_list = slack_messages["focused"]
    else:
        message_list = slack_messages["unfocused"]
    message = random.choice(message_list)

    # special message for using the override to look focused.
    if async_state.focused and not async_state.mentally_focused:
        message["text"] += "Clearly hit the override for this time."

    # now add the running average to the message.
    # get the running average from the async_state.running_focus_avg
    if len(async_state.running_focus_avg)>0:
        concentration_rate = sum(async_state.running_focus_avg)/len(async_state.running_focus_avg)
    else:
        concentration_rate = "mystery"

    message["text"] += f" Currently at a {concentration_rate} concentration rate. Compare that to the target of " \
               f"{slack_state.target_rate}, and use peer pressure appropriately."
    try:
        request = requests.post(slack_state.slack_hooks_path, json=message)
        print("Slack updated!")
        # print(request.status_code, request.reason)
    except:
        # we don't want to block things, so... carry on, young script
        print("Failed to update Slack")
        pass
    # now update the BossBoxBot
    state = {
        "concentration_rate": concentration_rate,
        "target": slack_state.target_rate
    }
    state_json = json.dumps(state)
    try:
        ser.write(state_json.encode())
        print("Boss box bot updated")
    except:
        print("Failed to update Boss Bot Box")
        return


def update_server_state(received_state: str):
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
        received_state = json.loads(received_state)
        print(received_state)

        if type(received_state) == dict:

            async_state.hat_running = True
            async_state.connected = True
            async_state.focused_prev = async_state.focused
            async_state.focused = received_state["focused"]
            async_state.wearing = received_state["wearing"]
            async_state.user_override = received_state["userOverride"]
            async_state.last_reading = time.time()

            # if there's a change in status
            if async_state.focused != async_state.focused_prev:
                slack_state.slack_do_update = True

            state_dict = context_vars_to_state_dict(async_state)

            # log the update to the console
            print("Server state updated to: ")
            print(state_dict)

            # no real reason to return, but doing anyway
            return state_dict
        else:
            print(received_state)
    except json.decoder.JSONDecodeError as error:
        print(received_state)  # this just prints whatever the message actually is


def update_client_state(uart_conn):
    """
    Update the Arduino client.
    :return:
    """

    state = context_vars_to_state_dict(async_state)
    state_json = json.dumps(state, sort_keys=True, default=str)  # dump to a JSON string according to https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable

    uart_conn.write(state_json.encode())  # encode
    # Log to the console
    print("Client state updated to: ")
    print(state_json)


def update_focused():
    try:
        with open(pickle_path+'concentration.pkl', 'rb') as pickle_file:
            concentration_dict = pickle.load(pickle_file)
        concentration_level = concentration_dict["concentration"]
        async_state.running_focus_avg.append(concentration_level)
        if concentration_level > 0.5:
            async_state.mentally_focused = True
        else:
            async_state.mentally_focused = False
    except FileNotFoundError:
        return
    except pickle.UnpicklingError:
        # just can't open sometimes. Skip it and try later.
        return
    except EOFError:
        # just ignore
        return


def context_vars_to_state_dict(async_state) -> dict:
    """
    Convenience fn to turn the context variables into a dictionary,
    :return:
    """
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
        ser = serial.Serial(ARD_PORT, baudrate=9600, timeout=0.05)

        async_state.hat_running = True
        async_state.connected = True

        while async_state.hat_running:
            try:
                # if time elapsed >= update time
                if (time.time() - async_state.last_reading) > sync_state_seconds:
                    update_focused()
                    print("Waiting for update")
                    received_state = uart.read(timeout_sec=60)
                    print(received_state)
                    if received_state:
                        # connection made, update the variables
                        update_server_state(received_state)
                    update_client_state(uart)
                if slack_state.slack_do_update:
                    if time.time()-slack_state.slack_updated > slack_state.slack_update_period:
                        update_slack(ser)
            except RuntimeError:
                device.disconnect()


            # sanity check for seeing response on the BossBotBox.
            ard_resp = ser.readline()
            if ard_resp != b'\r\n' and ard_resp != b'Updating from server\r\n' and ard_resp != b'':
                print(ard_resp)
                # time.sleep(3)
    finally:
        device.disconnect()


ble.initialize()
ble.run_mainloop_with(main)