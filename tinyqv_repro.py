import gc
gc.threshold(50000)
import rp2
from time import sleep_us

import machine
from machine import Pin

from ttboard.demoboard import DemoBoard, DemoboardDetect
from ttboard.mode import RPMode


DemoboardDetect.probe()

@rp2.asm_pio(autopush=True, push_thresh=8, in_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=8, out_shiftdir=rp2.PIO.SHIFT_RIGHT,
             out_init=(rp2.PIO.IN_HIGH, rp2.PIO.IN_LOW, rp2.PIO.IN_HIGH, rp2.PIO.IN_LOW,
                       rp2.PIO.IN_LOW, rp2.PIO.IN_LOW, rp2.PIO.IN_HIGH, rp2.PIO.IN_HIGH))
def qspi_send():
    out(x, 8)
    out(y, 8)
    out(pindirs, 8)
    
    wait(0, gpio, 21)  # Wait for selection
    wait(1, gpio, 24)  # Wait for clock rising edge
    
    label("cmd_loop")  # Wait for x+1 clocks
    nop().delay(2)
    jmp(x_dec, "cmd_loop")
    
    out(pindirs, 8).delay(1)  # Set pindirs, wait another clock
    
    label("data_loop")   # Send y+1 nibbles of data
    out(pins, 8).delay(2)
    jmp(y_dec, "data_loop")
    
    out(pindirs, 8)
    
tt = DemoBoard()
tt.shuttle.tt_um_MichaelBell_tinyQV.enable()
tt.clock_project_once()

machine.freq(128_000_000)

dma = rp2.DMA()

data = bytearray(18)
data[0] = 9 # 12 clocks for address and dummy cycles
data[1] = 11 # 12 nybbles data
data[2] = 0  # All inputs

data[3] = 0b110110 # data pins to outputs

# 6f00600a6f00
data[4]  = 0b010100
data[5]  = 0b110110
data[6]  = 0
data[7]  = 0
data[8]  = 0b010100
data[9]  = 0
data[10] = 0
data[11] = 0b100100
data[12] = 0b010100
data[13] = 0b110110
data[14] = 0
data[15] = 0
data[16] = 0

data[17] = 0 # All inputs

while True:
    sm = rp2.StateMachine(0, qspi_send, 128_000_000, out_base=Pin(21))

    tt.clock_project_once()
    tt.reset_project(True)
    tt.clock_project_once(10)

    sm.active(1)
    dma.config(
        read = data,
        write = sm,
        count = len(data),
        ctrl = dma.pack_ctrl(
            size      = 0,  # 0 = byte, 1 = half word, 2 = word
            irq_quiet = True,
            inc_read = True,
            inc_write = False,
            bswap     = False,
            treq_sel = 0 # SM0 TX DREQ
        ),
        trigger = True
    )

    #input("Start? ")

    tt.clk(1)
    tt.reset_project(False)
    tt.clock_project_PWM(64000000)
    sleep_us(10)

    #input("Repeat? ")
