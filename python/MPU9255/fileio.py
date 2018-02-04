import os
import struct
import sys
import time

from . import SCALE_2G

# I/O Structures
STRUCT_OUT = struct.Struct(">QBBBBBB")
STRUCT_IN = struct.Struct(">Qhhh")

def writeAccelData(bus):
    write_file=True
    configAccel(ACCEL_FS_SEL_2G)
    start = time.time()
    file_time = int(start/600)*600
    f=open('%d.bin'%file_time,'ab')
    while write_file:
        f.write(
            STRUCT_OUT.pack(
                int(1000*time.time()),
                bus.read_byte_data(ADDR,reg.ACCEL_XOUT_H),
                bus.read_byte_data(ADDR,reg.ACCEL_XOUT_L),
                bus.read_byte_data(ADDR,reg.ACCEL_YOUT_H),
                bus.read_byte_data(ADDR,reg.ACCEL_YOUT_L),
                bus.read_byte_data(ADDR,reg.ACCEL_ZOUT_H),
                bus.read_byte_data(ADDR,reg.ACCEL_ZOUT_L)
            )
        )
        if time.time()-file_time>600:
            f.close();
            file_time = int(time.time()/600)*600
            f=open('%d.bin'%file_time,'ab')
            
    end = time.time()
    f.close()
    print("Wrote 1000 records in %f seconds"%(end-start))

def readAccelData(file_name = None, dir_name="."):
    if file_name == None:
        file_time = int(time.time()/600)*600
        file_name = os.path.join(dir_name,'%d.bin'%file_time)

    f=open(file_name,'rb+')
    while True:
        record = f.read(STRUCT_IN.size)
        while len(record)<STRUCT_IN.size:
            rec = f.read(STRUCT_IN.size-len(record))
            if len(rec)>0:
                record = record + rec
            if len(record)==0 and int(time.time()/600)*600 > file_time:
                f.close()
                file_time = int(time.time()/600)*600
                file_name = os.path.join(dir_name,'%d.bin'%file_time)
                f=None
                while f==None:
                    try:
                        f=open(file_name,'rb+')
                    except IOError:
                        time.sleep(0.1)
                        pass

        t,x,y,z = STRUCT_IN.unpack(record)
        yield {'t':t,'x':x,'y':y,'z':z}
