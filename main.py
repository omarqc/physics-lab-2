import time
import threading
import usb.core
import usb.util
import pyvisa
import keyboard
import numpy as np
from random import randint

from scipy.optimize import curve_fit
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

FIND_ALL = False
DEVICES = {}

def detach_kernel_driver(dev, name):
    try:
        if DEVICES[name].is_kernel_driver_active(0):
            DEVICES[name].detach_kernel_driver(0)
                
        print(f"Succesfully connected to '{name}'")

    except:
        print(f"Error in connecting to '{name}'")

# Attempt connection to MAGSYS HGM09s gaussmeters
for d_type in list(description.keys()):
    IDV = description[d_type]["idVendor"]
    IDP = description[d_type]["idProduct"]

    devices = usb.core.find(idVendor=IDV, idProduct=IDP, find_all=FIND_ALL)
    devices = tuple(devices)
    try: 
        # will give error if device variable is None (not found)
        device[0]
    except:
        print(f"Device {d_type} not found, exiting")
        exit()

    # this is for case of >1 gaussmeter
    i = 0
    for sub_device in devices:
        name = d_type + str(i)
        DEVICES[name] = sub_device
        detach_kernel_driver(DEVICES[name], description[d_type]['name']+str(i))

        i += 1

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


def get_magnetic_field(device):
    device.write(1, ':READ?')
    data = device.read(0x81, 100, 100)
    return time.time(), float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))


def get_temperature():
    return time.time(), randint(0,100)


def get_resistance(device):
    data = device.query(":MEASure:FRESistance?")
    print(data.decode('utf-8'))
    return time.time(), randint(0,100)


app = QtGui.QApplication([])

times1x, times1y, times1z, times2, times3 = [], [], [], [], []
B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


def reset_data():
    global times1x, times1y, times1z, times2, times3
    global B_x, B_y, B_z, resistance, temperature
    times1x, times1y, times1z, times2, times3 = [], [], [], [], []
    B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


window = pg.GraphicsWindow(title="Physics Lab 2 Data.")
window.setBackground((238,238,228))
window.showMaximized()


def make_plot(name, units, color):
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


def update(N=1, x:list=[], y:list=[], devs:list=[], func="", curve="", plot="", mag:list=[], ON=True):
    # Get 3 measurements from the 3 gaussmeters
    # timestamp, value = get_magnetic_field(device)

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
        # for case of magnetometer, plot time of middle reading y. (x, y, z)
        X = x[1][-MAX_VIEW:]
        curve.setData(x[1], mag)

    if PAUSE_FLAG: plot.setRange(xRange=[min(X), max(X)])
 
    QtGui.QApplication.processEvents() 


REF_TIME = time.time()

while True:
    if keyboard.is_pressed("space"):
        PAUSE_FLAG = not PAUSE_FLAG

    if keyboard.is_pressed("r"):
        # reset time and data arrays
        REF_TIME = time.time()
        reset_data()
    
    else:
        # make sure that the 3 gaussmeters have been connected.
        update(N=3, x=[times1x, times1y, times1z], y=[B_x, B_y, B_z], devs=[], func=get_magnetic_field, 
            curve=curve1, plot=magnetic_field_plot, mag=B_mag, ON=False)

        update(N=1, x=[times2], y=[resistance], devs=[], func=get_resistance, curve=curve2, plot=resistance_plot, ON=False)
        update(N=1, x=[times3], y=[temperature], devs=[], func=get_temperature, curve=curve3, plot=temperature_plot, ON=False)
