
## Still To Do
* Cleanup bluez source in the /root directory
* Try to use bluex package created by checkinstall if available
* Set raspberry pi locale
* Set raspberry pi timezone
* Move MPU9255 functions to a class.  Accept the bus and address as a constructor parameter
* Add MPU9255 Documentation to the code
* Configure the pi-gen sumbmodule in git
* reorganize the top level directories:
 * move client -> device
 * move pi-image -> device/os
 * create server
* Add eq notification - monitor USGS feeds
 * Try to generate prose base on: economic impact, history of eqs, moment, etc.  Add some "educational" component to the notification
 * notify WPA
 * post to Reddit
* Add git to os image
* Use git to update scripts, like zsh does

## Too Done
* ~~add --experimental flag for /lib/systemd/system/bluetooth.service~~
* ~~ add sudo modprobe btusb to /etc/modules ~~
* ~~patch /usr/bin/btuart to use btattach rather than hci attact
  see https://github.com/Re4son/re4son-kernel-builder/issues/7~~
* ~~Already enabled.  enable the bluetooth service : sudo systemctl enable bluetooth (double check this, maybe not needed), links appears to be in /etv/systemd/system/bluetooth.target.wants~~
