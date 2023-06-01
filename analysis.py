from scipy.optimize import curve_fit
import pyqtgraph as pg
import numpy as np
import os
import math

INDEPENDENT = False
LEGEND = True
MOVING_AVERAGE = 10
FILTER = ""

SHOW_77K_RESISTANCE = False

FILTER_MAGNET = False
PLOT_DISTANCE_RESISTANCE = True

windows = []

colors = ["red", "green", "blue", "black", "orange", "violet", "turquoise", "lightgreen", "pink", "yellow","yellowgreen","gray","lightgray"]
folders = ["resistance"]
units = ["Ω"]

N = 1000000
A = np.linspace(-10000, 10000, N)
B = np.linspace(-2000, 2000, N)

def resistance_fit(x, a, b):
    return a*np.log(x) + b


def straight_fit(x, b):
    return np.array([b]*len(x))


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
    data_files = os.popen(f"ls data/{folder}/{FILTER}*.txt").read().split("\n")[:-1]
    mins = []
    i = 0
    if not INDEPENDENT:
        window, plot = create_window()

    for filename in data_files:
        run = filename.replace(".txt", "").split("Run")[1]
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
            if "_" not in row:
                r = row.split(",")
                if not c:
                    y_label = r[1].replace("\n", "")
                    if y_label == "Resistance":
                        y_units = "Ω"
                    elif y_label == "Temperature":
                        y_units = "C"

                    c = 1

                else:
                    x.append(float(r[0]))
                    if float(r[1]) > 10000:
                        r[1] = 0
                    y.append(float(r[1]))
            
            else:
                magnet_distance = row.split("=")[1]

        x = np.array(x,dtype=np.float64)
        y = np.array(y,dtype=np.float64)

        # N = np.where(y==min(y))[0][0]
        # X2 = x[N:]
        # Y2 = y[N:]

        # X = x[385:]'
        # Y = y[385:]

        # popt, pcov = curve_fit(resistance_fit, X, Y)
        # plot.plot(X, resistance_fit(X, *popt))        

        # popt, pcov = curve_fit(resistance_fit, X, Y)
        label = f"{filename.split('/')[-1][:5]}: Run {run}, mag_distance={magnet_distance}"

        if FILTER_MAGNET:
            if not magnet_distance:
                continue
            
        B, _ = curve_fit(straight_fit, x[:70], y[:70])
        if not FILTER_MAGNET or not PLOT_DISTANCE_RESISTANCE:
            if MOVING_AVERAGE:
                mv_av = []
                for k in range(len(y)):
                    mv_av.append(np.average(y[k:k+MOVING_AVERAGE]))

                plot.plot(x, mv_av, pen=pg.mkPen(colors[i], width=2), name=label)
                if SHOW_77K_RESISTANCE:
                    plot.plot(x[:70], straight_fit(x[:70], B[0]),pen=pg.mkPen(colors[i], width=3))

            else:
                plot.plot(x, y, pen=pg.mkPen(colors[i], width=2), name=label)

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