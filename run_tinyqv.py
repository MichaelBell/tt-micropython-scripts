import time
import sys
import rp2
import machine
import gc
from machine import UART, Pin, PWM, SPI

gc.threshold(10000)

from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard

DemoboardDetect.probe()

from pio_spi import PIOSPI
import flash_prog

@rp2.asm_pio(autopush=True, push_thresh=8, in_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=8, out_shiftdir=rp2.PIO.SHIFT_RIGHT,
             out_init=(rp2.PIO.OUT_HIGH, rp2.PIO.OUT_HIGH, rp2.PIO.IN_HIGH, rp2.PIO.OUT_HIGH,
                       rp2.PIO.IN_HIGH, rp2.PIO.IN_HIGH, rp2.PIO.OUT_HIGH, rp2.PIO.OUT_HIGH),
             sideset_init=(rp2.PIO.OUT_HIGH))
def qspi_read():
    out(x, 8).side(1)
    out(y, 8).side(1)
    out(pindirs, 8).side(1)
    
    label("cmd_loop")
    out(pins, 8).side(0)
    jmp(x_dec, "cmd_loop").side(1)
    
    out(pindirs, 8).side(0)
    label("data_loop")
    in_(pins, 8).side(1)
    jmp(y_dec, "data_loop").side(0)
    
    out(pins, 8).side(1)
    out(pindirs, 8).side(1)

@rp2.asm_pio(autopush=True, push_thresh=32, in_shiftdir=rp2.PIO.SHIFT_RIGHT)
def pio_capture():
    in_(pins, 8)
    
def spi_cmd(spi, data, sel, dummy_len=0, read_len=0):
    dummy_buf = bytearray(dummy_len)
    read_buf = bytearray(read_len)
    
    sel.off()
    spi.write(bytearray(data))
    if dummy_len > 0:
        spi.readinto(dummy_buf)
    if read_len > 0:
        spi.readinto(read_buf)
    sel.on()
    
    return read_buf

def setup_flash():
    spi = PIOSPI(2, Pin(22), Pin(23), Pin(24), freq=10000000)

    flash_sel = Pin(21, Pin.OUT)
    ram_a_sel = Pin(27, Pin.OUT)
    ram_b_sel = Pin(28, Pin.OUT)
    
    flash_sel.on()
    ram_a_sel.on()
    ram_b_sel.on()    
    
    # Leave CM mode if in it
    spi_cmd(spi, [0xFF], flash_sel)
    spi._sm.active(0)
    del spi

    sm = rp2.StateMachine(0, qspi_read, 16_000_000, in_base=Pin(21), out_base=Pin(21), sideset_base=Pin(24))
    sm.active(1)
    
    # Read 1 byte from address 0 to get into continuous read mode
    num_bytes = 4
    buf = bytearray(num_bytes*2 + 4)
    
    sm.put(8+6+2-1)     # Command + Address + Dummy - 1
    sm.put(num_bytes*2 + 4 - 1) # Data + Dummy - 1
    sm.put(0b11111111)  # Directions
    
    # RAM_B_SEL, RAM_A_SEL, SD3, SD2, SCK, SD1, SD0, CS
    sm.put(0b11000010)  # Command
    sm.put(0b11000010)
    sm.put(0b11000010)
    sm.put(0b11000000)
    sm.put(0b11000010)
    sm.put(0b11000000)
    sm.put(0b11000010)
    sm.put(0b11000010)
    
    sm.put(0b11000000)  # Address
    sm.put(0b11000000)
    sm.put(0b11000000)
    sm.put(0b11000000)
    sm.put(0b11000000)
    sm.put(0b11000000)
    sm.put(0b11100100) 
    sm.put(0b11100100)
    
    sm.put(0b11001001)  # Directions
    
    for i in range(num_bytes*2 + 4):
        buf[i] = sm.get()
        if i > 4:
            d = buf[i]
            nibble = ((d >> 1) & 1) | ((d >> 1) & 2) | ((d >> 2) & 0x4) | ((d >> 2) & 0x8)
            print("%01x" % (nibble,), end="")
    print()
        
    sm.put(0b11111111)
    sm.put(0b11001001)  # Directions
    sm.active(0)
    del sm
    
    flash_sel = Pin(21, Pin.OUT)
    ram_a_sel = Pin(27, Pin.OUT)
    ram_b_sel = Pin(28, Pin.OUT)
    
    flash_sel.on()
    ram_a_sel.on()
    ram_b_sel.on()    

