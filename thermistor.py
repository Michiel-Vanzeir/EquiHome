import board
import time
import analogio
import math


# Setup thermistor pins
thermistor_pin_downstairs = analogio.AnalogIn(board.GP28)
thermistor_pin_upstairs1 = analogio.AnalogIn(board.GP27)
thermistor_pin_upstairs2 = analogio.AnalogIn(board.GP26)

# Thermistor & circuit values
SERIE_WEERSTAND = 10000
NOMINALE_WEERSTAND = 10000
NOMINALE_TEMP = 25
B_COEFFICIENT = 3950

# Reads the temperature of a thermistor in degrees Celsius
def get_temperature(pin):
    raw_value = pin.value

    # handle faulty readings
    if raw_value >= 65535:
        return -273.15
    if raw_value <= 0:
        return -273.15

    # Determine the thermistor resistance
    weerstand = SERIE_WEERSTAND * ((65535 / raw_value) - 1)

    # Steinhart temperature calculation
    steinhart = weerstand / NOMINALE_WEERSTAND
    steinhart = math.log(steinhart)
    steinhart /= B_COEFFICIENT
    steinhart += 1.0 / (NOMINALE_TEMP + 273.15)
    steinhart = 1.0 / steinhart

    return steinhart - 273.15

while True:
    print("Temperature downstairs:", get_temperature(thermistor_pin_downstairs))
    time.sleep(0.05)
    print("Temperature upstairs, room 1:", get_temperature(thermistor_pin_upstairs1))
    time.sleep(0.05)
    print("Temperature upstairs, room 2:", get_temperature(thermistor_pin_upstairs2))
    time.sleep(2)