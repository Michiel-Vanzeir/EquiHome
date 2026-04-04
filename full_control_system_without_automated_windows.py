import analogio
import board
import math
import pwmio
import time


class HouseControlSystem:
    def __init__(self, Kp=0.8, Ki=0.2, Kd=0.05, setpoint=15):
        # Thermistor & wiring values
        self._SERIES_RESISTANCE = 10000
        self._NOMINAL_RESISTANCE = 10000
        self._NOMINAL_TEMP = 25
        self._B_COEFFICIENT = 3950

        # PID controller setup
        self._Ki = Ki
        self._Kp = Kp
        self._Kd = Kd
        self._setpoint = setpoint # Setpoint temperature in degrees Celsius
        self._prvs_error = 0
        self._integral = 0

        # Pin setup
        self._thermistor_pins = [analogio.AnalogIn(pin) for pin in (board.GP28,board.GP27,board.GP26)] # [downstairs, upstairs room 1, upstairs room 2, outside]
        self._peltier_elements = [pwmio.PWMOut(pin, frequency=1000) for pin in (board.GP14, board.GP15)]


    # Sets the peltier element's power at the right percentage
    def set_peltiers_power(self, percentage):
        for peltier in self._peltier_elements:
            peltier.duty_cycle = int(percentage * (65535/100)) # 65535 is 3.3V
        print('De peltiers staan op', percentage, '%')
        
    # Returns the temperature measured by the thermistors as a list: [downstairs, upstairs room 1, upstairs room 2, outside, indoor average]
    def get_temperature(self):
        temperature_readings = []

        for thermistor in self._thermistor_pins:
          raw_value = thermistor.value

          # Handle faulty thermistor readings
          if raw_value >= 65535:
              return -273.15
          if raw_value <= 0:
              return 999.0

          resistance = self._SERIES_RESISTANCE* ((65535 / raw_value) - 1)

          steinhart = resistance / self._NOMINAL_RESISTANCE
          steinhart = math.log(steinhart)
          steinhart /= self._B_COEFFICIENT
          steinhart += 1.0 / (self._NOMINAL_TEMP + 273.15)
          steinhart = 1.0 / steinhart

          temperature_readings.append(steinhart - 273.15)
        
        temperature_readings.append(sum(temperature_readings[:3])/ 3)
    
        return temperature_readings
    
    # PID loop iteration
    def PID_iteration(self, reading) -> float:
        error = self._setpoint - reading
        self._integral += error

        pr = self._Kp * error  # proportional response
        ir = self._Ki * self._integral # integral response
        dr = self._Kd * (error - self._prvs_error)  # derivative response
        
        return -(pr + ir + dr)

    # Change the setpoint temperature
    def set_setpoint(self, temperature):
        self._setpoint = temperature

House = HouseControlSystem()

while True:
    # Measure the temperatures: [downstairs, upstairs room 1, upstairs room 2, indoor average]
    thermistor_readings = House.get_temperature()
    
    # Calculate PID response
    response = House.PID_iteration(thermistor_readings[-1])
    if response < 0:
        print('Temperatuur lager dan setpoint, peltiers uitgeschakeld')
        response = 0
    elif response > 100:
        response = 100
    # Set Peltier elements' power
    House.set_peltiers_power(response)
    

    time.sleep(0.1)
    
    print("Temperature at pin 1:", thermistor_readings[0])
    time.sleep(0.1)
    print("Temperature at pin 2:", thermistor_readings[1])
    time.sleep(0.1)
    print("Temperature at pin 3:", thermistor_readings[2])
    time.sleep(1)



