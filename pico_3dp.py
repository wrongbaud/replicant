import chipwhisperer.common.results.glitch as glitch
import chipwhisperer as cw
import serial
import time
import sys
import os
from printrun.printcore import printcore

p = printcore('/dev/ttyUSB0',115200)

while not p.online:
	time.sleep(0.1)

scope = None
# SWD device variable
dev = ""
usb_path = sys.argv[1]

class ChipShouterPicoEMP:
    def __init__(self, port='/dev/ttyACM0'):
        self.pico = serial.Serial(port, 115200)
        self.pico.write(b'\r\n')
        time.sleep(0.1)
        ret = self.pico.read(self.pico.in_waiting)
        if b'PicoEMP Commands' in ret:
            print('Connected to ChipSHOUTER PicoEMP!')
        else:
            raise OSError('Could not connect to ChipShouter PicoEMP :(')

    def disable_timeout(self):
        self.pico.write(b'disable_timeout\r\n')
        time.sleep(1)
        assert b'Timeout disabled!' in self.pico.read(self.pico.in_waiting)
        
    def arm(self):
        self.pico.write(b'arm\r\n')
        time.sleep(1)
        assert b'Device armed' in self.pico.read(self.pico.in_waiting)
        
    def disarm(self):
        self.pico.write(b'disarm\r\n')
        time.sleep(1)
        assert b'Device disarmed!' in self.pico.read(self.pico.in_waiting)
        
    def external_hvp(self):
        self.pico.write(b'external_hvp\r\n')
        time.sleep(1)
        assert b'External HVP mode active' in self.pico.read(self.pico.in_waiting)
        
    def print_status(self):
        self.pico.write(b'status\r\n')
        time.sleep(1)
        print(self.pico.read(self.pico.in_waiting).decode('utf-8'))
    
    def setup_external_control(self):
        self.disable_timeout()
        self.external_hvp()
        self.print_status()

'''
boot_mode_enable
Used to check if boot rom SDP check has been bypassed
1. Reset the STLink adapter using the usbreset program
2. Attempt to communicate with the DAP over SWD
'''
def boot_mode_enable():
    global dev
    import swd
    pc = 0
    try:    
        os.system(f"sudo /home/pi/glitch/replicant/python/usbreset {usb_path}")
        dev = swd.Swd()
        pc = dev.get_version().str
    except:
        del swd
        pass
    return pc

'''
pi_serial
Used to check if boot mode bypass was successful
'''
def pi_serial():
    # Open Pi serial port at 115200
    baud = 115200
    devpath = "/dev/ttyS0"
    ser = serial.Serial(timeout=1)
    ser.port = devpath
    ser.baudrate = baud
    ser.open()
    ser.write(b'\x7f')
    test = ser.read(1)
    ser.close()
    return test

def uart_test():
    global scope
    prog = cw.programmers.STM32FProgrammer
    scope.io.tio1 = "serial_rx"
    scope.io.tio2 = "serial_tx"
    stmprog = prog()
    stmprog.scope = scope
    stm32serial = stmprog.stm32prog()
    stm32serial.open_port(baud=115200)
    stm32serial.sp.write('\x7F')
    ret = stm32serial.sp.read(1)
    return ret and ret[0] == 0x79

def reboot_flush():            
    global scope
    # Cut power to target device
    scope.io.target_pwr = False
    # Pull reset low
    scope.io.nrst = False
    time.sleep(0.1)
    # Set up CW for glitching
    scope.arm()
    # Put reset in high impedance mode (we are triggering off of it)
    scope.io.nrst = "high_z"
    # Power the target and wait for the glitch to trigger
    scope.io.target_pwr = True

scope = cw.scope()
scope.io.target_pwr = "high_z"

'''
The following lines were pulled from CW jupyter notebooks from the tutorials/documentation
'''
try:
    if SS_VER == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    elif SS_VER == "SS_VER_2_0":
        raise OSError("SS_VER_2_0 is deprecated. Use SS_VER_2_1")
    else:
        target_type = cw.targets.SimpleSerial
except:
    SS_VER="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
    print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
    scope = cw.scope()
    target = cw.target(scope, target_type)

print("Found CW!")

# Set up scope specific parameters
scope.clock.clkgen_freq = 100E6
# Trigger on IO4 this is connected to our reset line
scope.trigger.triggers = 'tio4'
scope.adc.samples = 24400
scope.adc.offset = 0
scope.adc.basic_mode = "rising_edge"
scope.adc.decimate = 10
scope.glitch.clk_src = "clkgen" # set glitch input clock
scope.glitch.output = "enable_only" # glitch_out = clk ^ glitch
scope.glitch.trigger_src = "ext_single" # glitch only after scope.arm() called
scope.io.glitch_lp = False
scope.io.glitch_hp = False
scope.io.hs2 = "glitch"
scope.io.tio3 = "high_z"

pico = ChipShouterPicoEMP()
pico.setup_external_control()

def wait_for_hv():
    while scope.io.tio_states[2] != 0:
        time.sleep(0.1)

g_step = 1
gc = glitch.GlitchController(groups=["success", "failure"], parameters=["width", "offset", "x", "y", "ext_offset"])
#gc = glitch.GlitchController(groups=["success", "failure"], parameters=["width", "offset","ext_offset"])
gc.set_global_step(g_step)
gc.set_range("width", 40, 40)
gc.set_range("offset", -45, -45)
#gc.set_range("ext_offset", 19700, 19800)
gc.set_range("x", 207, 216)
gc.set_range("y", 86, 90)
gc.set_range("ext_offset", 19500, 19800)
#gc.set_range("ext_offset", 50000000, 50000100)
#gc.set_range("ext_offset", 2500000, 2500100)
reboot_flush()
# How many times we attempt each configuration
sample_size = 15
# How many clock cycles we pull low for
scope.glitch.repeat=100
#sample_size = 50
# How many clock cycles we pull low for
#scope.glitch.repeat=20
offsets = []
pico.arm()
for glitch_setting in gc.glitch_values():
    scope.glitch.width = glitch_setting[0]
    scope.glitch.offset = glitch_setting[1]
    scope.glitch.ext_offset = glitch_setting[2]
    x = glitch_setting[2]
    y = glitch_setting[3]
    p.send("G0 X%d" % (x))
    time.sleep(0.1)
    p.send("G0 Y%d" % (y))
    successes = 0
    failures = 0
    print(scope.glitch.ext_offset)
    successes = 0
    failures = 0
    for i in range(sample_size):
        # Reboot target, arm scope, wait for glitch
        wait_for_hv()
        reboot_flush()
        # Allow target time to initialize
        time.sleep(2)
        # Reset glitch lines as reccomended in docs
        # Check to see if glitch was successful
        x = boot_mode_enable()
        if x:
            print("Success! -- offset = {}, width = {}, ext_offset = {}".format(scope.glitch.offset, scope.glitch.width, scope.glitch.ext_offset))
            successes += 1
            break
    if successes > 0:                
        print("successes = {}, failures = {}, offset = {}, width = {}, ext_offset = {}".format(successes, failures, scope.glitch.offset, scope.glitch.width, scope.glitch.ext_offset))
        break
pico.disarm()
print("Done glitching")
