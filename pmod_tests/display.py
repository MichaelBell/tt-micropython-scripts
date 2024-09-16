from machine import Pin
from time import sleep_ms

mux_sel = Pin(1, Pin.OUT)
mux_sel.on()
led_segs = [Pin(5, Pin.OUT), Pin(6, Pin.OUT), Pin(7, Pin.OUT), Pin(8, Pin.OUT),
            Pin(13, Pin.OUT), Pin(14, Pin.OUT), Pin(15, Pin.OUT), Pin(16, Pin.OUT)]

def clear():
    for led in led_segs:
        led.off()

pass_text = [[1, 1, 0, 0, 1, 1, 1, 0], [1, 1, 1, 0, 1, 1, 1, 0], [1, 0, 1, 1, 0, 1, 1, 0], [1, 0, 1, 1, 0, 1, 1, 1]]
fail_text = [[1, 0, 0, 0, 1, 1, 1, 0], [1, 1, 1, 0, 1, 1, 1, 0], [0, 1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 1, 1, 0, 1]]

def display_text(text, reps):
    for r in range(reps):
        for char in text:
            for i in range(8):
                led_segs[i].value(char[i])
            sleep_ms(250)
        sleep_ms(250)

def display_pass(reps = 3):
    display_text(pass_text, reps)
    
def display_fail(reps = 3):
    display_text(fail_text, reps)
