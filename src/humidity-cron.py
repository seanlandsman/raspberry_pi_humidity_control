import json
import sys
import time
import datetime

import numpy as np

#import Adafruit_DHT
#import RPi.GPIO as GPIO

import gspread
from oauth2client.client import SignedJwtAssertionCredentials

# GDOCS_OAUTH_JSON       = '/Users/seanlandsman/IdeaProjects/humidity/src/landsmansfamily-33b13df5dd2c.json'

from oauth2client.service_account import ServiceAccountCredentials
import gspread

#GDOCS_OAUTH_JSON       = '/home/pi/humidity/landsmansfamily-33b13df5dd2c.json'

# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 'Humidity Logs'

# Dew Point Calc Constants
A = 17.27
B = 237.7
DEW_POINT_RANGE = 0.25

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']


credentials = ServiceAccountCredentials.from_json_keyfile_name('landsmansfamily-33b13df5dd2c.json', scope)
credentials = ServiceAccountCredentials.from_json_keyfile_name('landsmansfamily-aaf1623b12c8.json', scope)
gc = gspread.authorize(credentials)


# Log file location
LOG_FILE = '/home/pi/humidity/logs/humidity.log'

# Temp/Humidity Pin
DHT_PIN = 4

# Extractor Fan Pin
EXTRACTOR_FAN_PIN = 24

# Max time the can be kept on before we shut it down (to cooldown etc)
MAX_ON_TIME = 30 * 60

log = open(LOG_FILE, 'a')

def getDateTime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def logOutput(output):
    message = getDateTime() + " - " + output
    print message
    log.write(message + "\n")

logOutput("Starting now")

# setup gpio - temp/humidity sensor
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(EXTRACTOR_FAN_PIN, GPIO.OUT)
GPIO.output(EXTRACTOR_FAN_PIN,  GPIO.LOW)

logOutput("GPIO Setup Complete")

def login_open_sheet(oauth_key_file, spreadsheet):
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
        json_key = json.load(open(oauth_key_file))
        credentials = SignedJwtAssertionCredentials(json_key['client_email'],
                                                    json_key['private_key'],
                                                    ['https://spreadsheets.google.com/feeds'])
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print 'Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!'
        print 'Google sheet login failed with error:', ex
        sys.exit(1)

def readSensorReading(attempts):
    humidity = None
    temp = None
    attempt = 0
    while attempt < attempts:
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

def logReading(temp, humidity, Tdp, fanOn, attempts):
    logged = False
    attempt = 0
    while (attempt < attempts) and (logged == False):
        # Append the data in the spreadsheet, including a timestamp
        try:
            worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
            worksheet.append_row((getDateTime(), temp, humidity, Tdp, "On" if fanOn else "Off", "Cooling Down" if coolDown else ""))
            logged = True
        except:
            # Error appending data, most likely because credentials are stale.
            # Null out the worksheet so a login is performed at the top of the loop.
            logOutput('Append error, logging in again')
            worksheet = None
            time.sleep(2)
            attempt = attempt + 1
    log.flush()

coolDown = False
coolingDownTime = 0
fanOnTime = 0
fanOn = False

# Attempt to get sensor reading.
humidity, temp = readSensorReading(5)

humidityPct = float(humidity) / 100
Tdp = (B * (np.log(humidityPct) + (A * temp)/(B + temp))) / (A - np.log(humidityPct) - (A * temp)/ (B + temp))
message = 'Temperature: {0:0.1f} C'.format(temp)
message += ', Humidity:    {0:0.1f} %'.format(humidity)
message += ', Dew Point:   {0:0.1f} C'.format(Tdp)
logOutput(message)

if coolDown == True:
    logOutput("Still cooling down - %d left" % (coolingDownTime))
    coolingDownTime -= sleep
    if coolingDownTime <= 0:
        coolDown = False
        coolingDownTime = 0
else:
    if temp <= (Tdp + DEW_POINT_RANGE):
        if fanOn == False:
            fanOn = True
            logOutput("Turning Fan On")
            GPIO.output(24,  GPIO.HIGH)
    else:
        if fanOn == True:
            fanOn = False
            logOutput("Turning Fan Off")
            GPIO.output(24,  GPIO.LOW)
#    if fanOn == True:
#        fanOnTime += sleep
#    if fanOn >= MAX_ON_TIME:
#        fanOn = False
#        fanOnTime
#        logOutput("Turning Fan Off - been on for %d" % (maxOnTime))
#        GPIO.output(24,  GPIO.LOW)
#        coolingDownTime = maxOnTime

logReading(temp, humidity, Tdp, fanOn, 5)