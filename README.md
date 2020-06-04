# Joycontrol Bridge

Use your PC controller to control your Nintendo Switch via bluetooth. This is essentially a fork of [joycontrol](https://github.com/mart1nro/joycontrol/). I simply added an interface that accepts controller inputs and forwards them to the Switch.

Do not expect this to be low latency. Analog controls theoretically work but induce a lot of delay. Because of this I commented out all the relevant code.

Latency is fine for casual Mario Kart 8 (imho) but way too high for Super Smash Bros.

Tested on Manjaro.

## Installation
- Install the dbus-python and libhidapi-hidraw0 packages

Manjaro:
```bash
sudo pacman -S python-dbus hidapi
```

Debian/Ubuntu:
```bash
sudo apt install python3-dbus libhidapi-hidraw0
```

- Clone the repository and install the joycontrol package to get missing dependencies (Note: Controller script needs super user rights, so python packages must be installed as root). In the joycontrol folder run:
```bash
git clone https://github.com/z80z80z80/joycontrol-bridge.git
cd joycontrol
sudo pip install .
```

## Using the Bridge
- Run the script

Manjaro:
```bash
sudo python bridge.py PRO_CONTROLLER
```

Debian/Ubuntu:
```bash
sudo python3 bridge.py PRO_CONTROLLER
```

This will create a PRO_CONTROLLER instance waiting for the Switch to connect.

- Open the "Change Grip/Order" menu of the Switch

The Switch only pairs with new controllers in the "Change Grip/Order" menu.

Note: If you already connected an emulated controller once, you can use the reconnect option of the script (-r "\<Switch Bluetooth MAC address>").
This does not require the "Change Grip/Order" menu to be opened. You can find out a paired MAC address using the "bluetoothctl" system command.
Alternatively, when connecting via "Change Grip/Order" menu, you'll see something like:
```bash
[19:55:58] joycontrol.server create_hid_server::100 INFO - Accepted connection at psm 19 from ('XX:XX:XX:XX:XX:XX', 19)
```
XX:XX:XX:XX:XX:XX is the bluetooth MAC address of your Switch. 

- After connecting, the preconfigured controller layout is translated to pro controller commands that are then sent to the Switch.

## TODO
- basic GUI to easily configure different controllers
- saving & loading of controller configurations and the Switch MAC address

## Resources
[joycontrol](https://github.com/mart1nro/joycontrol/)

[Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)

[console_pairing_session](https://github.com/timmeh87/switchnotes/blob/master/console_pairing_session)
