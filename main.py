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
MAX_VIEW = 500

dev = usb.core.find(idVendor=0x04d8, idProduct=0xfe78)
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)


def get_magnetic_field(device):
    device.write(1, ':READ?<LF>')
    data = device.read(0x81, 100, 100)
    return time.time(), float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))


def get_temperature():
    return time.time(), randint(0,100)


def get_resistance():
    return time.time(), randint(0,100)


app = QtGui.QApplication([])

times1, times2, times3 = [], [], []
magnetic_field, resistance, temperature = [], [], []


def reset():
    global times1, times2, times3
    global magnetic_field, resistance, temperature
    times1, times2, times3 = [], [], []
    magnetic_field, resistance, temperature = [], [], []


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

FLAG = True


def update1():
    t1, B = get_magnetic_field(dev)
    t1 -= REF_TIME

    times1.append(t1)
    magnetic_field.append(B)

    curve1.setData(times1, magnetic_field)

    X = times1[-MAX_VIEW:]
    if FLAG: magnetic_field_plot.setRange(xRange=[min(X), max(X)])
 
    QtGui.QApplication.processEvents() 


def update2():
    t2, R = get_resistance()
    t2 -= REF_TIME

    times2.append(t2)
    resistance.append(R)

    curve2.setData(times2, resistance)

    X = times2[-MAX_VIEW:]
    if FLAG: resistance_plot.setRange(xRange=[min(X), max(X)])

    QtGui.QApplication.processEvents()


def update3():
    t3, T = get_temperature()
    t3 -= REF_TIME

    times3.append(t3)
    temperature.append(T)

    curve3.setData(times3, temperature)

    X = times3[-MAX_VIEW:]
    if FLAG: temperature_plot.setRange(xRange=[min(X), max(X)])

    QtGui.QApplication.processEvents()


REF_TIME = time.time()

while True:
    if keyboard.is_pressed("space"):
        FLAG = not FLAG

    if keyboard.is_pressed("r"):
        REF_TIME = time.time()
        reset()
    
    else:
        update1()
        update2()
        update3()

pg.QtGui.QApplication.exec_()

# b_file = open("magnetic_field.txt", "a")

# for i in range(len(_times1)):
#     b_file.write(f"{_times1[i]},{_B[i]},{_R[i], _T[i]}")
