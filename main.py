import usb.core
import usb.util
import numpy as np

dev = usb.core.find(idVendor=0x04d8, idProduct=0xfe78)
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

def magnetic_field(device):
    device.write(1, ':READ?<LF>')
    data = device.read(0x81, 100, 100)
    return float(bytearray(list(data)).replace(b'\x00', b'').decode('utf-8'))

for i in range(1000):
    print(magnetic_field(dev))

