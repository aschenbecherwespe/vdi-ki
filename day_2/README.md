# Inference

## installing the raspi python library


installing build dependencies:

```bash
sudo pip install jinja2 pyyaml ply
sudo apt install -y libboost-dev libgnutls28-dev openssl libtiff5-dev qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5 meson
sudo pip install --upgrade meson
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
```

install the libcamera library:
```bash
cd
git clone --branch picamera2 https://github.com/raspberrypi/libcamera.git
cd libcamera
# next we configure the build of the camera library
meson build --buildtype=release -Dpipelines=raspberrypi -Dipas=raspberrypi -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=enabled -Ddocumentation=disabled -Dpycamera=enabled
# compile and install
ninja -C build
sudo ninja -C build install
```

i'm not actually sure what this one is for, it's like some sort of drm kernel driver i think. 
```bash
cd
git clone https://github.com/tomba/kmsxx.git
cd kmsxx
git submodule update --init
sudo apt install -y libfmt-dev libdrm-dev
meson build
ninja -C build
```
next install raspi's version of python v4l2 (video for linux library)

```bash
cd
git clone https://github.com/RaspberryPiFoundation/python-v4l2.git
```

and now finally, the actual python library for the camera
```bash
cd
sudo pip3 install pyopengl
sudo apt install -y python3-pyqt5
git clone https://github.com/raspberrypi/picamera2.git
```

put this line into the bottom of the file `/home/pi/.bashrc`, to include these new libraries in your python path:
```bash
export PYTHONPATH=/home/pi/picamera2:/home/pi/libcamera/build/src/py:/home/pi/kmsxx/build/py:/home/pi/python-v4l2
```

now reboot.

next, check out and run the `preview.py` example code to make sure that everthing has worked okay. It should show the preview window for 5 seconds.

NOTE: the installation instructions are derived from [this page](https://github.com/raspberrypi/picamera2), they're going to change in the future as the picamera2 python library matures. this is just a preview build, so there might be some stability issues, but hopefully not too many! 

capturing an image we can use in yolo:

the model is trained to take images of resolution `416x416`, so first we should crop the image: 
```python
def crop_square(im):
    width, height = im.size   # Get dimensions

    # lets take the shorter side of image and crop to that
    new_longest = min(width, height) 

    left = (width - new_longest)/2
    top = (height - new_longest)/2
    right = (width + new_longest)/2
    bottom = (height + new_longest)/2

    # Crop the center of the image
    im = im.crop((left, top, right, bottom))

    return im

# lets test it

image = picam2.switch_mode_and_capture_image(capture_config)
squared = crop_square(image)
squared.size # both dimensions should be the same
```
we also need to resize the image, this should be done with antialilasing (otherwise the image will look terrible)

```python
import PIL
maxsize = (416, 416)

squared.thumbnail(maxsize, PIL.Image.ANTIALIAS)
# note, this operation occurs inplace, so the larger image is gone
```

## pil to disk

```python
# save the image to storage (and convert it to RGB - removing the alpha channel)
image.convert('RGB').save('/home/pi/ScaledYOLOv4/input.jpg')
```


## Publishing Results

Lets push our results to some databases. We'll first use Minio to store historic data. Minio is an Amazon S3 compatible blob storage. It's like a database but for binary things that we can't really get any nice aggregatable data from.

We can run it easily using Docker, but first we'll need to install Docker on the raspi: 


```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

check our installation by running the `hello-world` container:
```bash
sudo docker run hello-world
```
you should get greeted by a message saying that docker seems to be working successfully. 

next we'll create a folder for Minio storage on our disk:

```bash
sudo mkdir -p /data/minio
```

Start the server with 
```bash
sudo docker run -d -p 9000:9000 -p 9001:9001 -v /data/minio:/data minio/minio server /data --console-address ":9001"
```
the arguments of this command mean: 
`-d` - run in the background (detatch)
`-p <external-port>:<internal-port>` - bind to a port (we bind two, since we want api (9000) and http (9001) access)
`-v /local/dir:/conatiner/dir` - bind a folder from the host machine to the conatiner
and the rest is minio specifc stuff. 

Check if minio is up and running by opening this link in your browser: [http://localhost:9001](ttp://localhost:9001)
The default username and password are both `minioadmin`.

In Minio we can create a bucket where we'll dump our data, call it `images`


now we can install minio client, and start writing data to our bucket, this is quite straightforard:

```bash
pip install minio
```

in python:
```python
import minio

client = minio.Minio('localhost:9000/', 'minioadmin', 'minioadmin', secure=False)

with open('P1.png', 'rb') as infile:
    data = infile.read()
    infile.seek(0)
    client.put_object('images', 'test.png', infile, len(data))
```

## Timeseries DB

next we'd like to add a timeseries database, so that we can view statistical data over time. this is nice for pushing results of a neural network, since we can very easily visualise and retrieve the results.
We'll use InfluxDB.

again, first we'll need to create a folder for our data on the pi:
```bash
sudo mkdir -p /data/influx
```

and then download and start influx:
```bash
sudo docker run -d \
-p 8086:8086 \
-v /data/influx:/var/lib/influxdb2 \
influxdb
```

We can check it's running by visiting [http://localhosLt:8086](http://localhost:8086) and here we'll need to configure our credentials. 
Create a user `pi` with password `raspberry`, organisation `vdi` and bucket `predictions`, then click next. On the influx home screen, click the "API Tokens" tab and copy "pi's Token" into a file for safe keeping. This will be needed to write data to the database.

next we'll install the influx client: 
```bash
pip install influxdb-client
```

and using it is easy:
```
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

bucket="predictions"
org="vdi"
token="Dm_E_p6wLWxO2st-pefO7YEqLusl938By2zhbM9YmRTx2omBtw2X7-CcbI6jh1LTQ_6e0YylPZZsP5Hz_X5Dfw=="
url="http://localhost:8086"

client = influxdb_client.InfluxDBClient( url=url, token=token, org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)

p = influxdb_client.Point("measurement").field('hello', "world").field('value', 3.14)

write_api.write(bucket=bucket, org=org, record=p)


```


## Upgrading YOLO

We need now to put the prediction part of YOLO into an infinite loop. 
Each cycle of the loop, we'd like to read the input image from the capture tool, pass it to the neural network, and publish the results to influxdb.
We also should publish the prediction and input images to minio. 
Each of these data points should share some reference, like a timestamp `int(time.tim())`, so for example call the images:
```
<timestamp>_input.jpg
<timestamp>_prediction.jpg
```
and include these parameters in the influx entry. 

To interpret the results of the network we can use:
```python
classid, _, x, y, w, h, conf = output[0]
```

...in the live prediction file.
