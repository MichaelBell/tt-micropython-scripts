# Clock speed test, Michael Bell
# This test clocks the tt_um_test design at a high frequency
# and checks the counter has incremented by the correct amount
# 

import machine
import rp2
import time

from ttboard.mode import RPMode
from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard

DemoboardDetect.probe()

# PIO program to drive the clock.  Put a value n and it clocks n+1 times
# Reads 0 when done.
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32, autopush=True, push_thresh=32)
def clock_prog():
    out(x, 32)              .side(0)
    label("clock_loop")
    nop()                   .side(1)
    jmp(x_dec, "clock_loop").side(0)
    in_(null, 32)           .side(0)

# Select design, don't apply config so the PWM doesn't start.
tt = DemoBoard()
tt.shuttle.tt_um_rebelmike_incrementer.enable()
tt.ui_in.value = 1
tt.clock_project_stop()

# Setup the PIO clock driver
sm = rp2.StateMachine(0, clock_prog, sideset_base=machine.Pin(16))
sm.active(1)

# Enable powman
machine.mem32[0x40100004] = 0x5AFEA050

# 1.3V
machine.mem32[0x4010000c] = 0x5AFE00f0  # c0 = 1.15V, d0 = 1.2V, etc

# 8mA drive strength on the clock pin
#machine.mem32[0x40038044] = 0x66    # 56 = 4mA, 66 = 8mA, 76 = 12mA

def read_count():
    return tt.uo_out.value.to_unsigned() + ((tt.uio_out.value.to_unsigned()) << 8)

def run_test(freq, fast=False):
    # Multiply requested project clock frequency by 2 to get RP2040 clock
    freq *= 2
    
    if freq > 420_000_000:
        raise ValueError("Too high a frequency requested")
    
    machine.freq(freq)
    time.sleep_ms(2)

    try:
        # Run 1 clock
        print(f"Clock test, start at {read_count()}... ", end ="")
        start_val = read_count()
        sm.put(0)
        sm.get()
        print(f" done. Value: {read_count()}")
        #if tt.uo_out.value != ((start_val + 1) & 0xFF):
        #    return 1
    
        errors = 0
        if False:
            for _ in range(100):
                start_val = read_count()
                sm.put(0)
                sm.get()
                if read_count() != ((start_val + 1) & 0xFFFF):
                    errors += 1
            return errors

        for _ in range(10):
            last = read_count()
            
            # Run clock for approx 0.25 or 1 second, sending a multiple of 65536 clocks plus some.
            clocks = (freq // (2048 * 256)) * 65536 if fast else (freq // (512 * 256)) * 65536
            t = time.ticks_us()
            sm.put(clocks + 0x1116)
            sm.get()
            t = time.ticks_us() - t
            print(f"Clocked for {t}us: ", end = "")
                
            # Check the counter has incremented by the correct amount
            if read_count() != (last + 0x1117) & 0xFFFF:
                print(f"Error: {read_count()}, differs by {(read_count() - (last + 0x1117)) & 0xFFFF}")
                errors += 1
            else:
                print(read_count())
            
            if not fast:
                # Sleep so the 7-seg display can be read
                time.sleep(0.5)
    finally:
        if freq > 133_000_000:
            machine.freq(133_000_000)
        
    return errors

if __name__ == "__main__":
    freq = 198_000_000
    while True:
        print(f"\nRun at {freq/1000000}MHz project clock\n")
        errors = run_test(freq, True)
        print(errors)
        if errors > 0: break
        freq += 2_000_000