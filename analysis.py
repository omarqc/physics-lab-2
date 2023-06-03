from scipy.optimize import curve_fit
import pyqtgraph as pg
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

SHOW_77K_RESISTANCE = True

FILTER_MAGNET = False
PLOT_DISTANCE_RESISTANCE = False
FIT_EXP_CURVE = False

windows = []

colors = ["red", "green", "blue", "black", "orange", "violet", "turquoise", "lightgreen", "pink", "yellow","yellowgreen","gray","lightgray"]

folders = ["resistance", "magnetic_field"]
units = ["Ω", "T"]
labels=["Resistance", "Field_Mag"]


def resistance_fit(x, a, b):
    return a*np.exp(-b*x)
    

def fit_1_r2(x,a,b):
    return a/x**2 + b


def create_window():
    window = pg.GraphicsLayoutWidget(title=folder)
    window.setBackground((255,255,255))

    plot = window.addPlot(title="Resistance")

    if not PLOT_DISTANCE_RESISTANCE:
        x_l = "Time"
        x_u = "s"
    else:
        x_l = "Distance"
        x_u = "cm"

    plot.setLabel("left", folder, units=units[j])
    plot.setLabel("bottom", x_l, units=x_u)
    plot.getAxis("left").setTextPen("black")
    plot.getAxis("bottom").setTextPen("black")
    if LEGEND: plot.addLegend()
    return window, plot


j = 0
for folder in folders:
    data_files = os.popen(f"ls data/{folder}/{FILTER}*.csv").read().split("\n")[:-1]
    mins = []
    i = 0
    if not INDEPENDENT:
        window, plot = create_window()

    for filename in data_files:
        run = filename.replace(".csv", "").split("Run")[1]
        if INDEPENDENT:
            window, plot = create_window()
        print(filename)
        print(colors[i])
        print()
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

        x = np.array(x,dtype=np.float64)
        y = np.array(y,dtype=np.float64)
        
        if MOVING_AVERAGE:
            mv_av = []
            for k in range(len(y)):
                mv_av.append(np.average(y[k:k+MOVING_AVERAGE]))

            y = np.array(mv_av)
        
        if folder == "resistance":
            N_min_peak = np.where(y==min(y))[0][0]
            derivative = np.diff(y)/np.diff(x)
            der_77k = derivative[:N_min_peak]
            y_77k = y[:N_min_peak]
            start_peak = np.where(der_77k==max(der_77k))[0][0] - 5 # subtract a few data points to avoid start of peak
            if int(run) == 9:
                start_peak = 70
            resistance_77k = np.average(y[:start_peak])
            
            plot.plot(x[:-1], derivative)
            max_peak = np.where(y_77k==max(y_77k))[0][0]
            peak_duration = x[N_min_peak] - x[max_peak]
            plot.plot(x[max_peak:N_min_peak], [5e-3]*len(x[max_peak:N_min_peak]),pen=pg.mkPen(colors[i], width=3))

            print(f"Average 77K Resistance: {resistance_77k} Ω")
            print(f"Peak duration: {peak_duration} seconds")

        if folder == "magnetic_field":
            y = y/10**6 # microtesla to T

        if FIT_EXP_CURVE and not PLOT_DISTANCE_RESISTANCE:
            last = N_min_peak
            X = x[N_min_peak:]
            Y = y[N_min_peak:]

            popt, pcov = curve_fit(resistance_fit, X, Y, maxfev=10000)
            plot.plot(X, resistance_fit(X, *popt))

        label = f"{filename.split('/')[-1][:5]}: Run {run}, mag_distance={magnet_distance}"

        if FILTER_MAGNET:
            if not magnet_distance:
                continue
            

        if not FILTER_MAGNET or not PLOT_DISTANCE_RESISTANCE:
            plot.plot(x, y, pen=pg.mkPen(colors[i], width=2), name=label)

            if SHOW_77K_RESISTANCE:
                plot.plot(x[:start_peak], [resistance_77k]*start_peak,pen=pg.mkPen(colors[i], width=3))

        else:
            # Then create a plot of resistance at 77K vs distance to magnet
            scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen('w'), pxMode=True)
            scatter.setData([magnet_distance],[B[0]], pen=colors[i], brush=colors[i], name=label+",R_fit="+str(B[0]))
            plot.addItem(scatter)

        windows.append(window)
        i += 1
        window.show()
        input()

    j+=1


for i in range(len(windows)):
    windows[i].show()

input()