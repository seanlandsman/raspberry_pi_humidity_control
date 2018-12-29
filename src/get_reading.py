import time

import Adafruit_DHT
import RPi.GPIO as GPIO
import numpy as np

# Dew Point Calc Constants
A = 17.27
B = 237.7
DEW_POINT_RANGE = 0.25

# Temp/Humidity Pin
DHT_PIN = 4

# Max number of times to attempt read the temp from the sensor
MAX_DHT_READ_ATTEMPTS = 5


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


def calculateDewPointTemperature(humidity_pct, temp):
    return (B * (np.log(humidity_pct) + (A * temp) / (B + temp))) / (A - np.log(humidity_pct) - (A * temp) / (B + temp))


################################################################################
# Program starts now
try:
    # setup gpio - temp/humidity sensor
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    ################################################################################
    # temperature read & logging

    # Attempt to get sensor reading.
    humidity, temp = readSensorReading(MAX_DHT_READ_ATTEMPTS)
    if humidity is not None:

        # convert humidity to a percentage
        humidityPct = float(humidity) / 100

        # calculate the dew point
        Tdp = calculateDewPointTemperature(humidityPct, temp)

        message = 'Temperature: {0:0.1f} C'.format(temp)
        message += ', Humidity:    {0:0.1f} %'.format(humidity)
        message += ', Dew Point:   {0:0.1f} C'.format(Tdp)
        print(message)
    else:
        print("No result")
except Exception as err:
    print(err)
finally:
    GPIO.cleanup()
