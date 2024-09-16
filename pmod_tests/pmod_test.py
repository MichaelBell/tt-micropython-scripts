import qspi_test
import audio_test
import display
from machine import Pin
from time import sleep_ms

rst = Pin(3, Pin.IN)
clk = Pin(0, Pin.IN)

# Disable RAM B test for audio Pmod testing
qspi_test.TEST_RAM_B = False

display.clear()

while True:
    if rst.value() == 0:
        display.clear()
        display.led_segs[7].on()
        qspi_test.run_test()
        sleep_ms(500)
    if clk.value() == 1:
        display.clear()
        display.led_segs[7].on()
        audio_test.run_test()
        display.clear()
    sleep_ms(100)

    