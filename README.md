# A.I. on an RPi
_by Ciaran Moyne (PANDA GmbH), for VDI_

10.03.22

---

Today we'll cover:
- Hardware assembly
- OS installation
- Software/driver setup
- Capturing images for training
- Labelling training data
- Starting training the network
- Getting a prediction from a pretrained model

---

## Getting started

### Raspberry Pi Hardware Setup

The `Raspberry Pi` is a single board computer that was first released 10 years ago. It's a very low powered device, with a very small form factor, yet it runs a full Linux operating system with standard PC input/output devices (`USB`, `Ethernet`, `Display` and `audio` ports). The Pi 4B, which we're using, is the latest generation. It is the first version which has a choice of different amounts of onboard RAM. 
These are the 8GB variants. Typically they cost about 80€, but with the chip shortage, their price is (hopefully temporarily) currently much higher. 

![raspi crazy prices](https://i.imgur.com/HlmhVM4.jpg "who needs nft?")

The RasPi uses ARM processors, as opposed to Intel or AMD, which means that software for "desktop" processors sometimes won't work on them, but with Open Source software it can usually be recompiled to run on ARM. The ARM architecture is what allows the devices to be so cheap and low-power, it is generally much more efficient than desktop class CPUs. 

Raspberry Pi also host non-typical IO connectors, such as the GPIO pins, which allow interfacing with novel hardware (usually called Pi HATs). These allow very easy interfacing and prototyping with electronics. For example it is trivial to add a temperature sensor, button, led, etc. It also contains ribbon connectors which allow us to connect cameras and displays. We'll use the CSI connector to connect a camera today. 

The board also contains on-board WLAN and Bluetooth, in case you'd like to use it in a place where cables are inconvenient. It's even possible to run the device off a battery pack.

To squeeze the most performance out of the Pi, we'll add some heatsinks and a fan. 

You should assemble the device by sticking on the heatsinks, connecting the camera via the ribbon cable, and the fan. The fan should connect to a 5V and a ground connection on the GPIO. Then the case can be screwed together.

![pinout](https://i0.wp.com/www.notenoughtech.com/wp-content/uploads/2016/04/Raspberry-Pi-GPIO-Layout-Model-B-Plus-rotated-2700x900.png?fit=640%2C213)

--- 

### RasPi HQ Camera

- 12.3 megapixel sensor
- 7.9mm diagonal sensor size
- C/CS mount lenses
- Connects with CSI
- Can do pretty cool stuff, high framerate, RAW, etc.
- No global shutter
- External Hardware Sync supported! Strobe flash also.
- About 50€ without a lens
- We have a telephoto and wide lens. 

---

### Raspberry OS

We'll be using the latest version of Raspberry Pi OS, which is now running in 64bit mode. 

It's easier to get machine learning libraries for ARM64, like PyTorch.

Raspberry Pi computers use a MicroSD card as their primary storage device. We can load the operating system onto the card easily with the Raspberry Pi Imager software.

It can be downloaded [here.](https://www.raspberrypi.com/software/)

Insert the SD card into a card reader, and into the computer you want to _flash_ the card from. Open the Raspberry Pi software. 

**Choose an OS:** - today, we will use:

```
Raspberry Pi OS (64-bit) (Bullseye)
```

`Full` includes software we don't need, and is larger and slower to download, and `Lite` is for applications where no display is attached to the device.

**Choose Storage:** this option should show you the SD card in your computer. Select it. Be careful not to choose the wrong drive, you will loose any data on it. 
We can also configure some options here, it's probably a good idea to change your hostname, otherwise they will all be `raspberry`. The rest can be configured on first boot.

The application will now download the latest version, write it to the SD card, and verify the integrity of the operation. 

When complete, the card can be inserted into the RasPi, and power can be applied. 
Connect the HDMI to the port closest to the USB-C power port, and your keyboard, mouse and ethernet cable.

---

### First Boot

- Wait a while, takes some time to install, then reboots
- Select Keyboard and language
- Skip password select
- Select WIFI
- Start updates

---

### Hello Camera

First we'd like to make sure that all our devices are working okay, we can do that by viewing the output of the camera. 
Open a terminal by clicking the terminal icon in the top panel of the desktop. In the terminal enter:

```bash
libcamera-hello -t 0  # “-t 0” for no timeout - run indefinitely
```
Nice! A second window should have opened and should be showing a live video feed from the camera! It's probably blurry though. We'll need to focus the camera to get the resulting image good and sharp. 

We can also use this command line tool to record images and video in various formats. We're not interested in video today, but I think this is a good way of getting familiar with the `gain` and `exposure` parameters of the camera. The `libcamera-still` command will help:

```bash
#  list the options
libcamera-still —-help 
#  to take a picture and save it 
libcamera-still --output <filename.jpg>
#  for manual exposure control
libcamera-still —-shutter <us> —-gain <db> --output <filename.jpg>
```

### Python Library

Unfortunately, the RasPi software is currently in the middle of migrating to a new camera driver. This means that the Python library support is not as good as you would expect. 

Usually almost everything is very easy with RasPis since they're so popular, but this is surprisingly difficult. 

Maybe it's not worth it. Ha!