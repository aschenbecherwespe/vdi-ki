# Inference

Running ipython interpreter:

```bash 
python -m IPython
```

installing the camera drivers:
installing buidl dependencies:

```bash
sudo pip install jinja2 pyyaml ply
sudo apt install -y libboost-dev libgnutls28-dev openssl libtiff5-dev qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5 meson
sudo pip install --upgrade meson
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
```

install the libcamera library:
```bash
cd
git clone git://linuxtv.org/libcamera.git
cd libcamera
meson build --buildtype=release -Dpipelines=raspberrypi -Dipas=raspberrypi -Dv4l2=true -Dgstreamer=enabled -Dtest= -Dlc-compliance=disabled -Dcam=disabled -Dqcam=enabled -Ddocumentation=disabled -Dpycamera=enabled
ninja -C build
sudo ninja -C build install
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
-v /data/influx:/var/lib/influxdb2
```

We can check it's running by visiting [http://localhosLt:8086](http://localhost:8086) and here we'll need to configure our credentials. 
Create a user `pi` with password `raspberry`, organisation `vdi` and bucket `predictions`, then click next. On the influx home screen, click the "API Tokens" tab and copy "pi's Token" into a file for safe keeping. This will be needed to write data to the database.

next we'll install the influx client: 
```bash
pip install influxdb-client
```



automatically collect image based on timer? 
run prediction
stream results via fast api
push data into influx
push data into minio
show preview
preview in browser? 
