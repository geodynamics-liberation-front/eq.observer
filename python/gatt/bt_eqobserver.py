#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

import dbus
import dbus.mainloop.glib

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

# from Adafruit_LED_Backpack import BicolorMatrix8x8

# from bluez_components import *
from bluez_components import Characteristic
from bluez_components import Service
from bluez_components import Application
from bluez_components import Advertisement
from bluez_components import get_service_manager
from bluez_components import get_ad_manager

mainloop = None

#def int_to_hex(int_value):
#    return {
#        0: '0',
#        1: '1',
#        2: '2',
#        3: '3',
#        4: '4',
#        5: '5',
#        6: '6',
#        7: '7',
#        8: '8',
#        9: '9',
#        10: 'a',
#        11: 'b',
#        12: 'c',
#        13: 'd',
#        14: 'e',
#        15: 'f'
#    }.get(int_value, '0')


class EqoCharacteristic(Characteristic):
    UUID = '12345678-1234-5678-1234-56789abc0000'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.UUID,
            ['read', 'write'],
            service)
        self.value = list(bytes("test\u00f8","utf-8"))

    def ReadValue(self, options):
        print('RowCharacteristic Read: Row: ' + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        print('RowCharacteristic Write: Row: ' + repr(value))
        self.value = value[:2]


class ScanCharacteristic(Characteristic):
    UUID = '12345678-1234-5678-1234-56789abc0001'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.UUID,
            ['read', 'write'],
            service)
        self.essids = ["orangefood", "one", "s\u00f8ren", "two", "superman"]
        self.ndx = 0;

    def ReadValue(self, options):
        print('Scan Read {}'.format(self.ndx))
        if self.ndx >= len(self.essids):
            value = []
            self.ndx = 0
        else:
            value = list(bytes(self.essids[self.ndx],"utf-8"))
            self.ndx += 1
        print(repr(value))
        return value

    def WriteValue(self, value, options):
        print('RowCharacteristic Write: Row: ' + repr(value))
        self.ndx = 0


class EqoService(Service):
    UUID = '12345678-1234-5678-1234-56789abc0010'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, EqoService.UUID, True)
        self.add_characteristic(ScanCharacteristic(bus, 0, self))
        self.add_characteristic(EqoCharacteristic(bus, 1, self))


class EqoApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(EqoService(bus, 0))


class EqoAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        print("Advertising service uuid : %s" % EqoService.UUID)
        self.add_service_uuid(EqoService.UUID)
        self.include_tx_power = True
        self.add_local_name('EqObserver')


def register_ad_cb():
    """
    Callback if registering advertisement was successful
    """
    print('Advertisement registered')


def register_ad_error_cb(error):
    """
    Callback if registering advertisement failed
    """
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()


def register_app_cb():
    """
    Callback if registering GATT application was successful
    """
    print('GATT application registered')


def register_app_error_cb(error):
    """
    Callback if registering GATT application failed.
    """
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    # Get ServiceManager and AdvertisingManager
    service_manager = get_service_manager(bus)
    ad_manager = get_ad_manager(bus)

    # Create gatt services
    app = EqoApplication(bus)

    # Create advertisement
    test_advertisement = EqoAdvertisement(bus, 0)

    mainloop = GObject.MainLoop()

    # Register gatt services
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)

    # Register advertisement
    ad_manager.RegisterAdvertisement(test_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    mainloop.run()


if __name__ == '__main__':
    main()
