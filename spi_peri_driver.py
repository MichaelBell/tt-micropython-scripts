import time
import machine
from machine import SPI, Pin

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

from pio_spi import PIOSPI

tt = DemoBoard()
tt.shuttle.tt_um_MichaelBell_spi_peri.enable()

CMD_WRITE = 0x02
CMD_READ = 0x03

if tt.pins.mode == RPMode.ASIC_RP_CONTROL:
    spi_sel = Pin(10, Pin.OUT)
    spi_sel.on()
    spi = PIOSPI(1, Pin(21), Pin(22), Pin(9), freq=1000000)

def spi_cmd(data, dummy_len=0, read_len=0):
    dummy_buf = bytearray(dummy_len)
    read_buf = bytearray(read_len)
    
    spi_sel.off()
    spi.write(bytearray(data))
    if dummy_len > 0:
        spi.readinto(dummy_buf)
    if read_len > 0:
        spi.readinto(read_buf)
    spi_sel.on()
    
    return read_buf

def spi_cmd2(data, data2):
    spi_sel.off()
    spi.write(bytearray(data))
    spi.write(data2)
    spi_sel.on()

def print_bytes(data):
    for b in data: print("%02x " % (b,), end="")
    print()

def test_write(addr, val):
    spi_cmd([CMD_WRITE, addr >> 16, (addr >> 8) & 0xFF, addr & 0xFF, val & 0xFF])

def test_read(addr, length):
    return spi_cmd([CMD_READ, addr >> 16, (addr >> 8) & 0xFF, addr & 0xFF], 0, length)

def numbers_test(addr):
    print(f"{addr:x}")
    tt.in2(0)
    tt.in3(addr & 1)
    tt.in4((addr & 2) != 0)
    tt.in5((addr & 4) != 0)
    for i in range(16):
        test_write(addr, i)
        tt.clock_project_once()
        time.sleep_ms(100)
    tt.in2(1)
    for i in range(16):
        test_write(addr, i*16)
        tt.clock_project_once()
        time.sleep_ms(100)

def test_random():
    bins = [0]*256
    for i in range(10000):
        data = test_read(0x400, 1)
        for byte in data:
            bins[int(byte)] += 1
    for i in range(0, 256, 16):
        for j in range(i, i+16):
            print(f"{bins[j]:04d} ", end="")
        print()

if tt.pins.mode == RPMode.ASIC_RP_CONTROL:
    numbers_test(0x100)
    if False:
        numbers_test(0x101)
        numbers_test(0x102)
        numbers_test(0x103)
        numbers_test(0x104)
        numbers_test(0x105)
        numbers_test(0x106)
        numbers_test(0x107)
    test_random()

