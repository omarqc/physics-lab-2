import time
import threading
import usb.core
import usb.util
import pyvisa
import serial
import keyboard
import numpy as np
from random import randint
from threading import Thread

# from scipy.optimize import curve_fit
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

# display only last N values
MAX_VIEW = 350
PAUSE_FLAG = True

description = {
    "gaussmeter": {
        "name": "MAGSYS HGM09s",
        "idVendor": 0x04d8,
        "idProduct": 0xfe78
    }
}

FIND_ALL = True # Must be true to identify and connect to > 1 gaussmeters

"""
DEVICES stores all the device variables, accessed by their nameID
Example: DEVICES["gaussmeter0"] or DEVICES["thermometer"]
"""
DEVICES = {}

ARDUINO_PORT = "/dev/ttyACM0"
T_R0 = 100
T_A = 3.9083e-3
T_B = -5.775e-7
T_C = -4.183e-12


times1x, times1y, times1z, times2, times3 = [], [], [], [], []
B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


def reset_data():
    global times1x, times1y, times1z, times2, times3
    global B_mag, B_x, B_y, B_z, resistance, temperature
    times1x, times1y, times1z, times2, times3 = [], [], [], [], []
    B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


def get_magnetic_field(device):
    device.write(1, ':READ?')
    data = device.read(0x81, 100, 100)
    return time.time(), float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))


def get_temperature(device):
    data = float(device.readline()[:-2].decode('utf-8'))
    if data < T_R0:
        data = np.roots([T_R0*T_C, -100*T_C*T_R0, T_R0*T_B, T_R0*T_A,T_R0-float(data)])[-1].real
    elif data >= T_R0:
        data = np.roots([T_R0*T_B, T_R0*T_A,T_R0-float(data)])[-1].real

    return time.time(), data


def get_resistance(device):
    data = device.query(":MEASure:FRESistance?")
    print(data.decode('utf-8'))
    return time.time(), randint(0,100)


def detach_kernel_driver(dev, name):
    """
    Attempts to disconnect kernel driver for proper functioning
    Parameters:
        dev: device variable
        name: name of device
    Returns:
        No return value
    """
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
                
        print(f"Succesfully connected to '{name}'")

    except Exception as e:
        print(f"Error in connecting to '{name}'")


"""
Attempt connection to MAGSYS HGM09s gaussmeters
"""
for d_type in list(description.keys()):
    IDV = description[d_type]["idVendor"]
    IDP = description[d_type]["idProduct"]

    devices = tuple(usb.core.find(idVendor=IDV, idProduct=IDP, find_all=FIND_ALL))
    print(devices)
    try: 
        # will give error if device variable is None (not found)
        devices[0]
    except:
        print(f"Device {d_type} not found, exiting")
        break

    # this is for case of >1 gaussmeter
    i = 0
    for sub_device in devices:
        name = d_type + str(i)
        DEVICES[name] = sub_device
        detach_kernel_driver(DEVICES[name], description[d_type]['name']+str(i))

        i += 1


def connect_keithley():
    # Attempt connection to Keithley 2000 Multimeter
    rm = pyvisa.ResourceManager('@py')
    print(rm.list_resources())
    try:
        keithley = rm.open_resource("ASRL/dev/ttyUSB0::INSTR", timeout=5000)
        keithley.baud_rate = 19200
        keithley.data_bits = 8
        keithley.parity = pyvisa.constants.Parity.none
        keithley.stop_bits = pyvisa.constants.StopBits.one

        print(f"Succesfully connected to Keithley 2000 Multimeter")
        
    except Exception as e:
        keithley=None
        print(e)
        print(f"Error in connecting to Keithley 2000 Multimeter")

    DEVICES["ohmmeter"] = keithley


def connect_arduino():
    arduino = serial.Serial(ARDUINO_PORT)
    DEVICES["thermometer"] = arduino
    print("Successfully connected to Arduino")


connect_arduino()

window = pg.GraphicsLayoutWidget(title="Physics Lab 2 Data.")
window.setBackground((238,238,228))
window.showMaximized()


def make_plot(name, units, color):
    """
    Parameters:
        name: name of plot
        units: units of plot
        color: color of plot/graph
    Returns:
        curve, plot: pyqtgraph variables necessary to create plots and graph data
    """
    plot = window.addPlot(title=name)
    curve = plot.plot(pen=color)
    plot.setLabel("left", name, units=units)
    plot.setLabel("bottom", "Time / s")
    plot.getAxis("left").setTextPen("black")
    plot.getAxis("bottom").setTextPen("black")

    return curve, plot