def setup_ram():
    spi = PIOSPI(2, Pin(22), Pin(23), Pin(24), freq=10000000)

    flash_sel = Pin(21, Pin.OUT)
    ram_a_sel = Pin(27, Pin.OUT)
    ram_b_sel = Pin(28, Pin.OUT)

    flash_sel.on()
    ram_a_sel.on()
    ram_b_sel.on()
    
    for sel in (ram_a_sel, ram_b_sel):
        spi_cmd(spi, [0x35], sel)
        
    spi._sm.active(0)
    del spi        

def run(query=True, stop=True):
    machine.freq(128_000_000)

    tt = DemoBoard()
    tt.shuttle.tt_um_MichaelBell_tinyQV.enable()

    if query:
        input("Reset? ")

    # Pull up UART RX
    Pin(20, Pin.IN, pull=Pin.PULL_UP)
    
    # All other inputs pulled low
    Pin(9, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(10, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(11, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(12, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(17, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(18, Pin.IN, pull=Pin.PULL_DOWN)
    Pin(19, Pin.IN, pull=Pin.PULL_DOWN)    

    tt.clk.off()
    tt.reset_project(False)
    tt.clock_project_once()
    tt.clock_project_once()
    tt.reset_project(True)
    tt.clk.off()
    
    tt.clk.on()
    time.sleep(0.001)
    tt.clk.off()
    time.sleep(0.001)

    setup_flash()
    setup_ram()    

    flash_sel = Pin(21, Pin.OUT)
    qspi_sd0  = Pin(22, Pin.OUT)
    qspi_sd1  = Pin(23, Pin.OUT)
    qspi_sck  = Pin(24, Pin.OUT)
    qspi_sd2  = Pin(25, Pin.OUT)
    qspi_sd3  = Pin(26, Pin.OUT)
    ram_a_sel = Pin(27, Pin.OUT)
    ram_b_sel = Pin(28, Pin.OUT)

    qspi_sck.off()
    flash_sel.off()
    ram_a_sel.off()
    ram_b_sel.off()
    qspi_sd0.off()
    qspi_sd1.on()
    qspi_sd2.off()
    qspi_sd3.off()

    for i in range(10):
        tt.clk.off()
        time.sleep(0.001)
        tt.clk.on()
        time.sleep(0.001)

    Pin(21, Pin.IN, pull=Pin.PULL_UP)
    Pin(22, Pin.IN, pull=None)
    Pin(23, Pin.IN, pull=None)
    Pin(24, Pin.IN, pull=None)
    Pin(25, Pin.IN, pull=None)
    Pin(26, Pin.IN, pull=None)
    Pin(27, Pin.IN, pull=Pin.PULL_UP)
    Pin(28, Pin.IN, pull=Pin.PULL_UP)
    
    for i in range(21, 29):
        print(f"{machine.mem32[0x40014004+i*8]:08x}")
    print(f"{machine.mem32[0xd0000004]:08x}")

    tt.reset_project(False)
    time.sleep(0.001)
    tt.clk.off()

    sm = rp2.StateMachine(1, pio_capture, 128_000_000, in_base=Pin(21))

    capture_len=1024
    buf = bytearray(capture_len)

    rx_dma = rp2.DMA()
    c = rx_dma.pack_ctrl(inc_read=False, treq_sel=5) # Read using the SM0 RX DREQ
    sm.restart()
    sm.exec("wait(%d, gpio, %d)" % (1, 24))
    rx_dma.config(
        read=0x5020_0024,        # Read from the SM1 RX FIFO
        write=buf,
        ctrl=c,
        count=capture_len//4,
        trigger=True
    )
    sm.active(1)

    if query:
        input("Start? ")

    #uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    time.sleep(0.001)
    tt.clock_project_PWM(64_000_000)

    # Wait for DMA to complete
    while rx_dma.active():
        time.sleep_ms(1)
        
    sm.active(0)
    del sm

    if not stop:
        return

    if query:
        input("Stop? ")

    tt.reset_project(True)
    tt.clock_project_stop()

    if False:
        while True:
            data = uart.read(16)
            if data is not None:
                for d in data:
                    if d > 0 and d <= 127:
                        print(chr(d), end="")

        for i in range(len(buf)):
            print("%02x " % (buf[i],), end = "")
            if (i & 7) == 7:
                print()

    if True:
        for j in range(8):
            print("%02d: " % (j+21,), end="")
            for d in buf:
                print("-" if (d & (1 << j)) != 0 else "_", end = "")
            print()

        print("SD: ", end="")
        for d in buf:
            nibble = ((d >> 1) & 1) | ((d >> 1) & 2) | ((d >> 2) & 0x4) | ((d >> 2) & 0x8)
            print("%01x" % (nibble,), end="")
        print()

def execute(filename):
    flash_prog.program(filename)
    run(query=False, stop=False)
