# Clock speed test, Michael Bell
# This test clocks the tt_um_test design at a high frequency
# and checks the counter has incremented by the correct amount
# 

import machine
import rp2
import time

from ttboard.mode import RPMode
from ttboard.demoboard import DemoBoard

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
tt.shuttle.tt_um_factory_test.enable()
tt.in0(1)
tt.clock_project_stop()

# Setup the PIO clock driver
sm = rp2.StateMachine(0, clock_prog, sideset_base=machine.Pin(0))
sm.active(1)

# Higher core voltage
machine.mem32[0x40064000] = 0xf1  # c1 = 1.15V, d1 = 1.2V, etc

# Drive strength on the clock
machine.mem32[0x4001c004] = 0x56  # 66 = 8mA, 56 = 4mA

def run_test(freq, fast=False):
    # Multiply requested project clock frequency by 2 to get RP2040 clock
    freq *= 2
    
    #if freq > 400_000_000:
    #    raise ValueError("Too high a frequency requested")
    
    machine.freq(freq)
    time.sleep_ms(2)

    try:
        # Run 1 clock
        print(f"Clock test, start at {tt.output_byte}... ", end ="")
        start_val = tt.output_byte
        sm.put(0)
        sm.get()
        print(f" done. Value: {tt.output_byte}")
        #if tt.output_byte != ((start_val + 1) & 0xFF):
        #    return 1
    
        errors = 0
        if False:
            for _ in range(100):
                start_val = tt.output_byte
                sm.put(0)
                sm.get()
                if tt.output_byte != ((start_val + 1) & 0xFF):
                    errors += 1
            return errors

        for _ in range(10):
            last = tt.output_byte
            
            # Run clock for approx 0.25 or 1 second, sending a multiple of 256 clocks plus 1.
            clocks = (freq // 2048) * 256 if fast else (freq // 512) * 256
            t = time.ticks_us()
            sm.put(clocks + 1)
            sm.get()
            t = time.ticks_us() - t
            print(f"Clocked for {t}us: ", end = "")
                
            # Check the counter has incremented by 2 (or 1).
            if tt.output_byte != (last + 2) & 0xFF and tt.output_byte != (last + 1) & 0xFF:
                print("Error: ", end="")
                errors += 1
            print(tt.output_byte)
            
            if not fast:
                # Sleep so the 7-seg display can be read
                time.sleep(0.5)
    finally:
        if freq > 133_000_000:
            machine.freq(133_000_000)
        
    return errors

if __name__ == "__main__":
    freq = 140_000_000
    while True:
        print(f"\nRun at {freq/1000000}MHz project clock\n")
        errors = run_test(freq, True)
        print(errors)
        if errors > 0: break
        freq += 2_000_000