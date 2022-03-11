#!/usr/bin/python3

# Normally the QtGlPreview implementation is recommended as it benefits
# from GPU hardware acceleration.

from qt_gl_preview import *
from picamera2 import *
import time

picam2 = Picamera2()
preview = QtGlPreview(picam2)

preview_config = picam2.preview_configuration()
picam2.configure(preview_config)

capture_config = picam2.still_configuration()


picam2.start()

# load image

while True:
    input("press return to trigger")
    image = picam2.switch_mode_and_capture_image(capture_config)
    #do something with the image




