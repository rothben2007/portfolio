# You will need to install pyserial
# Run the following command on the command line --> pip install pyserial

# You may need to install some libraries if you PC does not have them
# You need pyserial and pygame to install them type:
# pip install pyserial
# pip install pygame
#V9 fully working as to orginal input map with triggers and right horizontal joystick being yaw


import serial
import sys
import time
from serial.tools.list_ports import comports
import pygame

comPort = "COM18"
for port in comports():
    s = str(port)
    if "USB Serial" in s:
        comPort = str(port).split(" ")[0]
        print("Will connect using ->", comPort)
        
if len(sys.argv) == 2:
    comPort = sys.argv[1]
    print("Will connect using ->", comPort)

# Open the serial port to the pico
try:
    ser = serial.Serial(comPort, 115200, timeout=1)
except Exception as e:
    print("***** Unable to connect to motor controller *****")
    print("Make sure only one USB Serial port is active")
    print("Make sure putty is not running")
    print("Change code to match the correct com port")
    print(e)

def setSpeed(motor, speed, log=True):
    if abs(speed) >63:
        print("Speed needs to be greater than -62 and less then 63")
        return False
    if motor < 0 or motor >= 6:
        print("Motor number must be between 0 and 5")
        return False
    if log:
      print("Set Speed motor ", motor,"->", speed)
    cmd = "m,%d,%d\n" %  (motor, speed)
    try:
        if log:
          print("Send cmd:", cmd[0:-1])
        ser.write(bytes(cmd, "utf-8"))
    except Exception as e:
        print("***** Unable to send command to motors *****")
        print(e)
        return False
    return True

def readLinesPico():
    while True:
        line = ser.readline()
        if not line:
            return
        if len(line) > 2:
            print(line[0:-2].decode('utf-8').replace(">",""))
         
def doTask(task):
    ar = task.split(",")
    cmd = task[0]
    if cmd == 'h':
       printHelp()
    elif cmd >= "0" and cmd < "6":
       if len(ar) != 2:
          print("Try again with a speed")
          return False
       setSpeed(int(cmd), int(ar[1]))
    elif cmd == 'a':
        if len(ar) != 2:
           print("Try again with a speed")
           return False
        for i in range(6):
            if(not setSpeed(i, int(ar[1]))):
              return False
            time.sleep(.02)
        print("Delay 10 seconds")
        time.sleep(10)
        for i in range(6):
            setSpeed(i, 0)
            time.sleep(.02)
    elif cmd == "j":
        setupJoyStick()
    elif cmd == "r":
        readLinesPico()
    # Close the port
    elif cmd == "q":
        if ser is not None:
           print("Close Serial port to Pico")
           ser.close()
           return True
    else:
        print("Try again")
    return False

lastSpeed = [0,0,0,0,0,0]
def setSpeedCheck(motor, speed):
    if abs(speed) < 10:
        speed = 0
        setSpeed(motor,0, log=False)
        lastSpeed[motor] = speed
    if abs(speed - lastSpeed[motor]) > 5:
        setSpeed(motor, lastSpeed[motor], log=False)
        lastSpeed[motor] = speed
        
        
def setupJoyStick():
    pygame.init()
    pygame.joystick.init()
    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        print("No joystick found.")
        return
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("Joystick detected:", joystick.get_name())

    # Normalize initial joystick values
    axes_initial = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    
    running = True
    motor_speeds = [0] * 6  # Track motor speeds to avoid conflicts
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.JOYBUTTONDOWN:
                print("Button pressed:", event.button)
                if event.button == 6:  # Back button to exit
                    running = False
                elif event.button == 4:  # LB - Yaw Left (Corrected Based on Manual Testing)
                    print("LB Pressed: Turning left")
                    setSpeed(0, 60)  # M0 CW
                    setSpeed(1, 60)  # M1 CCW
                elif event.button == 5:  # RB - Yaw Right (Corrected Based on Manual Testing)
                    print("RB Pressed: Turning right")
                    setSpeed(0, -60)  # M0 CCW
                    setSpeed(1, -60)  # M1 CW
            
            elif event.type == pygame.JOYBUTTONUP:
                if event.button == 4:  # LB released
                    print("LB Released: Stopping yaw left")
                    setSpeed(0, 0)
                    setSpeed(1, 0)
                elif event.button == 5:  # RB released
                    print("RB Released: Stopping yaw right")
                    setSpeed(0, 0)
                    setSpeed(1, 0)
                elif event.button in [7, 8]:  # Triggers released
                    setSpeed(4, 0)
                    setSpeed(5, 0)
            
            elif event.type == pygame.JOYAXISMOTION:
                speed = int(event.value * 60)
                
                if abs(speed) < 30:  # Ignore values 0-29, only 30-60 do something
                    speed = 0
                
                if event.axis == 1:  # Left joystick Y (Forward/Backward)
                    setSpeed(0, -speed)  # M0 Forward/Backward
                    setSpeed(1, speed)  # M1 Forward/Backward
                    
                    
                elif event.axis == 0:  # Left joystick X (Strafing Left/Right)
                    setSpeed(2, -speed)  # M2 Strafe Left/Right
                    setSpeed(3, speed)   # M3 Strafe Left/Right
                elif event.axis == 2:  # Right joystick horz (yaw Left/Right)
                    setSpeed(0, -speed)  # M0 Yaw Left/Right
                    setSpeed(1, -speed)   # M1 Yaw Left/Right
                elif event.axis == 3:  # Right joystick Y (Pitch Up/Down) - FIXED
                    setSpeed(4, speed)  # M4 CW (Pitch Up)
                    setSpeed(5, speed)  # M5 CCW (Pitch Up)
                elif event.axis == 5:  # Right Trigger (Move Up) - FIXED
                    normalized_speed = int((event.value + 1) / 2 * 60)  # Normalize -1 to 1 into 0 to 60
                    setSpeed(4, -normalized_speed)  # M4 CW
                    setSpeed(5, normalized_speed)  # M5 CW (Correct Up Movement)
                elif event.axis == 4:  # Left Trigger (Move Down) - FIXED
                    normalized_speed = int((event.value + 1) / 2 * 60)  # Normalize -1 to 1 into 0 to 60
                    setSpeed(4, normalized_speed)  # M4 CCW
                    setSpeed(5, -normalized_speed)  # M5 CCW (Correct Down Movement)
    
    pygame.quit()

def printHelp():
    helpStr = "Set speed of motor 0 to -20 type 0,-20\nSet Speed motor 1 to 45 type 1,45\n"
    helpStr += "Type a,50 to run all motors at speed 50\nType r to see results from PICO\n"
    helpStr += "Type j to enter joy stick mode\nHit Back button on game pad to return to motor control\n"
    helpStr += "Type q to quit motor control\nType h Show Help\n"
    if ser is None:
       helpStr += "**** Not connected to port " + comPort + " *****\n"
    else:
       helpStr += "Connected to port " + comPort + "\n"
    print(helpStr)

def resetPico():
  ser.write(b'\x03')
  time.sleep(.5)
  ser.write(b'\x04')

printHelp()
resetPico()

while True:
    print(">", end='',  flush=True)
    task = sys.stdin.readline().lower()
    # RUn the indicated task if doTask returns true a quit was requested
    if doTask(task):
        break
   
   