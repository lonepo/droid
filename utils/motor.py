# utils/motor.py
import RPi.GPIO as GPIO
import time
from config import MOTOR_PINS

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup motor pins
for pin in MOTOR_PINS["driver1"].values():
    GPIO.setup(pin, GPIO.OUT)

# PWM setup (1 kHz frequency)
pwm1 = GPIO.PWM(MOTOR_PINS["driver1"]["EN1"], 1000)
pwm2 = GPIO.PWM(MOTOR_PINS["driver1"]["EN2"], 1000)

pwm1.start(0)
pwm2.start(0)

class MotorController:
    def __init__(self):
        self.stop()

    def forward(self, duration=0, speed=100):
        """Run motor forward. If duration > 0, stop after duration seconds."""
        GPIO.output(MOTOR_PINS["driver1"]["C1A"], GPIO.HIGH)
        GPIO.output(MOTOR_PINS["driver1"]["C1B"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C2A"], GPIO.HIGH)
        GPIO.output(MOTOR_PINS["driver1"]["C2B"], GPIO.LOW)
        pwm1.ChangeDutyCycle(speed)
        pwm2.ChangeDutyCycle(speed)

        if duration > 0:
            time.sleep(duration)
            self.stop()

    def backward(self, duration=0, speed=100):
        """Run motor backward. If duration > 0, stop after duration seconds."""
        GPIO.output(MOTOR_PINS["driver1"]["C1A"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C1B"], GPIO.HIGH)
        GPIO.output(MOTOR_PINS["driver1"]["C2A"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C2B"], GPIO.HIGH)
        pwm1.ChangeDutyCycle(speed)
        pwm2.ChangeDutyCycle(speed)

        if duration > 0:
            time.sleep(duration)
            self.stop()

    def stop(self):
        pwm1.ChangeDutyCycle(0)
        pwm2.ChangeDutyCycle(0)
        GPIO.output(MOTOR_PINS["driver1"]["C1A"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C1B"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C2A"], GPIO.LOW)
        GPIO.output(MOTOR_PINS["driver1"]["C2B"], GPIO.LOW)
        print("Motor stopped")

motor = MotorController()
