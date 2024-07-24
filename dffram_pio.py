# Speed test for the DFFRAM project.
import random

from ttboard.pins import Pins
from ttboard.demoboard import DemoBoard
import ttboard.util.time as time

from machine import Pin
from rp2 import PIO, StateMachine, asm_pio

machine.freq(133_000_000)

tt = DemoBoard(apply_user_config=False)
tt.shuttle.tt_um_urish_dffram.enable()

tt.reset_project(True)
tt.clock_project_PWM(1000000)
time.sleep_ms(1)

tt.reset_project(False)
time.sleep_ms(1)
tt.clock_project_stop()

# This PIO program writes to the PIO in the following sequence:
# - Set clock low
# - Set clock high
# - Set address, wen and data inputs
# - Wait 1 clock
#
# The DFFRAM only expects inputs to be changed while clock is high, and requires
# some setup time before the falling clock edge.  The above sequence has experimentally
# been found to allow a fairly high clock rate (up to 80MHz on my hardware).
#
# The PIO correctly aligns a 16-bit write to the input and bidir pins, so the
# calling code doesn't have to worry about unpacking the inputs to match the pinout.
@asm_pio(sideset_init=PIO.OUT_LOW, autopull=True, pull_thresh=32, out_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_TX,
         in_shiftdir=PIO.SHIFT_LEFT,
         out_init=(PIO.OUT_LOW,)*4 + (PIO.IN_LOW,)*4 + (PIO.OUT_LOW,)*12)
def dffram_prog():
    out(isr, 16)         .side(0)
    in_(isr, 4)          .side(1)
    mov(pins, isr)       .side(1).delay(1)

# This PIO program waits for the first rising clock edge and then reads the DFFRAM outputs
# once every project clock.  For different frequencies the initial delay may need to be tuned
# to sample the output at the best time:
# ~25MHz: 6
# ~35MHz: 7
# ~50MHz: 8
# ~60MHz: 9
# ~70MHz: 10
# >80MHz: 11
@rp2.asm_pio(autopush=True, push_thresh=32, in_shiftdir=PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_RX)
def read_prog():
    wait(1, gpio, 0).delay(8)
    wrap_target()
    in_(pins, 16).delay(3)
    wrap()

# Create the PIO state machines
sm = StateMachine(0, dffram_prog, out_base=Pin(9), sideset_base=Pin(0), in_base=Pin(5))
sm.active(1)

sm_rx = StateMachine(1, read_prog, in_base=Pin(5))

# Buffers for DMA to/from the PIO
RAM_LEN = 128
src_data = bytearray(RAM_LEN*64+4)
dst_data = bytearray(RAM_LEN*64)

# Setup the DMA
rx_dma = rp2.DMA()
c = rx_dma.pack_ctrl(inc_read=False, treq_sel=5) # Read using the SM1 RX DREQ
rx_dma.config(
    read=0x5020_0024,        # Read from the SM1 RX FIFO
    ctrl=c,
    trigger=False
)

tx_dma = rp2.DMA()
c = tx_dma.pack_ctrl(inc_write=False, treq_sel=0) # Read using the SM0 TX DREQ
tx_dma.config(
    write=0x5020_0010,  # Write to the SM0 RX FIFO
    ctrl=c,
    trigger=False
)

def restart_rx():
    sm_rx.active(0)
    while sm_rx.rx_fifo() > 0: sm_rx.get()
    sm_rx.restart()
    sm_rx.active(1)