curve1, magnetic_field_plot = make_plot("Magnetic Field", "T", "green")
curve2, resistance_plot = make_plot("Resistance", "&Omega;", "brown")
curve3, temperature_plot = make_plot("Temperature", "K", "blue")


def update(N=1, x=[], y=[], func="", devs=[], curve="", plot="", mag=[], ON=True):
    """
    Arguments:
        N: number of devices per measurement type
        x: list of arrays to store time data. len(x) must be equal to N.
        y: list of arrays to store y data. len(y) must be equal to N.
        func: device-dependent function for requesting measurement
        devs: list of device variables to be passed to func as parameter
        curve: external pyqtgraph variable, used to set graph data
        plot: external pyqtgraph variable, used here to update graph x-range
        mag: optional, used to calculate magnitude of 3 magnetometers and store
            the magnitude in an external variable
        ON: simulate random data if ON is False
    Returns:
        No return value
    """

    values = []
    for i in range(N):
        if ON:
            t, v = func(devs[i])
        else:
            # if ON is False, simulate data with random values
            t, v = time.time(), randint(0, 100)

        # append x values to the lists given as parameters
        x[i].append(t - REF_TIME)
        # append y values to the lists given as parameters
        y[i].append(v)
        # append y values to another list for internal reference
        values.append(v)

    mag.append(np.linalg.norm(values))

    if N==1:
        X = x[0][-MAX_VIEW:]
        curve.setData(x[0], y[0])
    else:
        # for case of magnetometer, plot time of middle reading (y)
        X = x[1][-MAX_VIEW:]
        curve.setData(x[1], mag)

    if PAUSE_FLAG: plot.setRange(xRange=[min(X), max(X)])
 
    QtGui.QGuiApplication.processEvents() 


REF_TIME = time.time()

while True:
    if keyboard.is_pressed("space"):
        PAUSE_FLAG = not PAUSE_FLAG

    if keyboard.is_pressed("r"):
        # Reset ALL the data (x and y) arrays
        REF_TIME = time.time()
        reset_data()
    
    else:
        try:
            # graph update function for Gaussmeters
            update(N=3, x=[times1x, times1y, times1z], y=[B_x, B_y, B_z], devs=[DEVICES["gaussmeter0"], DEVICES["gaussmeter1"],
                DEVICES["gaussmeter2"]], func=get_magnetic_field, curve=curve1, plot=magnetic_field_plot, mag=B_mag, ON=False)

            # graph update function for Ohmmeter
            update(N=1, x=[times2], y=[resistance], devs=[DEVICES["ohmmeter"]], func=get_resistance, curve=curve2, plot=resistance_plot, ON=True)

            # # graph update function for Temperature Sensor
            update(N=1, x=[times3], y=[temperature], devs=[DEVICES["thermometer"]], func=get_temperature, curve=curve3, plot=temperature_plot, ON=True)

        except KeyboardInterrupt:
            break

print("\nLogging data to files (DO NOT CANCEL)...", end="")

# Save data to files
b_file = open("magnetic_field.txt", "a")
b_file.write("TimeX,TimeY,TimeZ,Bx,By,Bz")
for i in range(len(times1x)):
    b_file.write(f"\n{times1x[i]},{times1y[i]},{times1z[i]},{B_x[i]},{B_y[i]},{B_z[i]}")

# b_file.write("TimeX,Bx")
# for i in range(len(times1x)):
#     b_file.write(f"\n{times1x[i]},{B_x[i]}")

b_file.close()


r_file = open("resistance.txt", "a")
r_file.write("Time,Resistance")
for i in range(len(times2)):
    r_file.write(f"\n{times2[i]},{resistance[i]}")

r_file.close()


t_file = open("temperature.txt", "a")
t_file.write("Time,Resistance,Temperature")
for i in range(len(times3)):
    R = temperature[i]
    t_file.write(f"\n{times3[i]},{R},{np.roots([T_R0*T_C, -100*T_C*T_R0, T_R0*T_B, T_R0*T_A, T_R0 - R])[-1].real}")

t_file.close()

print(" DONE")
