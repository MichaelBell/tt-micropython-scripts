import time
import gc
gc.threshold(10000)

from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard

DemoboardDetect.probe()
tt = DemoBoard()
tt.shuttle.tt_um_MichaelBell_tinyQV.enable()

def reset(dut, latency=1, ui_in=0x80):
  # Reset
  #dut._log.info(f"Reset, latency {latency}")
  dut.ui_in.value = ui_in
  dut.uio_in.value = 0
  dut.reset_project(False)
  time.sleep(0.1)
  dut.clock_project_once()
  time.sleep(0.1)
  dut.clock_project_once()
  time.sleep(0.1)
  dut.reset_project(True)
  time.sleep(0.1)
  dut.uio_in.value = latency << 1 # TODO
  dut.clock_project_once()
  time.sleep(0.1)
  dut.uio_oe_pico.value = 0xff
  time.sleep(0.1)
  for i in range(10):
      dut.clock_project_once()
  dut.uio_oe_pico.value = 0
  time.sleep(0.1)
  dut.reset_project(False)

