import adafruit_motor
import pwmio
import time
import board

servo_pin = pwmio.PWMOut(board.GP0, duty_cycle=2**15, frequency=50)
servo = adafruit_motor.servo.Servo(servo_pin)

while True:
  print('Window closed!')
  servo.angle = 0 
  time.sleep(2)
  print('Window opened!')
  servo.angle = 180
  time.sleep(4)