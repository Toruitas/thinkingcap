# This connects Python to Arduino
# Remember to have the Arduino serial terminal closed
# Original learnings from: https://www.youtube.com/watch?v=WV4U51TlRaQ

import serial
import time
import csv

NUM_POINTS = 10
NUM_ROWS = 100
NUM_VARS = 4
OPERATOR = "Bob"
TYPE = "VOLTAGE"
PORT = "COM3"

ser = serial.Serial(PORT, baudrate = 9600, timeout=1)  # timeout 1 second. This resets the Ard when it connects.

time.sleep(1)  # give 1 second for the Ard to initialize fully before the user can ask for data.

def get_values(time_stamp) -> int:
    """
    Send g to the Arduino, which it understands as the signal to write data to serial.
    This data is decoded and 
    """
    if not time_stamp:
        ser.write(b'g')  # b for byte, writing a write to serial bus. 
        arduino_data = ser.readline().decode().split("\r\n") # split data by this: ['339', '']
        arduino_output = arduino_data[0]
        # print(type(arduino_data))
    
    else:
        ser.write(b'c')
        arduino_output = ser.readline().decode().split('-')

    return arduino_output

while True:
    user_input = input('Get data points?')

    if user_input == 'y':
        time_stamp = False
        with open('data_file.csv','w') as csvfile:  # w for write, a for 
            data_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            # put together a row.

            for row in range(NUM_ROWS):
                data_list = []
                for point in range(NUM_POINTS):
                    data = get_values(time_stamp)
                    data = int(data)  # 
                    data_list.append(data)
                print(sum(data_list)/len(data_list))  # calc the avg for the row
                data_writer.writerow(data_list)  # write the row of data to the csv
                print(data_list)
    
    if user_input == "c":
        time_stamp = True
        data = get_values(time_stamp)
        data_point = data[0]
        time_collected = data[1]
        time_collected = time_collected.strip()
        unit_time = time_collected[-2:]
        delta_time = time_collected[:-2]

        if unit_time == "ms":
            time_value = int(delta_time)
            time_value = time_value/1000
        
        if unit_time == "us":
            time_value = int(delta_time)
            time_value = time_value/1000

        print("Data Point: " + data_point + " Time from last point: " + str(time_value) + "s")

    if user_input == "n":
        print("Shutting down.")
        exit()
