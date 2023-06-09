from scipy.optimize import curve_fit
from PyQt5 import QtGui, QtCore
from scipy.datasets import electrocardiogram
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import os
import math
import random
import ruptures as rpt
import pyqtgraph as pg
import numpy as np
import pandas as pd

EARTH_FIELD = 27.99519322989239E-6
AV_VOLTAGE = 1.0134575854761009e-08

INDEPENDENT = False
LEGEND = True
MOVING_AVERAGE = 0
FILTERS = ["31_05", "05_06", "30_05"]
# FILTERS = ["05_06_tin","30_05_Tin"]
FILTERS = ["31_05"]

JOIN_FILTERS = False

FILTER_BY_RUN = [False, False, False]
EXCLUDE_RUN_FILTER = [False, False, False]
# RUN_FILTER = [[4,8,9,3,10,11,12]]
# RUN_FILTER = [[1,2,8], []]
RUN_FILTER = [[],[],[]]

# EXCLUDE_RUNS = [[1,2,3,11,12]] #30_05

# EXCLUDE_RUNS = [[],[1],[1,2,3,4,5,6,7,8,9,20], []] #05_06
EXCLUDE_RUNS = [[]]

SHOW_MOVE_TIME = False
SHOW_RAW_DATA = True
SHOW_DERIVATIVE = False

PLOT_CURRENT_TIME = False

SHOW_77K_RESISTANCE = True
SHOW_PEAK_DURATION = False

FILTER_MAGNET = False

PLOT_DISTANCE_RESISTANCE = False
PLOT_FIELD_RESISTANCE = False

PLOT_DISTANCE_HIGH_PEAK = False
PLOT_DISTANCE_LOW_PEAK = False

PLOT_DISTANCE_PEAK_LENGTH = False
PLOT_FIELD_PEAK_LENGTH = False

PLOT_FIELD_DISTANCE = False

FIT_EXP_CURVE = False

windows = []

colors = [[255,181,98],
[96,58,173],
[74,216,92],
[200,104,241],
[84,126,0],
[226,60,185],
[0,173,114],
[253,47,148],
[0,176,160],
[239,15,98],
[8,96,54],
[192,0,138],
[177,210,113],
[125,47,148],
[235,125,0],
[125,150,255],
[168,21,0],
[198,138,255],
[124,115,0],
[80,69,161],
[255,115,73],
[1,94,140],
[154,65,0],
[199,180,255],
[175,0,44],
[86,80,129],
[255,154,124],
[171,120,161],
[141,52,71],
[255,137,175]]

