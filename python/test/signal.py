#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import signal
import time


def main():
    f = open("out.csv", "w")
    last_time = time.time()

    def t(signum=None, stack=None):
        nonlocal last_time
        now = time.time()
        print("%0.2f" % (now - last_time))
        f.write("%f\n" % now)
        last_time = now

    signal.signal(signal.SIGALRM, t)
    signal.setitimer(signal.ITIMER_REAL, 0.02, 1.0 / 50)
    time.sleep(10)


if __name__ == "__main__":
    main()
