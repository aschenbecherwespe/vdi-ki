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

---

## Software/Driver Setup 

Unfortunately, the RasPi software is currently in the middle of migrating to a new camera driver. This means that the Python library support is not as good as you would expect. 

Usually almost everything is very easy with RasPis since they're so popular, but this is surprisingly difficult. 

Maybe it's not worth it. Ha!

## Python Library

This takes a few minutes to install:
https://github.com/raspberrypi/picamera2

This is the required build command for libcamera
```bash
meson build --buildtype=release -Dpipelines=raspberrypi -Dipas=raspberrypi -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=enabled -Ddocumentation=disabled -Dpycamera=enabled
```

Good examples of how to get basic programs working.
We can try to build something that lets us preview the image we're about to take, and then take an image by pressing the spacebar. It should increment the name of the image, and print to the screen so we know how many we've captured so far. It would also be nice to be able to specify a folder to save the images into, and required resolution.


---

## Recording Data

Use your program to record as many images as you can before you get bored. When we've got a nice variety of images, with varying angles and light conditions, we can start to label the data.


```python
import time
import threading

from qt_gl_preview import *
from picamera2 import *
from null_preview import *

picam2 = Picamera2()
config = picam2.still_configuration()
picam2.configure(config)
preview = QtGlPreview(picam2)

preview_config = picam2.preview_configuration()
picam2.configure(preview_config)

#preview = NullPreview(picam2)

picam2.start()
time.sleep(1)

metadata = picam2.capture_metadata()
controls = {c : metadata[c] for c in ["ExposureTime", "AnalogueGain", "ColourGains"]}
print(controls)

picam2.set_controls(controls)

count = 0

while True:
    #key = input("push space to capture")
    #if key == ' ':
    name = f"{int(time.time() * 1000)}.jpg"
    count += 1
    print(f'capturing with name: {name}, count: {count}')
    picam2.capture_file(name)


#threading.Thread(target = control_thread).start()
```

---

## Labelling Data

We'll use the [MakeSense.AI](https://makesense.ai) tool to label our images. Open it in the Chromium web browser on your Pi, click "get started" and select `object detection` 
 - object detection allows selection of areas of interest on an image
 - image recognition allows assigning labels to each image

This tool allows us to export our annotations in a format that YOLO will understand, we just need to add the generated text files in the same folder with our images, after extracting them from the zip file.

We can create a label `connector` by clicking the `+` button, and then all the images should be labelled. This should be as pixel-accurate as possible, good training data makes for good networks.

When we've labelled all data, we can download the data in YOLO format as a zip. This zip contains a `txt` file for each image that was labelled. 

Their contents should look something like this: 
```
0 0.441748 0.512928 0.531823 0.649270
```
the first value is the class ID, the second and third values are the X and Y coordinates (as a fraction of the image) of the centre of the rectangle, of size the last two numbers (also as a fraction of the image, width and height).


---

## Training

To train we first need to organise our training data. We need to split the data into three (train, test and validate) groups. 

Monitor performance with
```bash
htop
```

---

## Scaled YOLOv4
Scaled YOLOv4 is a pytorch based implementation of the YOLO 
```
git clone https://github.com/aschenbecherwespe/ScaledYOLOv4
```

Download the pretrained [weights](https://drive.google.com/file/d/1aXZZE999sHMP1gev60XhNChtHPRMH3Fz/view?usp=sharing) and save them into a `weights` folder in the yolo folder.


Modify our settings `yaml`
In the `ScaledYOLOv4/data` directory, copy the `coco.yaml` file and rename it to `vdi.yaml`
In this file we'll need to point our training infrastructure to the three folders we made earlier: 
```
/home/pi/data/train/
/home/pi/data/val/
/home/pi/data/test/
```

We also need up update the class `names`, remove the existing ones and replace with our new, single class, and update the number of classes variable: `nc`.


Install the needed python packages - save this into a file, `requirements.txt`

```requirements.txt
git+https://github.com/aschenbecherwespe/mish-cuda-dummy
numpy==1.21.2
opencv-python==4.5.5.62
wheel==0.37.1
scikit_image==0.19.1
tensorboard==2.8.0
tqdm==4.63.0
matplotlib==3.5.1
torch==1.10.2
torchvision==0.11.3
torchaudio==0.10.2
```

and install via pip:
```bash
pip install -U -r requirements.txt
```

We might need to manually upgrade numpy, also:
```bash
pip install --upgrade numpy
```

We use the `train.py` script to do our training. Descriptions for available options can be found with: 

```bash
python3 train.py --help
```

To start training:

```bash
python3 train.py --data ./data/coco.yaml --weights weights/yolov4-p5.pt  --device 'cpu' --epochs 1 #--batch 1
```



--- 

## Basic Inference

Let's use `ipython` to walk step by step through the process of taking an image and running the AI on it, using our pretrained model.

```
pip install -U ipython
ipython
```

We've created a helper module in `helper.py` to modify the network before we load it. This is due to being trained on a GPU, the network uses some functions that aren't available on CPU, but we can replace them before using the model:


```python
import torch
from mish_cuda import MishCuda
from utils.general import non_max_suppression, output_to_target
from helper import replace_mish_layers, revert_sync_batchnorm
import cv2

# load and setup model
model = torch.load('home/pi/ScaledYOLOv4/final_model.pt', map_location=torch.device('cpu'))
replace_mish_layers(model['model'], MishCuda, torch.nn.Mish())
model = reverse_sync_batchnorm(model['model'])
model = model.float().fuse().eval()

# load image
img_path = '/home/pi/test.jpg'
img = cv2.imread(img_path)
transposed = img[:, :, ::-1].transpose(2, 0, 1)


# reformat image
contiguous = np.ascontiguousarray(transposed)
torch_img = torch.from_numpy(contiguous).to('cpu')
torch_float = torch_img.float()
torch_normalized = torch_float / 255.0
unsqueezed = torch_float.unsqueeze(0)

# get a prediction
start = time.perf_counter()
pred = model(unsqueezed)[0]
end = time.perf_counter()
print('prediction took %f seconds.', end - start)
non_maxed = non_max_suppression(pred)
output = output_to_target(non_maxed)

print(output)
```

