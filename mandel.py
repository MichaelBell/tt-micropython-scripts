## Note this script assumes a different IO pinout to the regular TT demo board
## It is written for https://github.com/MichaelBell/pga2350-tt06/tree/main/hardware

from machine import Pin
from rp2 import PIO, StateMachine, asm_pio

from math import pi, sin, cos

from time import sleep, sleep_ms
import ttcontrol

print("Loading Mandelbrot")
ttcontrol.select_design(844)
ttcontrol.set_clock_hz(90_000_000, 220_000_000)

ttcontrol.enable_ui_in(True)
ttcontrol.enable_uio_in([True]*8)

ttcontrol.write_ui_in(0)
ttcontrol.write_uio_in(0)

ttcontrol.reset_project()

@asm_pio(out_init=(PIO.OUT_LOW,)*16, pull_thresh=16, out_shiftdir=PIO.SHIFT_RIGHT)
def reg_prog():
    pull()
    label("clk_loop")
    jmp(pin, "clk_loop")
    nop()
    out(pins, 16)
    
sm = StateMachine(0, reg_prog, out_base=Pin(1), jmp_pin=Pin(17))
sm.active(1)

last_value = 0

def set_reg(reg, value):
    global last_value
    val1 = ((reg & 7) | ((last_value << 3) & 0xFFF8))
    val2 = ((reg & 7) | ((value << 3) & 0xFFF8))
    #print(f"{val2:04x}")
    while ((machine.mem32[0xd0000004] >> 24) & 1) == 0: pass

    sm.put(val1)
    sm.put(val2)
    #while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass
    last_value = value

set_reg(1, -1900)
set_reg(2, 2400)
set_reg(4, 196)
set_reg(7, -42)

def spin():
    for d in range(0, 361, 2):
        r = d * pi / 180
        s = sin(r)
        c = cos(r)
        tx = int(-1250 * c + 1200 * s) - 650
        ty = int(4000 * s + 2500 * c)
        icx = int(28 * 7 * c)
        icy = int(-42 * 7 * s)
        irx = int(-28 * s)
        iry = int(-42 * c)
        #print(tx, ty, icx, icy, irx, iry)
        set_reg(1, tx)
        set_reg(2, ty)
        set_reg(4, icx)
        set_reg(5, icy)
        set_reg(6, irx)
        set_reg(7, iry)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass
        sleep_ms(50)

@micropython.native
def slide():
    for d in range(0, 360*10, 2):
        r = d * pi / 180
        q = d // 360
        c = cos(r)
        s = sin(r)
        tx = int(-600 * c) - 1600
        ty = int(q * 100 * s) + 2400
        set_reg(1, tx)
        set_reg(2, ty)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass

    for d in range(0, 360*10, 2):
        r = d * pi / 180
        q = (10 - d // 360)
        c = cos(r)
        s = sin(r)
        tx = int(-600 * c) - 1600
        ty = int(q * 100 * s) + 2400
        set_reg(1, tx)
        set_reg(2, ty)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass

def spin2():
    set_reg(1, 0)
    set_reg(2, 0)
    for d in range(0, 360):
        r = d * pi / 180
        s = sin(r)
        c = cos(r)
        icx = int(14 * 7 * c)
        icy = int(-21 * 7 * s)
        irx = int(-14 * s)
        iry = int(-21 * c)
        #print(tx, ty, icx, icy, irx, iry)
        set_reg(4, icx)
        set_reg(5, icy)
        set_reg(6, irx)
        set_reg(7, iry)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass
        #sleep_ms(50)

def zoom(x, y):
    set_reg(5, 0)
    set_reg(6, 0)
    
    x = int(x * 2**10)
    y = int(y * 2**11)
    
    for z in range(196, 14, -2):
        icx = z
        iry = int(-z / 4.67)
        tx = x - (icx * 51) // 8
        ty = y - (iry * 240) // 4
        #print(tx, ty, icx, iry)
        set_reg(1, tx)
        set_reg(2, ty)
        set_reg(4, icx)
        set_reg(7, iry)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass
        
    sleep(2)
        
    for z in range(14, 197, 2):
        icx = z
        iry = int(-z / 4.67)
        tx = x - (icx * 51) // 8
        ty = y - (iry * 240) // 4
        set_reg(1, tx)
        set_reg(2, ty)
        set_reg(4, icx)
        set_reg(7, iry)
        while ((machine.mem32[0xd0000004] >> 24) & 1) == 1: pass
