import time
import threading
import usb.core
import usb.util
import numpy as np
import matplotlib.gridspec as gridspec
from random import randint
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

# sample rate (ms)
SAMPLE_RATE = 10
REF_TIME = time.time()

# display only last N values
MAX_VIEW = 200

# dev = usb.core.find(idVendor=0x04d8, idProduct=0xfe78)
# if dev.is_kernel_driver_active(0):
#     dev.detach_kernel_driver(0)


def get_magnetic_field():
    # device.write(1, ':READ?<LF>')
    # data = device.read(0x81, 100, 100)
    return time.time(), randint(0, 100)
    return time.time(), float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))


def get_temperature():
    return time.time(), randint(0, 100)


def get_resistance():
    return time.time(), randint(0, 100)


times1, times2, times3 = [], [], []
magnetic_field, resistance, temperature = [], [], []

gs = gridspec.GridSpec(2, 2)
fig = plt.figure()
fig.suptitle(f"Settings | Sample Rate: {1000/SAMPLE_RATE} / s | Display last {MAX_VIEW} values")

manager = plt.get_current_fig_manager()
manager.full_screen_toggle()

ax1 = fig.add_subplot(gs[0,:])
line1, = ax1.plot(times1, magnetic_field, "-",color="green")

ax2 = fig.add_subplot(gs[1,0])
line2, = ax2.plot(times2, resistance, "-",color="brown")

ax3 = fig.add_subplot(gs[1,1])
line3, = ax3.plot(times3, temperature, "-",color="blue")

ax1.set_title("Magnetic Field")
ax1.set_xlabel("Time / s")
ax1.set_ylabel("B / T")

ax2.set_title("Resistance")
ax2.set_xlabel("Time / s")
ax2.set_ylabel(r"R / $\Omega$")

ax3.set_title("Temperature")
ax3.set_xlabel("Time / s")
ax3.set_ylabel("T / K")

_times1, _times2, _times3 = [], [], []
_B, _R, _T = [], [], []


def update1(frame):
    global times1, magnetic_field
    t1, B = get_magnetic_field()
    t1 -= REF_TIME

    times1.append(t1)
    magnetic_field.append(B)

    _times1.append(t1)
    _B.append(B)
   
    times1 =  times1[-MAX_VIEW:]
    magnetic_field = magnetic_field[-MAX_VIEW:]

    line1.set_data(times1, magnetic_field)
 
    ax1.relim()
    ax1.autoscale_view()

    return line1,

def update2(frame):
    global times2, resistance
    t2, R = get_resistance()
    t2 -= REF_TIME

    times2.append(t2)
    resistance.append(R)

    _times2.append(t2)
    _R.append(R)

    times2 = times2[-MAX_VIEW:]
    resistance = resistance[-MAX_VIEW:]

    line2.set_data(times2, resistance)

    ax2.relim()
    ax2.autoscale_view()

    return line2,


def update3(frame):
    global times3, temperature
    t3, T = get_temperature()
    t3 -= REF_TIME

    times3.append(t3)
    temperature.append(T)

    _times3.append(t3)
    _T.append(T)

    times3 = times3[-MAX_VIEW:]
    temperature = temperature[-MAX_VIEW:]

    line3.set_data(times3, temperature)

    ax3.relim()
    ax3.autoscale_view()

    return line3,


anim = FuncAnimation(fig, update1, interval=SAMPLE_RATE)
anim2 = FuncAnimation(fig, update2, interval=SAMPLE_RATE)
anim3 = FuncAnimation(fig, update3, interval=SAMPLE_RATE)

plt.show()

# b_file = open("magnetic_field.txt", "a")

# for i in range(len(_times1)):
#     b_file.write(f"{_times1[i]},{_B[i]},{_R[i], _T[i]}")
