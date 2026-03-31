def PID_controller(setpoint, reading, prvs_error, integral, Kp, Ki, Kd):
   error = setpoint - reading
   integral += error

   pr = Kp * error  # proportional response
   ir = Ki * integral # integral response
   dr = Kd * (error - prvs_error)  # derivative response
   
   return pr + ir + dr