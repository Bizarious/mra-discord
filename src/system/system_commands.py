import os
import sys
import time


def measure_temp():
    return float(os.popen("/opt/vc/bin/vcgencmd measure_temp").read()[5:8])


def restart(args):
    time.sleep(3)
    os.system("clear")
    os.execv(sys.executable, [sys.executable.split("/")[-1]] + args)
