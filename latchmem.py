import gc
gc.threshold(50000)
import micropython
import machine
from time import sleep_ms

from ttcontrol import *
from ttboard.util.platform import write_ui_in_byte, write_uio_byte, read_uo_out_byte

# Use this method to select project
# to ensure high frequency clock is running when selecting
# this clears a possible contention within the design
set_clock_hz(66000000)
select_design(620)
sleep_ms(1)
clk_pin.init(Pin.OUT, value=0)

def enable_uio(enabled):
    for pin in uio:
        pin.init(Pin.OUT if enabled else Pin.IN, Pin.PULL_DOWN)

enable_ui_in(True)
enable_uio(True)

@micropython.native
def cycle_clock():
    machine.mem32[0xd0000014] = 1 # Set
    machine.mem32[0xd0000018] = 1 # Clear

def write_byte(addr, val):
    write_ui_in_byte(addr | 0x80)
    write_uio_byte(val)
    cycle_clock()
    old_val = read_uo_out_byte()
    write_ui_in_byte(addr)
    cycle_clock()
    assert read_uo_out_byte() == val
    return old_val
    
def read_byte(addr):
    write_ui_in_byte(addr)
    cycle_clock()
    return read_uo_out_byte()

