import pygatt
import binascii

YOUR_DEVICE_ADDRESS = "9C:B6:D0:16:72:36"

ADDRESS_TYPE = pygatt.BLEAddressType.random

adapter = pygatt.GATTToolBackend()
adapter.start()
device = adapter.scan()
print(device)
#
# for uuid in device.discover_characteristics().keys():
#     print("Read UUID %s: %s" % (uuid, binascii.hexlify(device.char_read(uuid))))