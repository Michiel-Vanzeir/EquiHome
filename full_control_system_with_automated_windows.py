import analogio
import board
import math
import pwmio
import time
import adafruit_motor
from adafruit_httpserver import Server, Request, Response, GET, POST, OPTIONS
import wifi
import json
import socketpool


class HouseControlSystem:
    def __init__(self, Kp=32, Ki=1.8, Kd=0.0, setpoint=20.0):
        # Thermistor & wiring values
        self._SERIES_RESISTANCE = 10000
        self._NOMINAL_RESISTANCE = 10000
        self._NOMINAL_TEMP = 25
        self._B_COEFFICIENT = 3950

        # PID controller setup
        self._Ki = Ki
        self._Kp = Kp
        self._Kd = Kd
        self._setpoint = setpoint
        self._prvs_error = 0
        self._integral = 0
        self._error = 0
        self._PID_control = "PID"

        # Pin setup
        self._pwm_pins = [pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=50) for pin in (board.GP0,)] # Thermistor readings
        self._servos = [adafruit_motor.servo.Servo(pwm) for pwm in self._pwm_pins] # These servos control the windows
        self._thermistor_pins = [analogio.AnalogIn(pin) for pin in (board.GP28,board.GP27,board.GP26)] # [downstairs, upstairs, PCM cavity, average of all thermistors]
        self._peltier_elements = [pwmio.PWMOut(pin, frequency=1000) for pin in (board.GP2, board.GP3)] # Peltier elements

        # Dashboard data
        # Current temperature readings
        self._t1 = 20 
        self._t2 = 20
        self._t3 = 20
        self._avg = 20
        # Current peltier power
        self.peltier1_power = 0
        self.peltier2_power = 0
            
    # Sets all servo motors to a given angle
    def set_servos(self, angle):
        for servo in self._servos:
            servo.angle = angle

    # Sets the peltier element's power at the right percentage
    def set_peltier_power(self, peltier_id, percentage):
        self._peltier_elements[peltier_id-1].duty_cycle = int(percentage * (65535/100))
        if peltier_id == 1:
            self.peltier1_power = percentage
        else:
            self.peltier2_power = percentage

    # Changes the PID setpoint
    def set_setpoint(self, setpoint):
        self._setpoint = setpoint

    # Returns the temperature measured by the thermistors as a list: [downstairs, upstairs, PCM cavity, average of all thermistors]
    def get_temperature(self):
        temperature_readings = []

        for thermistor in self._thermistor_pins:
          raw_value = thermistor.value

          # Handle faulty thermistor readings (replace with probably somewhat correct measurements)
          if raw_value >= 65535:
              return [20.0]*4
          if raw_value <= 0:
              return [20.0]*4

          resistance = self._SERIES_RESISTANCE* ((65535 / raw_value) - 1)

          steinhart = resistance / self._NOMINAL_RESISTANCE
          steinhart = math.log(steinhart)
          steinhart /= self._B_COEFFICIENT
          steinhart += 1.0 / (self._NOMINAL_TEMP + 273.15)
          steinhart = 1.0 / steinhart

          temperature_readings.append(steinhart - 273.15)

        temperature_readings.append(sum(temperature_readings[:3])/ 3)

        # Update dashboard data
        self._t1, self._t2, self._t3, self._avg = temperature_readings
        
        return temperature_readings

    # PID loop iteration
    def PID_iteration(self, reading):
        error = -(self._setpoint - reading)
        self._error = error
        
        # Make sure the integral can't get too large or small
        if (self._integral < 100 and self._integral > -100) or (self._integral > 100 and error < 0) or (self._integral < -100 and error > 0):
            self._integral += error

        pr = self._Kp * error  # proportional response
        ir = self._Ki * self._integral # integrative response
        dr = self._Kd * (error - self._prvs_error)  # differential response

        return (pr + ir + dr)

    # Change the setpoint temperature
    def set_setpoint(self, temperature):
        self._setpoint = temperature


# --- Wifi Setup ---
print("Connecting to WiFi...")
wifi.radio.connect('Rpitest', 'felix2026')
print("Connected! IP:", wifi.radio.ipv4_address)
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

# --- Initialize House Class ---
House = HouseControlSystem()

# --- GET/POST/OPTIONS requests ---
@server.route("/api/data", GET)
def get_data(request: Request):
    """Sends current temperatures to the dashboard."""
    
    payload = {
        "house1": {"t1": House._t1, "t2": House._t2, "t3": House._t3, "t4": House._avg},
        "peltiers": {"p1": House.peltier1_power, "p2": House.peltier2_power},
        "status": House._PID_control
    }
    
    headers = {"Access-Control-Allow-Origin": "*"}
    return Response(request, body=json.dumps(payload), content_type="application/json", headers=headers)

@server.route("/api/control", [POST, OPTIONS])
def post_control(request: Request):
    """Receives control commands from the dashboard."""
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if request.method == "OPTIONS":
        return Response(request, headers=headers)
    
    data = request.json()
    
    if "peltier1" in data:
        House.set_peltier_power(1, float(data["peltier1"]))
    if "peltier2" in data:
        House.set_peltier_power(2, float(data["peltier2"]))
        
    if "windows_open" in data:
        angle = 15 if data["windows_open"] else 180 # servos keep pushing against the wall if you use angle 0
        House.set_servos(angle)
        
    if "status" in data:
        House._PID_control = data["status"]
        print("Changed status to:", House._PID_control)
        
    if "setpoint" in data:
        House.set_setpoint(float(data["setpoint"]))
        print("New PID setpoint:", House._setpoint)

    return Response(request, body=json.dumps({"status": "success"}), content_type="application/json", headers=headers)

server.start(str(wifi.radio.ipv4_address), port=5000)

# --- Loop Helper Variables --- 
last_thermistor_reading_time = time.monotonic()
INTERVAL = 0.01 
historic_readings = []
counter = 0 # To only calculate a PID reponse every 1 seconds

while True:
    try:
        server.poll()
        now = time.monotonic()
        
        # Every 0.01 seconds
        if now - last_thermistor_reading_time >= INTERVAL:
            thermistor_readings = House.get_temperature()
            historic_readings.append(thermistor_readings[-1])
            counter += 1
            
            # Every second
            if counter % 100 == 0:
                if House._PID_control == "PID": 
                    # Calculate the average thermistor reading to decrease noise
                    avg_thermistor_reading = sum(historic_readings) / len(historic_readings)
                    response = House.PID_iteration(avg_thermistor_reading)
                    
                    # Limit Peltier response to valid range
                    if response < 0:
                        response = 0
                    elif response > 100:
                        response = 100
                    
                    House.set_peltier_power(1, response) # arguments: (peltier_id, power percentage)
                    House.set_peltier_power(2, response) # arguments: (peltier_id, power percentage)
                
                historic_readings = []
                counter = 0

            # Reset timer
            last_thermistor_reading_time = now
            
    except Exception as e:
        print("Prevented crash in loop:", e)
        time.sleep(0.1)
