import time
import machine
import random
import gc
from machine import Pin

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard
from ttboard import logging

# TT05 4-bit pipelined multiplier test
tt = DemoBoard()
tt.shuttle.tt_um_4_bit_pipeline_multiplier.enable()

def reset_project():
    tt.reset_project(True)
    tt.clock_project_once()
    tt.clock_project_once()
    tt.reset_project(False)
    tt.clock_project_once()
    tt.clock_project_once()

def test_all_values():
    for a in range(16):
        for b in range(16):
            tt.input_byte = a | (b << 4)
            tt.clock_project_once()
            tt.clock_project_once()
            if tt.output_byte != a * b: print(f"{a} * {b} != {tt.output_byte}")

def test_pipeline():
    tt.input_byte = 0
    tt.clock_project_once()
    last_result = 0
    for i in range(10000):
        a = random.randint(0,15)
        b = random.randint(0,15)
        tt.input_byte = a | (b << 4)
        tt.clock_project_once()
        if tt.output_byte != last_result: print(f"Expected {last_result}, got {tt.output_byte}")
        last_result = a * b

test_all_values()
test_pipeline()
