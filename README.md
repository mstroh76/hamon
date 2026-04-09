# hamon - Home Assistent Monitor

![Monitor](hamon.jpg)

## Install

```bash
sudo apt install python3-qtpy fonts-dseg
```

Add hamon to autostart file
``vi ~/.config/lxsession/LXDE/autostart``

```bash
@python3 /home/pi/hamon.py
```


Disable Screen Blanking with Raspberry Pi Software Configuration Tool (raspi-config)
```
2 Display Options
  D2 Screen Blanking
    Would you like to enable screen blanking? No
```
