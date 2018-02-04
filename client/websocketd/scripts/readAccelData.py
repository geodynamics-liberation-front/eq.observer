#!/usr/bin/env python
import json
import struct
import sys
import time

from MPU9255 import fileio
from MPU9255 import SCALE_2G

if __name__=='__main__':
    for l in fileio.readAccelData(dir_name=".."):
        l['x']=SCALE_2G*l['x']
        l['y']=SCALE_2G*l['y']
        l['z']=SCALE_2G*l['z']
        sys.stdout.write(json.dumps(l))
        sys.stdout.write('\n')
        sys.stdout.flush()
