import pyqtgraph as pg
import numpy as np
import os

data_files = os.popen("ls data/").read().split("\n")[1:-1]

windows = []

for filename in data_files:
    f = open(f"data/{filename}", "r")
    window = pg.GraphicsLayoutWidget(title=filename)
    window.setBackground((238,238,228))

    plot = window.addPlot(title=filename)
    
    x = []
    y = []

    c = 0
    for row in f.readlines():
        r = row.split(",")
        if not c:
            y_label = r[1].replace("\n", "")

            if y_label == "Resistance":
                y_units = "Ω"
            elif y_label == "Temperature":
                y_units = "K"

            c = 1

        else:
            x.append(float(r[0]))
            if float(r[1]) > 10:
                r[1] = 0
            y.append(float(r[1]))

    x = np.array(x)
    y = np.array(y)

    plot.setLabel("left", y_label, units=y_units)
    plot.setLabel("bottom", "Time / s")
    plot.getAxis("left").setTextPen("black")
    plot.getAxis("bottom").setTextPen("black")
    plot.plot(x, y, pen="blue")
    windows.append(window)


for i in range(len(windows)):
    windows[i].show()
    input("# Press enter to show next window > ")
