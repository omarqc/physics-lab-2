import time
import threading
import usb.core
import usb.util
import keyboard
import numpy as np
from random import randint

from scipy.optimize import curve_fit
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

# display only last N values
MAX_VIEW = 350

description = {
    "gaussmeter": {
        "name": "MAGSYS HGM09s",
        "idVendor": 0x04d8,
        "idProduct": 0xfe78
    },
    "ohmmeter": {
        "name": "Keithley 2000 Multimeter",
        "idVendor": 0x0403,
        "idProduct": 0x6001
    }
}

DEVICES = {}

for d_type in list(description.keys()):
    IDV = description[d_type]["idVendor"]
    IDP = description[d_type]["idProduct"]

    devices = tuple(usb.core.find(idVendor={IDV}, idProduct={IDP}, find_all=True))
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
        try:
            if DEVICES[name].is_kernel_driver_active(0):
                DEVICES[name].detach_kernel_driver(0)
            
            print(f"Succesfully connected to '{NAMES[i]}' ({i})")

        except:
            print(f"Error in connecting to '{NAMES[i]}'")
            exit()

        i += 1


def get_magnetic_field(device):
    device.write(1, ':READ?')
    data = device.read(0x81, 100, 100)
    return time.time(), float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))


def get_temperature():
    return time.time(), randint(0,100)


def get_resistance(device):
    device.write(2, ':MEASure:FRESistance?<LF>')
    data = device.read(0x81, 100, 100)
    print(data)
    return time.time(), randint(0,100)


app = QtGui.QApplication([])

times1, times1y, times1z, times2, times3 = [], [], [], [], []
B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


def reset_data():
    global times1x, times1y, times1z, times2, times3
    global B_x, B_y, B_z, resistance, temperature
    times1, times1y, times1z, times2, times3 = [], [], [], [], []
    B_mag, B_x, B_y, B_z, resistance, temperature = [], [], [], [], [], []


window = pg.GraphicsWindow(title="Physics Lab 2 Data.")
window.setBackground((238,238,228))
window.showMaximized()

magnetic_field_plot = window.addPlot(title="Magnetic Field", color="red")
resistance_plot = window.addPlot(title="Resistance")
temperature_plot = window.addPlot(title="Temperature")

curve1 = magnetic_field_plot.plot(pen="green")
magnetic_field_plot.setLabel("left", "Magnetic Field", units="T")
magnetic_field_plot.setLabel("bottom", "Time / s")
magnetic_field_plot.getAxis("left").setTextPen("black")
magnetic_field_plot.getAxis("bottom").setTextPen("black")


curve2 = resistance_plot.plot(pen="brown")
resistance_plot.setLabel("left", "Resistance", units="&Omega;")
resistance_plot.setLabel("bottom", "Time / s")
resistance_plot.getAxis("left").setTextPen("black")
resistance_plot.getAxis("bottom").setTextPen("black")

curve3 = temperature_plot.plot(pen="blue")
temperature_plot.setLabel("left", "Temperature", units="K")
temperature_plot.setLabel("bottom", "Time / s")
temperature_plot.getAxis("left").setTextPen("black")
temperature_plot.getAxis("bottom").setTextPen("black")

PAUSE_FLAG = True


def update1():
    t1x, Bx = get_magnetic_field(DEVICES["gaussmeter0"])
    t1y, By = get_magnetic_field(DEVICES["gaussmeter1"])
    t1z, Bz = get_magnetic_field(DEVICES["gaussmeter2"])
    t1x -= REF_TIME
    t1y -= REF_TIME
    t1z -= REF_TIME

    times1x.append(t1x)
    times1y.append(t1y)
    times1z.append(t1z)
    B_x.append(Bx)
    B_y.append(By)
    B_z.append(Bz)
    B_mag.append((Bx**2 + By**2 + Bz**2)**0.5)

    curve1.setData(times1y, B_mag)

    X = times1y[-MAX_VIEW:]
    if PAUSE_FLAG: magnetic_field_plot.setRange(xRange=[min(X), max(X)])
 
    QtGui.QApplication.processEvents() 


def update2():
    t2, R = get_resistance(DEVICES["ohmmeter0"])
    t2 -= REF_TIME

    times2.append(t2)
    resistance.append(R)

    curve2.setData(times2, resistance)

    X = times2[-MAX_VIEW:]
    if PAUSE_FLAG: resistance_plot.setRange(xRange=[min(X), max(X)])

    QtGui.QApplication.processEvents()


def update3():
    t3, T = get_temperature()
    t3 -= REF_TIME

    times3.append(t3)
    temperature.append(T)

    curve3.setData(times3, temperature)

    X = times3[-MAX_VIEW:]
    if PAUSE_FLAG: temperature_plot.setRange(xRange=[min(X), max(X)])

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
        update1()
        update2()

        # still have to add code for thermometer (actually just reading resistance -> temperature)
        update3()

pg.QtGui.QApplication.exec_()

# Save data to files
b_file = open("magnetic_field.txt", "a")
b_file.write("TimeX,TimeY,TimeZ,Bx,By,Bz")
for i in range(len(times1x)):
    b_file.write(f"{times1x[i]},{times1y[i]},{times1z[i]},{B_x[i]},{B_y[i]},{B_z[i]}")

b_file.close()