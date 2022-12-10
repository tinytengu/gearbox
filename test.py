import pymem
import time

pm = pymem.Pymem("speed2.exe")
while True:
    print(pm.read_int(0x03C080B4))
    time.sleep(0.5)
