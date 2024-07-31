import time
import machine
import gc
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard
from ttboard import logging

tt = DemoBoard()
tt.shuttle.tt_um_tt05_analog_test.enable()

# Cycle the DAC input up - repeating 0, 1, 2, 3, 4, 5, 6, 7
@asm_pio(out_init=(PIO.OUT_LOW,)*3)
def count_up_prog():
    label("top")
    mov(pins, invert(x))
    jmp(x_dec, "top")

# Cycle the DAC input down - repeating 7, 6, 5, 4, 3, 2, 1, 0
@asm_pio(out_init=(PIO.OUT_LOW,)*3)
def count_down_prog():
    label("top")
    mov(pins, x)
    jmp(x_dec, "top")
    
tt.input_byte = 8

machine.freq(128_000_000)

# Frequency of input change is half the configured frequency here
sm = StateMachine(0, count_up_prog, out_base=Pin(9), freq=800000)
sm.active(1)