colors=[[230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [245, 130, 48], [145, 30, 180], [70, 240, 240], [240, 50, 230], [210, 245, 60], [250, 190, 212], [0, 128, 128], [220, 190, 255], [170, 110, 40], [255, 250, 200], [128, 0, 0], [170, 255, 195], [128, 128, 0], [255, 215, 180], [0, 0, 128], [128, 128, 128], [255, 255, 255]]
random.shuffle(colors)

folders = ["magnetic_field", "resistance"]
units = ["T", "Ω"]
labels=["Field_Mag", "Resistance"]

def resistance_fit(x, a, b):
    return a*np.exp(-b*x)
    

def linear_fit(x,a,b):
    return a*x + b


def quadratic_fit(x,a):
    return a/x**2


def cut_data(X, Y, a=0, b=0):
    A = np.where(np.round(X) == a)[0][-1]
    B = np.where(np.round(X) == round(X[-1]-b))[0][0]
    return X[A:B], Y[A:B]


def create_window(name, y_u="", d=False):
    window = pg.GraphicsLayoutWidget()
    window.setWindowTitle(name)
    window.setBackground((255,255,255))
    x = ""
    if d: x = " derivative"
    # plot = window.addPlot(title=f"<h1 style='color:black;'>{FILTER} {name.capitalize()}{x} data</h1>")
    plot = window.addPlot()

    if not PLOT_DISTANCE_RESISTANCE and not PLOT_DISTANCE_PEAK_LENGTH and not PLOT_DISTANCE_HIGH_PEAK and not PLOT_DISTANCE_LOW_PEAK:
        x_l = "Time"
        x_u = "s"
    else:
        x_l = "Magnet Distance"
        x_u = "cm"
    
    if SHOW_DERIVATIVE:
        name = "Derivative of R with respect to time"
        y_u = "Ω / s"

    if PLOT_FIELD_RESISTANCE:
        x_l = "Magnetic Field"
        x_u = "T"
        name = "Superconductor Resistance (T=77K)"
        y_u = "Ω"

    if PLOT_CURRENT_TIME:
        name = "Current"
        y_u = "A"
    
    if PLOT_DISTANCE_LOW_PEAK:
        name = "Resistance of Low Peak"
        y_u = "Ω"

    if PLOT_DISTANCE_HIGH_PEAK:
        name = "Resistance of High Peak"
        y_u = "Ω"

    if PLOT_DISTANCE_PEAK_LENGTH:
        name = "Resistance Peak Duration"
        y_u = "s"

    if PLOT_FIELD_PEAK_LENGTH:
        name = "Resistance Peak Duration"
        y_u = "s"
        x_l = "Magnetic Field"
        x_u = "T"

    if PLOT_FIELD_DISTANCE:
        name = "Magnetic Field"
        y_u = "T"
        x_l = "Magnet-Superconductor Distance"
        x_u = "cm"

    labelStyle = {'color': '#FFF', 'font-size': '30pt'}
    plot.setLabel("left", name, units=y_u, **labelStyle)
    plot.setLabel("bottom", x_l, units=x_u, **labelStyle)

    plot.getAxis("left").setTextPen("black")
    plot.getAxis("bottom").setTextPen("black")

    font=QtGui.QFont()
    font.setPixelSize(35)
    plot.getAxis("left").setTickFont(font)
    plot.getAxis("bottom").setTickFont(font)
    if LEGEND: plot.addLegend(labelTextSize='20pt', labelTextColor='black', pen=pg.mkPen(width=3))
    return window, plot


symbols = ["s", "t1", "x"]
k = 0
if JOIN_FILTERS and not INDEPENDENT:
    window, plot = create_window("Tin Resistance", y_u="Ω", d=SHOW_DERIVATIVE)
    # window, plot = create_window("time", y_u="s", d=SHOW_DERIVATIVE)


X = []
Y = []
for file_filter in FILTERS:
    j = 0
    R_77ks = []
    B_77ks = []
    B_77ks_E = []
    B_peaks = []
    for folder in folders:
        print(f"------{folder}-----------")
        name = folder.replace("_", " ")
        data_files = os.popen(f"ls data/{folder}/{file_filter}*").read().split("\n")[:-1]
        mins = []
        i = 0
        if not INDEPENDENT and not JOIN_FILTERS:
            window, plot = create_window(name, y_u=units[j], d=SHOW_DERIVATIVE)

        for filename in data_files:
            def PEN(w, col="",style=None):
                print(k)
                return pg.mkPen(tuple(col) if col else colors[i] , width=w,style=style)

            run = filename.replace(".csv", "").split("Run")[1]

            if int(run) in EXCLUDE_RUNS[k]: continue
            if FILTER_BY_RUN[k]:
                if int(run) not in RUN_FILTER[k]: continue
            else:
                if EXCLUDE_RUN_FILTER[k]:
                    if int(run) in RUN_FILTER[k]: continue

            if INDEPENDENT:
                window, plot = create_window(name, y_u=units[j], d=SHOW_DERIVATIVE)
            print(filename)

            f = open(f"{filename}", "r")
            
            x = []
            y = []

            c = 0
            magnet_distance = 0
            for row in f.readlines():
                if "=" not in row:
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
                
                if "MAGNET" in row:
                    magnet_distance = int(row.split("=")[-1])
                    if file_filter=="31_05":
                        magnet_distance-=2
                        
                    print(f"mag_dist={magnet_distance}cm")
                
                if "DELAY" in row:
                    dly = int(row.split("=")[-1])
                    print(dly)

            if magnet_distance: extra = f", mag_distance={magnet_distance} cm"
            else: extra = ""
            label = f"{filename.split('/')[-1][:5]}: Run {run}{extra}"
            x = np.array(x)
            y = np.array(y)

            if folder == "magnetic_field":
                y = y/10**6 # microtesla to T
                x, y = cut_data(x, y, a=10, b=10)
                x = x[::100]
                y = y[::100]
                algo = rpt.Pelt(model="rbf").fit(y)
                result = algo.predict(pen=10)
                move_time = result[0]+10
                field_77k = np.average(y[:move_time])
                if file_filter == "30_05":
                    if int(run) == 9:
                        move_time = 96
                    elif int(run) == 6:
                        move_time = 58
                    elif int(run) == 12:
                        move_time = 77
                    elif int(run) == 10:
                        move_time = 95
                    elif int(run) == 5:
                        move_time += 1

                B_77ks.append(field_77k)
                B_peaks.append(move_time)
                B_77ks_E.append(np.std(y[:move_time])/np.sqrt(len(y[:move_time])))
            
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
                
                if file_filter == "31_05":
                    if int(run) == 9:
                        start_peak = 70
                    elif int(run) == 1:
                        start_peak = 80
                    elif int(run) == 10:
                        start_peak = 135

                elif file_filter == "30_05":
                    if int(run) == 9:
                        start_peak = 120
                    elif int(run) == 11:
                        start_peak = 115

                elif file_filter == "05_06_resistance":
                    if int(run) == 17:
                        start_peak = 75
                    if int(run) == 10:
                        start_peak = 70

                resistance_77k = np.average(y[:start_peak])
                N = len(y[:start_peak])
                R77k_STD = np.std(y[:start_peak])
                R77k_E = R77k_STD/np.sqrt(N)
                
                N_max_peak = np.where(y_77k==max(y_77k))[0][0]
                peak_duration = x[N_min_peak] - x[N_max_peak]

                min_peak = y[N_min_peak]
                max_peak = y[N_max_peak]

                print(f"Average 77K Resistance: {resistance_77k} Ω")
                print(f"77k Resistance Standard Deviation: {R77k_STD} Ω")
                print(f"77k Resistance Standard Error: {R77k_E} Ω")
                print(f"Data points in 77k Resistance: {N}")
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
                
            if SHOW_RAW_DATA:
                for _ in x: X.append(_)
                for _ in y: Y.append(_)
                # if PLOT_CURRENT_TIME and folder=="resistance":
                #     y = AV_VOLTAGE/y

                plot.plot(x, y, pen=PEN(3), name=label)

                if folder == "resistance":
                    if SHOW_77K_RESISTANCE:
                        plot.plot(x[:start_peak], [resistance_77k]*start_peak,pen=PEN(5))

                    if SHOW_PEAK_DURATION:
                        plot.plot(x[N_max_peak:N_min_peak], [5e-3]*len(x[N_max_peak:N_min_peak]),pen=PEN(3))

                if SHOW_MOVE_TIME:
                    # dly = 3
                    x_ = B_peaks[i]+dly if folder == "resistance" else B_peaks[i]
                    v_bar1 = pg.PlotDataItem([x_-1, x_-1], [min(y), max(y)], pen=PEN(3))
                    v_bar2 = pg.PlotDataItem([x_+1, x_+1], [min(y), max(y)], pen=PEN(3))
                    # plot.addItem(v_bar1)
                    fill = pg.FillBetweenItem(curve1=v_bar1, curve2=v_bar2)
                    fill.setBrush(pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],100))
                    plot.addItem(fill)

            else:
                if folder == "resistance":
                    if not i: label = file_filter
                    else: label = None
                    if PLOT_DISTANCE_RESISTANCE:
                        # Then create a plot of resistance at 77K vs distance to magnet
                        x_ = np.array([magnet_distance])
                        y_ = np.array([resistance_77k])
                        e_ = np.array([R77k_E])
                        errorbar = pg.ErrorBarItem(x=x_,y=y_, pen=PEN(2), brush=colors[i], beam=0.5,
                            bottom=e_, top=e_)
                        plot.addItem(errorbar)
                        plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                        symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                            name=label)

                    if PLOT_DISTANCE_PEAK_LENGTH:
                        X.append(magnet_distance)
                        Y.append(peak_duration)
                        x_ = np.array([magnet_distance])
                        y_ = np.array([peak_duration])
                        e_ = np.array([0.8])
                        errorbar = pg.ErrorBarItem(x=x_,y=y_, pen=PEN(2), brush=colors[i], beam=0.5,
                            bottom=e_, top=e_)
                        plot.addItem(errorbar)
                        plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                        symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                            name=label)

                    if PLOT_FIELD_PEAK_LENGTH:
                        X.append(B_77ks[i])
                        Y.append(peak_duration)
                        x_ = np.array([B_77ks[i]])
                        y_ = np.array([peak_duration])
                        e_ = np.array([0.8])
                        errorbar = pg.ErrorBarItem(x=x_,y=y_, pen=PEN(2), brush=colors[i], beam=1e-5,
                            bottom=e_, top=e_)
                        plot.addItem(errorbar)
                        plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                        symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                            name=label)

                    if PLOT_DISTANCE_HIGH_PEAK:
                        x_ = np.array([magnet_distance])
                        y_ = np.array([max_peak])
                        plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                        symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                            name=label)

                    if PLOT_DISTANCE_LOW_PEAK:
                        x_ = np.array([magnet_distance])
                        y_ = np.array([min_peak])
                        plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                        symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                            name=label)

                if PLOT_FIELD_RESISTANCE:
                    if folder == "magnetic_field": continue
                    X.append(B_77ks[i])
                    Y.append(resistance_77k)
                    x_ = np.array([B_77ks[i]])
                    y_ = np.array([resistance_77k])

                    e1_ = np.array([B_77ks_E[i]])
                    e2_ = np.array([R77k_E])

                    errorbar = pg.ErrorBarItem(x=x_,y=y_, pen=PEN(2), brush=colors[i], beam=0.5e-5,
                            bottom=e2_, top=e2_, left=e1_, right=e1_)
                    plot.addItem(errorbar)


                    plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                    symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                        name=label)
                
                if PLOT_FIELD_DISTANCE:
                    if folder == "magnetic_field": continue
                    X.append(magnet_distance)
                    Y.append(B_77ks[i])
                    x_ = np.array([magnet_distance])
                    y_ = np.array([B_77ks[i]-EARTH_FIELD])

                    e1_ = np.array([0.1])
                    e2_ = np.array([B_77ks_E[i]])

                    errorbar = pg.ErrorBarItem(x=x_,y=y_, pen=PEN(2), brush=colors[i], beam=0.5e-5,
                            bottom=e2_, top=e2_, left=e1_, right=e1_)
                    plot.addItem(errorbar)


                    plot.plot(x_, y_, symbol=symbols[k], symbolPen=PEN(2), 
                    symbolBrush=pg.mkBrush(colors[i][0],colors[i][1],colors[i][2],255),
                        name=label)

            windows.append(window)
            window.show()

            i += 1
            print()
            print()

        j+=1
        print()
        # break
        
    k += 1

input()