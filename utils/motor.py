import RPi.GPIO as GPIO
from config import MOTOR_PINS

IN1, IN2, IN3, IN4 = MOTOR_PINS["IN1"], MOTOR_PINS["IN2"], MOTOR_PINS["IN3"], MOTOR_PINS["IN4"]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
GPIO.output([IN1, IN2, IN3, IN4], False)

class MotorController:
    def __init__(self):
        self.stop()

    def forward(self):
        self._set_motor_pins(False, True, False, True)

    def backward(self):
        self._set_motor_pins(True, False, True, False)

    def stop(self):
        self._set_motor_pins(False, False, False, False)

    def _set_motor_pins(self, in1, in2, in3, in4):
        GPIO.output([IN1, IN2, IN3, IN4], [in1, in2, in3, in4])
        print(f"Motor Pins - IN1: {in1}, IN2: {in2}, IN3: {in3}, IN4: {in4}")

motor = MotorController()
