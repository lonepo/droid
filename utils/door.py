import RPi.GPIO as GPIO
from config import DOOR_PINS
import time

IN5, IN6 = DOOR_PINS["IN5"], DOOR_PINS["IN6"]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([IN5, IN6], GPIO.OUT)
GPIO.output([IN5, IN6], False)

def operate_door(open_door=True):
    print('Operating Door...')
    if open_door:
        GPIO.output(IN5, True)
        GPIO.output(IN6, False)
        time.sleep(3)
        GPIO.output(IN5, False)
        time.sleep(6)
        GPIO.output(IN5, False)
        GPIO.output(IN6, True)
        time.sleep(3)
    else:
        GPIO.output(IN5, False)
        GPIO.output(IN6, False)
