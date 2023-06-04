from scipy.optimize import curve_fit
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pandas as pd
from scipy.datasets import electrocardiogram
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
import os
import math

INDEPENDENT = True
LEGEND = True
MOVING_AVERAGE = 0
FILTER = "31_05"

FILTER_BY_RUN = False
EXCLUDE_RUN_FILTER = False
RUN_FILTER = [3,10,11,12]

EXCLUDE_RUNS = []

SHOW_RAW_DATA = False
SHOW_DERIVATIVE = True

SHOW_77K_RESISTANCE = False
SHOW_PEAK_DURATION = False

FILTER_MAGNET = False
PLOT_DISTANCE_RESISTANCE = False
FIT_EXP_CURVE = False


B_PEAKS_31 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

windows = []

colors = ["red", "green", "blue", "black", "orange", "violet", "turquoise", "lightgreen", "pink", "yellow","yellowgreen","gray","lightgray"]

# folders = ["resistance", "magnetic_field"]
# units = ["Ω", "T"]
# labels=["Resistance", "Field_Mag"]

folders = ["magnetic_field"]
units = ["T"]
labels=["Field_Mag"]

def resistance_fit(x, a, b):
    return a*np.exp(-b*x)
    

def fit_1_r2(x,a,b):
    return a/x**2 + b


def cut_data(X, Y, a=0, b=0):
    A = np.where(np.round(X) == a)[0][-1]
    B = np.where(np.round(X) == round(X[-1]-b))[0][0]
    return X[A:B], Y[A:B]


def create_window(name, d=False):
    window = pg.GraphicsLayoutWidget()
    window.setWindowTitle(name)
    window.setBackground((255,255,255))
    x = ""
    if d: x = " derivative"
    # plot = window.addPlot(title=f"<h1 style='color:black;'>{FILTER} {name.capitalize()}{x} data</h1>")
    plot = window.addPlot()

    if not PLOT_DISTANCE_RESISTANCE:
        x_l = "Time"
        x_u = "s"
    else:
        x_l = "Distance"
        x_u = "cm"

    labelStyle = {'color': '#FFF', 'font-size': '20pt'}
    plot.setLabel("left", name, units=units[j], **labelStyle)
    plot.setLabel("bottom", x_l, units=x_u, **labelStyle)

    plot.getAxis("left").setTextPen("black")
    plot.getAxis("bottom").setTextPen("black")

    font=QtGui.QFont()
    font.setPixelSize(26)
    plot.getAxis("left").setTickFont(font)
    plot.getAxis("bottom").setTickFont(font)
    if LEGEND: plot.addLegend(labelTextSize='20pt', labelTextColor='black', pen=pg.mkPen(width=3))
    return window, plot


j = 0
for folder in folders:
    name = folder.replace("_", " ")
    data_files = os.popen(f"ls data/{folder}/{FILTER}*.csv").read().split("\n")[:-1]
    mins = []
    i = 0
    if not INDEPENDENT:
        window, plot = create_window(name, d=SHOW_DERIVATIVE)

    for filename in data_files:
        def PEN(w):
            return pg.mkPen(colors[i], width=w)

        run = filename.replace(".csv", "").split("Run")[1]
        if int(run) in EXCLUDE_RUNS: continue
        if FILTER_BY_RUN:
            if int(run) not in RUN_FILTER: continue
        else:
            if EXCLUDE_RUN_FILTER:
                if int(run) in RUN_FILTER: continue

        if INDEPENDENT:
            window, plot = create_window(name, d=SHOW_DERIVATIVE)
        print(filename)
        print(colors[i])

        f = open(f"{filename}", "r")
        
        x = []
        y = []

        c = 0
        magnet_distance = False
        for row in f.readlines():
            if "MAGNET" not in row:
                try:
                    r = row.replace("\n", "").split(",")
                    if not c:
                        y_label = r[-1]
                        if y_label == "Resistance":
                            y_units = "Ω"
                        elif y_label == "Temperature":
                            y_units = "C"

                        c = 1

                    else:
                        x.append(float(r[0]))
                        if float(r[-1]) > 10000:
                            r[-1] = 0
                        y.append(float(r[-1]))
                except Exception as e:
                    print(e)
            
            else:
                magnet_distance = row.split("=")[-1]

        if magnet_distance: extra = f", mag_distance={magnet_distance} cm"
        else: extra = ""
        label = f"{filename.split('/')[-1][:5]}: Run {run}{extra}"
        x = np.array(x,dtype=np.float64)
        y = np.array(y,dtype=np.float64)

        if folder == "magnetic_field":
            y = y/10**6 # microtesla to T
            x, y = cut_data(x, y, a=10, b=10)
            x = x[::200]
            y = y[::200]
        
        if MOVING_AVERAGE:
            if folder == "magnetic_field":
                MOVING_AVERAGE = 200
            mv_av = []
            for k in range(len(y)):
                mv_av.append(np.average(y[k:k+MOVING_AVERAGE]))

            y = np.array(mv_av)
        
        derivative = np.diff(y)/np.diff(x)
        if SHOW_DERIVATIVE: plot.plot(x[:-1], derivative, pen=PEN(3), name=label)

        if folder == "resistance":
            N_min_peak = np.where(y==min(y))[0][0]
            der_77k = derivative[:N_min_peak]
            y_77k = y[:N_min_peak]
            start_peak = np.where(der_77k==max(der_77k))[0][0] - 5 # subtract a few data points to avoid start of peak
            
            if FILTER == "31_05":
                if int(run) == 9:
                    start_peak = 70
                elif int(run) == 1:
                    start_peak = 80
                elif int(run) == 10:
                    start_peak = 135

            elif FILTER == "30_05":
                if int(run) == 9:
                    start_peak = 120
                elif int(run) == 11:
                    start_peak = 115

            resistance_77k = np.average(y[:start_peak])
            
            max_peak = np.where(y_77k==max(y_77k))[0][0]
            peak_duration = x[N_min_peak] - x[max_peak]

            print(f"Average 77K Resistance: {resistance_77k} Ω")
            print(f"77k Resistance Standard Deviation: {np.std(y[:start_peak])} Ω")
            print(f"Peak duration: {peak_duration} seconds")

        if FIT_EXP_CURVE and not PLOT_DISTANCE_RESISTANCE:
            last = N_min_peak
            X = x[N_min_peak:]
            Y = y[N_min_peak:]

            popt, pcov = curve_fit(resistance_fit, X, Y, maxfev=10000)
            plot.plot(X, resistance_fit(X, *popt))

        if FILTER_MAGNET:
            if not magnet_distance:
                continue
            
        if not FILTER_MAGNET or not PLOT_DISTANCE_RESISTANCE:
            if SHOW_RAW_DATA:
                plot.plot(x, y, pen=PEN(4), name=label)

                if folder == "resistance":
                    if SHOW_77K_RESISTANCE:
                        plot.plot(x[:start_peak], [resistance_77k]*start_peak,pen=PEN(5))

                    if SHOW_PEAK_DURATION:
                        plot.plot(x[max_peak:N_min_peak], [5e-3]*len(x[max_peak:N_min_peak]),pen=PEN(3))

        else:
            # Then create a plot of resistance at 77K vs distance to magnet
            scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen('w'), pxMode=True)
            scatter.setData([magnet_distance],[B[0]], pen=colors[i], brush=colors[i], name=label+",R_fit="+str(B[0]))
            plot.addItem(scatter)

        windows.append(window)
        window.show()
        i += 1
        print()

    j+=1
    break


for i in range(len(windows)):
    windows[i].show()

input()