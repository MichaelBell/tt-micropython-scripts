import random
import struct

import machine
from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard

from machine import Pin
from rp2 import PIO, StateMachine, asm_pio

from encdec8b10b import EncDec8B10B

# Enable powman
machine.mem32[0x40100004] = 0x5AFEA050

# 1.3V
machine.mem32[0x4010000c] = 0x5AFE00f0  # c0 = 1.15V, d0 = 1.2V, etc


@asm_pio(sideset_init=PIO.OUT_LOW, autopull=True, pull_thresh=20, out_shiftdir=PIO.SHIFT_RIGHT,
         in_shiftdir=PIO.SHIFT_LEFT, push_thresh=16, autopush=True,
         out_init=(PIO.OUT_LOW,)*2)
def enc_prog():
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    nop()          .side(1)
    out(pins, 2)   .side(0)
    in_(pins, 16)  .side(1)

DATA_LEN = 4096

a_vals = [random.randint(0, 255) for _ in range(DATA_LEN)]
b_vals = [random.randint(0, 255) for _ in range(DATA_LEN)]

def encode(a_vals, b_vals):
    enc = bytearray(DATA_LEN*4)
    disp_a, disp_b = 0, 0
    
    for i in range(DATA_LEN):
        disp_a, enc_val_a = EncDec8B10B.enc_8b10b(a_vals[i], disp_a)
        disp_b, enc_val_b = EncDec8B10B.enc_8b10b(b_vals[i], disp_b)
        enc_val = 0
        enc_val_b <<= 1
        for j in range(10):
            enc_val |= ((enc_val_a & 1) | (enc_val_b & 2)) << (j * 2)
            enc_val_a >>= 1
            enc_val_b >>= 1
        #enc.append(enc_val)
        enc_bytes = struct.pack("<I", enc_val)
        enc[i*4] = enc_bytes[0]
        enc[i*4 + 1] = enc_bytes[1]
        enc[i*4 + 2] = enc_bytes[2]
        enc[i*4 + 3] = enc_bytes[3]

    return enc

enc = encode(a_vals, b_vals)

DemoboardDetect.probe()            
tt = DemoBoard.get()
tt.shuttle.tt_um_MichaelBell_hs_mul.enable()
tt.clock_project_stop()

machine.freq(400000000)

tt.reset_project(True)
tt.clock_project_once()
tt.clock_project_once()
tt.reset_project(False)

for _ in range(15):
    tt.clock_project_once()

PIO(0).gpio_base(16)
sm = StateMachine(0, enc_prog, out_base=Pin(17), sideset_base=Pin(16), in_base=Pin(25))
sm.active(1)
sm.put(0b00110011111111110000)
sm.get()

if False:
    for i in range(DATA_LEN):
        a = a_enc[i]
        b = b_enc[i]
        for j in range(10):
            tt.ui_in.value = (a & 1) | ((b << 1) & 2) | 0x84
            a >>= 1
            b >>= 1
            tt.clock_project_once()
            
            if j == 0:
                if i == 0:
                    assert tt.uo_out.value == 5
                else:
                    assert tt.uo_out.value == 0xf
                    tt.ui_in.value = 0xc0
                    assert tt.uo_out.value == a_vals[i-1]
                    assert tt.uio_out.value == b_vals[i-1]

if False:
    tt.ui_in.value = 0xc0
    for i in range(DATA_LEN):
        sm.put(enc[i])
        val = sm.get()
        if i != 0:
            assert val >> 8 == a_vals[i-1]
            assert val & 0xFF == b_vals[i-1]

# Test value decode
tt.ui_in.value = 0xc0

# Setup the DMA
rx_dma = rp2.DMA()
c = rx_dma.pack_ctrl(inc_read=False, treq_sel=4, size=1) # Read using the SM0 RX DREQ
rx_dma.config(
    read=sm,        # Read from the SM0 RX FIFO
    ctrl=c,
    trigger=False
)

tx_dma = rp2.DMA()
c = tx_dma.pack_ctrl(inc_write=False, treq_sel=0) # Read using the SM0 TX DREQ
tx_dma.config(
    write=sm,  # Write to the SM0 RX FIFO
    ctrl=c,
    trigger=False
)

dst_data = bytearray(DATA_LEN * 2)
rx_dma.config(write=dst_data, count=DATA_LEN, trigger=True)
tx_dma.config(read=enc, count=DATA_LEN, trigger=True)

for i in range(1, DATA_LEN):
    assert dst_data[i*2] == b_vals[i-1]
    assert dst_data[i*2+1] == a_vals[i-1]


# Test multiplier
tt.ui_in.value = 0x88

# Setup the DMA
rx_dma = rp2.DMA()
c = rx_dma.pack_ctrl(inc_read=False, treq_sel=4, size=1) # Read using the SM0 RX DREQ
rx_dma.config(
    read=sm,        # Read from the SM0 RX FIFO
    ctrl=c,
    trigger=False
)

tx_dma = rp2.DMA()
c = tx_dma.pack_ctrl(inc_write=False, treq_sel=0) # Read using the SM0 TX DREQ
tx_dma.config(
    write=sm,  # Write to the SM0 RX FIFO
    ctrl=c,
    trigger=False
)

dst_data = bytearray(DATA_LEN * 2)
rx_dma.config(write=dst_data, count=DATA_LEN, trigger=True)
tx_dma.config(read=enc, count=DATA_LEN, trigger=True)

for i in range(1, DATA_LEN):
    res = b_vals[i-1] * a_vals[i-1]
    assert dst_data[i*2] == res >> 8
    assert dst_data[i*2+1] == res & 0xFF

