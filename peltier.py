import pwmio
import board
import time

# Setup the peltier pins
peltier_upstairs = pwmio.PWMOut(board.GP14, frequency=1000)
peltier_downstairs = pwmio.PWMOut(board.GP15, frequency=1000)

# Sets the peltier element's power at the right percentage
def set_peltier_power(peltier, percentage):
    peltier.duty_cycle = int(percentage * (65535/100)) # 65535 is 3.3V

# Set the peltier power
set_peltier_power(peltier_upstairs, 100)
set_peltier_power(peltier_downstairs, 100)