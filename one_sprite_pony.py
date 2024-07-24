import time
import machine
import gc
from machine import SPI, Pin

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

from pio_spi import PIOSPI

tt = DemoBoard()
tt.shuttle.tt_um_top_mole99.enable()

spi_sel = Pin(21, Pin.OUT)
spi_sel.on()
spi = PIOSPI(1, Pin(22), Pin(23), Pin(24), freq=2000000, cpha=True)

vs = Pin(8, Pin.IN)

def wait_for_vsync():
    while not vs.value():
        time.sleep_us(10)

def spi_cmd(data, dummy_len=0, read_len=0, sync=True):
    dummy_buf = bytearray(dummy_len)
    read_buf = bytearray(read_len)
    
    if sync:
        gc.collect()
        wait_for_vsync()
    spi_sel.off()
    spi.write(bytearray(data))
    if dummy_len > 0:
        spi.readinto(dummy_buf)
    if read_len > 0:
        spi.readinto(read_buf)
    spi_sel.on()
    
    return read_buf

def print_bytes(data):
    for b in data: print("%02x " % (b,), end="")
    print()

def sprite2bytes(sprite):
    bits = ""
    
    for row in sprite:
        for bit in row:
            bits += str(bit)
    
    byte_data = [int(bits[x:x+8], 2) for x in range(0, len(bits), 8)]
    print_bytes(byte_data)
    
    return byte_data

def set_sprite(sprite):
    sprite_bytes = bytearray(sprite2bytes(sprite))
    wait_for_vsync()
    spi_sel.off()
    spi.write(bytearray([0]))
    spi.write(sprite_bytes)
    spi_sel.on()

DRINK = [
    [0,0,0,0,0,0,0,1,1,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0],
    [1,1,1,1,0,1,0,1,1,1,1,0],
    [1,0,0,0,0,1,0,0,0,0,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,0,0,1,1,1,0,0,0],
    [0,0,0,1,0,0,1,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0],
]

HEART = [
    [0,0,1,1,0,0,0,1,1,0,0,0],
    [0,1,1,1,1,0,1,1,1,1,0,0],
    [1,1,1,1,1,1,1,1,0,1,1,0],
    [1,1,1,1,1,1,1,1,1,0,1,0],
    [1,1,1,1,1,1,1,1,1,0,1,0],
    [1,1,1,1,1,1,1,1,0,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,0,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,0,0],
]

SPIRAL = [
    [0,0,0,1,1,1,1,1,0,0,0,0],
    [0,1,1,0,0,0,0,0,1,1,0,0],
    [1,0,0,0,0,0,0,0,0,0,1,0],
    [1,0,0,0,0,0,0,0,0,0,1,0],
    [0,0,0,0,1,1,1,1,0,0,0,1],
    [0,0,0,1,0,0,0,0,1,0,0,1],
    [0,0,1,0,0,1,1,0,1,0,0,1],
    [0,0,1,0,1,0,0,0,1,0,0,1],
    [0,0,1,0,1,0,0,1,0,0,1,0],
    [0,0,1,0,0,1,1,0,0,0,1,0],
    [0,0,0,1,0,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,0,0,0,0],
]

def arc_bounce():
    x = 0
    y = 63
    x_vel = 1
    y_vel = -2.5
    while x < 88:
        x += x_vel
        y += y_vel
        y_vel += 5.0/88
        spi_cmd([5, x])
        spi_cmd([6, int(y)], sync=False)
        while vs.value():
            time.sleep_us(100)
    