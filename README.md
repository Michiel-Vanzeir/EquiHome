# EquiHome

EquiHome is an automated climate control system designed to maintain a stable indoor temperature. The system interfaces with hardware components such as Peltier elements and thermistors, managed by a custom PID controller written in Python.

## Features

* **Automated Temperature Control:** Utilizes a PID controller to reach and maintain the target temperature with minimal overshoot.
* **Active Cooling & Heating:** Drives a Peltier element for direct heat transfer.
* **Real-time Monitoring:** Continuously reads analog data from a connected thermistor.
* **Ventilation Management:** Actuates servos to automatically open or close windows for natural cooling and fresh air circulation.
* **Modular Design:** Hardware components are decoupled into separate drivers for easier maintenance and testing.

## Project Structure

* `full_control_system.py`: The main execution script that initializes all hardware and runs the primary control loop.
* `controller.py`: Contains the high-level logic for coordinating the temperature sensors and actuators.
* `pid_controller.py`: The Proportional-Integral-Derivative math engine calculating the power output required to maintain the setpoint.
* `peltier.py`: Hardware driver for the Peltier element.
* `thermistor.py`: Handles analog-to-digital conversion and calculates degrees Celsius based on the Steinhart-Hart equation or a lookup table.
* `windows.py`: Controls the PWM signals required to move the window servos.

## Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Michiel-Vanzeir/EquiHome.git](https://github.com/Michiel-Vanzeir/EquiHome.git)
   cd EquiHome