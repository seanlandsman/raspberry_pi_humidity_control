import time
import datetime

import numpy as np

import Adafruit_DHT
import RPi.GPIO as GPIO

# Dew Point Calc Constants
A = 17.27
B = 237.7
DEW_POINT_RANGE = 0.25

# Temp/Humidity Pin
DHT_PIN = 4

# Max number of times to attempt read the temp from the sensor
MAX_DHT_READ_ATTEMPTS=5

# Extractor Fan Pin
EXTRACTOR_FAN_PIN = 24

# Log file location
LOG_FILE = '/home/pi/humidity/logs/humidity.log'

# Max time the can be kept on before we shut it down (to cooldown etc)
MAX_ON_TIME = 15 * 60

# Loop check interval
LOOP_INTERVAL = 5 * 60

# create (or append to) log file
log = open(LOG_FILE, 'a')

fanOnTime = 0
fanOn = False


def getDateTime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def logOutput(output):
    # noinspection PyShadowingNames
    message = getDateTime() + " - " + output
    print message
    log.write(message + "\n")


# noinspection PyShadowingNames
def readSensorReading(max_attempts):
    humidity = None
    temp = None
    attempt = 0
    while attempt < max_attempts:
        humidity, temp = Adafruit_DHT.read(Adafruit_DHT.AM2302, DHT_PIN)
        # Skip to the next reading if a valid measurement couldn't be taken.
        # This might happen if the CPU is under a lot of load and the sensor
        # can't be reliably read (timing is critical to read the sensor).
        if humidity is None or temp is None:
            time.sleep(2)
            attempt = attempt + 1
        else:
            break
    return humidity, temp


################################################################################
# Program starts now

logOutput("Starting now")

# setup gpio - temp/humidity sensor
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(EXTRACTOR_FAN_PIN, GPIO.OUT)
GPIO.output(EXTRACTOR_FAN_PIN, GPIO.LOW)

logOutput("GPIO Setup Complete")


while True:
    ################################################################################
    # temperature read & logging

    # Attempt to get sensor reading.
    humidity, temp = readSensorReading(MAX_DHT_READ_ATTEMPTS)

    # convert humidity to a percentage
    humidityPct = float(humidity) / 100

    # calculate the dew point
    Tdp = (B * (np.log(humidityPct) + (A * temp) / (B + temp))) / (A - np.log(humidityPct) - (A * temp) / (B + temp))

    message = 'Temperature: {0:0.1f} C'.format(temp)
    message += ', Humidity:    {0:0.1f} %'.format(humidity)
    message += ', Dew Point:   {0:0.1f} C'.format(Tdp)
    logOutput(message)

    ################################################################################
    # fan operation

    if fanOn:
        fanOnTime += LOOP_INTERVAL
        if fanOnTime >= MAX_ON_TIME:
            GPIO.output(EXTRACTOR_FAN_PIN, GPIO.LOW)
            fanOn = False
            fanOnTime = 0
    else:
        if Tdp < temp + DEW_POINT_RANGE:
            GPIO.output(EXTRACTOR_FAN_PIN, GPIO.HIGH)
            fanOn = True

    # sleep until the next temp & fan check
    time.sleep(LOOP_INTERVAL)
