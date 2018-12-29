import sys
import time

import RPi.GPIO as GPIO

# Extractor Fan Pin
EXTRACTOR_FAN_PIN = 24

state = GPIO.LOW if sys.argv[1] == '0' else GPIO.HIGH

print state
print 'Turning fan ', 'ON' if state else 'OFF'

try:
    # setup gpio - temp/humidity sensor
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(EXTRACTOR_FAN_PIN, GPIO.OUT)

    time.sleep(1)
    GPIO.output(EXTRACTOR_FAN_PIN, state)
except Exception as err:
    print(err)