def linear_test():
    offset = random.randint(0, 127)
    
    print(f"Linear write and read back test, using data = addr + {offset}")

    # Setup writes to each memory location in the DMA buffer
    for i in range(RAM_LEN):
        src_data[i*2] = i + 0x80        # Address, wen
        src_data[i*2 + 1] = i + offset # Data
        
    # And read back all the written values
    for i in range(RAM_LEN):
        src_data[RAM_LEN*2 + i*2] = i
        src_data[RAM_LEN*2 + i*2+1] = 0

    # Write one more value so the final clock cycle happens
    src_data[RAM_LEN*4] = RAM_LEN-1
    src_data[RAM_LEN*4+1] = 0
    src_data[RAM_LEN*4+2] = RAM_LEN-1
    src_data[RAM_LEN*4+3] = 0

    # Kick off the writes and reads
    restart_rx()
    rx_dma.config(write=dst_data, count=(RAM_LEN*4)//4, trigger=True)
    tx_dma.config(read=src_data, count=(RAM_LEN*4)//4+1, trigger=True)
    
    # Wait for DMA to complete
    while rx_dma.active():
        time.sleep_ms(1)
        
    # Verify all the read values match what was written
    for i in range(RAM_LEN):
        addr = i
        val = (dst_data[RAM_LEN*2+i*2+0] & 0xF) | ((dst_data[RAM_LEN*2+i*2 + 1] << 4) & 0xF0)
        expected = addr + offset
        if val != expected:
            print(f"Error, at {addr} read {val}, expected {expected}")
    print("Done")

def random_test(runs):
    print("Clearing RAM")
    
    # Setup DMA to clear the RAM
    for i in range(RAM_LEN):
        src_data[i*2] = i + 0x80       # Address, wen
        src_data[i*2 + 1] = 0          # Data
    
    for i in range(RAM_LEN):
        src_data[RAM_LEN*2 + i*4] = i
        src_data[RAM_LEN*2 + i*4+1] = 0
        src_data[RAM_LEN*2 + i*4+2] = i
        src_data[RAM_LEN*2 + i*4+3] = 0
    
    restart_rx()
    rx_dma.config(write=dst_data, count=(RAM_LEN*6)//4, trigger=True)
    tx_dma.config(read=src_data, count=(RAM_LEN*6)//4, trigger=True)

    for i in range(RAM_LEN):
        val = (dst_data[RAM_LEN*2 + i*4+2] & 0xF) | ((dst_data[RAM_LEN*2 + i*4+3] << 4) & 0xF0)
        if val != 0:
            print("Clear failed")
            return 1

    mhz = machine.freq() // 4_000_000
    print(f"Starting {runs} runs of random reads and writes at {mhz}MHz")
    
    ram = [0,] * RAM_LEN
    errors = 0
    
    for r in range(runs):
        # Setup DMA to perform a random sequence of reads and writes
        for i in range(len(dst_data) // 4):
            if random.randint(0, 1) == 1:
                # Two writes
                addr = random.randint(0, RAM_LEN-1)
                val = random.randint(0, 255)
                src_data[i*4 + 0] = addr + 0x80       # Address, wen
                src_data[i*4 + 1] = val               # Data
                
                addr = random.randint(0, RAM_LEN-1)
                val = random.randint(0, 255)
                src_data[i*4 + 2] = addr + 0x80       # Address, wen
                src_data[i*4 + 3] = val               # Data

            else:
                # Read - at high clock rates the outputs can't toggle fast enough
                # for the output to be reliable, so keep the address stable over two clocks
                addr = random.randint(0, RAM_LEN-1)
                src_data[i*4 + 0] = addr
                src_data[i*4 + 1] = 0
                src_data[i*4 + 2] = addr
                src_data[i*4 + 3] = 0
            
        # Cycle the clock one more time
        src_data[len(dst_data)] = 0
        src_data[len(dst_data)+1] = 0
        src_data[len(dst_data)+2] = 0
        src_data[len(dst_data)+3] = 0
    
        # Kick off the DMA transfers
        restart_rx()
        rx_dma.config(write=dst_data, count=len(dst_data)//4, trigger=True)
        tx_dma.config(read=src_data, count=len(src_data)//4+1, trigger=True)
        
        while rx_dma.active():
            time.sleep_ms(1)

        # Spin through the data we sent, tracking what the RAM contents should be
        # due to writes, and verifying that is what was read back on reads.
        for i in range(len(dst_data) // 4):
            addr = src_data[i*4] & 0x7F
            write = (src_data[i*4] & 0x80) != 0
            if write:
                ram[addr] = src_data[i*4+1]
                addr = src_data[i*4+2] & 0x7F
                ram[addr] = src_data[i*4+3]

            else:
                addr = src_data[i*4+2]
                val = (dst_data[i*4+2] & 0xF) | ((dst_data[i*4 + 3] << 4) & 0xF0)
                expected = ram[addr]
                if val != expected:
                    print(f"Error, at {addr} read {val}, expected {expected}")
                    errors += 1
        
        print(f"{r+1}/{runs}", end = '\r')
        
        if errors > 3*(r+1):
            print("Too many errors")
            return errors

    if errors == 0:
        print("All passed")
    else:
        print(f"{errors} errors")
    
    return 0

def test_freq_range(start_freq, end_freq=266_000_000, freq_step = 4_000_000, runs=20):
    try:
        # Ramp up the frequency until the tests fail
        next_freq = start_freq
        
        while next_freq <= end_freq:
            machine.freq(next_freq)
            
            if random_test(runs) != 0:
                break
            
            next_freq += freq_step

    finally:
        # Reset RP2040 frequency to a more normal range
        machine.freq(133_000_000)

if __name__ == "__main__":
    project_freq = 50_000_000
    test_freq_range(project_freq * 4)
    
    #project_freq = 70_000_000
    #test_freq_range(project_freq * 4, end_freq = 340_000_000)