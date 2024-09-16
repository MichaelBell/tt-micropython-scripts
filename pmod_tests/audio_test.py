import time
import machine
import gc
import random
from machine import PWM, Pin

# Set this to flase if no TT carrier is mounted on the demoboard
DISABLE_TT_ASIC = False

if DISABLE_TT_ASIC:
    from ttboard.mode import RPMode
    from ttboard.demoboard import DemoBoard
    
def disable_tt_board():
    if DISABLE_TT_ASIC:
        # Select the chip ROM, which should always be present and set the bidirs to all inputs
        # so we can drive them with SPI
        tt = DemoBoard()
        tt.shuttle.tt_um_chip_rom.enable()
        
def play_audio():
    pwm = PWM(Pin(28), freq = 700, duty_u16=32768)
    time.sleep(1)
    
    def freq_note(m):
        return 440*2**((m-69)/12)
    
    for i in range(36, 85):
        pwm.freq(int(freq_note(i)))
        time.sleep(0.1)
    for i in range(84, 35, -1):
        pwm.freq(int(freq_note(i)))
        time.sleep(0.1)

    time.sleep(0.3)
    pwm.deinit()

def run_test():
    disable_tt_board()
    play_audio()
