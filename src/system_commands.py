import os
import sys


def measure_temp():
    return float(os.popen("/opt/vc/bin/vcgencmd measure_temp").read()[5:8])


def restart(args):
    os.system("clear")
    os.execv(sys.executable, [sys.executable.split("/")[-1]] + args)
