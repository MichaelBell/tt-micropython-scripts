import time
import machine
import random
import gc
import math
from machine import Pin

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard
from ttboard import logging

# TT05 4-bit pipelined multiplier test
tt = DemoBoard()
tt.shuttle.tt_um_btflv_8bit_fp_adder.enable()

def reset_project():
    tt.reset_project(True)
    tt.clock_project_once()
    tt.clock_project_once()
    tt.reset_project(False)
    tt.clock_project_once()
    tt.clock_project_once()

def to_float(n):
    exp = (n >> 3) & 0xf
    mant = n & 0x7
    sign = n >> 7
    
    if exp == 0: val = mant * 0.001953125
    elif exp == 0xf:
        if mant == 0: val = math.inf
        else: val = math.nan
    else:
        mant += 8
        val = mant * 0.001953125 * (2 ** (exp-1))
    
    if sign == 1:
        val = -val
    
    return val

def test_all_values():
    for a in range(256):
        for b in range(256):
            fa = to_float(a)
            fb = to_float(b)
            tt.input_byte = a
            tt.bidir_byte = b
            tt.clock_project_once()
            fo = to_float(tt.output_byte)
            if fa + fb > 240 and fo == math.inf: continue
            if fa + fb < -240 and fo == -math.inf: continue
            max_diff = max(abs(fa), abs(fb), abs(fa+fb)) / 8
            if abs(fo - (fa + fb)) > max_diff: print(f"{fa} + {fb} != {fo} (diff {abs(fo - (fa + fb))}, raw {a}, {b}, {tt.output_byte})")
        #break

reset_project()
test_all_values()

