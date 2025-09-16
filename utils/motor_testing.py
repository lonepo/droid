# motor_test.py
# Test motors with Raspberry Pi 4B (2 Motor Driver Modules)

import RPi.GPIO as GPIO
import time

# -------------------------------
# Pin Mapping
# -------------------------------

# Module 1 (Driver 1)
M1_IN1 = 17  # BCM 17, Physical 11
M1_IN2 = 27  # BCM 27, Physical 13
M1_EN  = 18  # BCM 18, Physical 12 (PWM)

M2_IN1 = 22  # BCM 22, Physical 15
M2_IN2 = 23  # BCM 23, Physical 16
M2_EN  = 13  # BCM 13, Physical 33 (PWM)

# Module 2 (Driver 2)
M3_IN1 = 5   # BCM 5, Physical 29
M3_IN2 = 6   # BCM 6, Physical 31
M3_EN  = 19  # BCM 19, Physical 35 (PWM)

# (You can add more motors if Module 2 has second channel)

# -------------------------------
# Setup
# -------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor pin groups
motor_pins = [
    (M1_IN1, M1_IN2, M1_EN),
    (M2_IN1, M2_IN2, M2_EN),
    (M3_IN1, M3_IN2, M3_EN)
]

# Set up pins
for in1, in2, en in motor_pins:
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(en, GPIO.OUT)

# Initialize PWM (1000 Hz frequency)
pwm_list = []
for _, _, en in motor_pins:
    pwm = GPIO.PWM(en, 1000)
    pwm.start(0)  # start with 0% duty cycle
    pwm_list.append(pwm)

# -------------------------------
# Motor Control Functions
# -------------------------------
def motor_forward(motor_index, speed=50):
    """Run selected motor forward at given speed (0-100)."""
    in1, in2, en = motor_pins[motor_index]
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    pwm_list[motor_index].ChangeDutyCycle(speed)

def motor_backward(motor_index, speed=50):
    """Run selected motor backward at given speed (0-100)."""
    in1, in2, en = motor_pins[motor_index]
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    pwm_list[motor_index].ChangeDutyCycle(speed)

def motor_stop(motor_index):
    """Stop selected motor."""
    in1, in2, en = motor_pins[motor_index]
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    pwm_list[motor_index].ChangeDutyCycle(0)

# -------------------------------
# Test Routine
# -------------------------------
try:
    while True:
        for i in range(len(motor_pins)):
            print(f"\nTesting Motor {i+1} forward...")
            motor_forward(i, 70)
            time.sleep(2)

            print(f"Testing Motor {i+1} backward...")
            motor_backward(i, 70)
            time.sleep(2)

            print(f"Stopping Motor {i+1}")
            motor_stop(i)
            time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting and cleaning up...")
    for i in range(len(motor_pins)):
        motor_stop(i)
    for pwm in pwm_list:
        pwm.stop()
    GPIO.cleanup()
