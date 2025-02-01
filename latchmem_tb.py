import gc
gc.threshold(50000)
import random
from time import sleep_ms

from ttboard.demoboard import DemoBoard, DemoboardDetect
from ttboard.mode import RPMode
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.time.value import TimeValue
import microcotb as cocotb
from microcotb.utils import get_sim_time
gc.collect()
gc.threshold(-1)

DemoboardDetect.probe()

cocotb.set_runner_scope(__name__)

async def fast_write(dut, addr, val, reset_wr_en = True):
  dut.addr.value = addr
  dut.data_in.value = val
  dut.wr_en.value = 1
  await ClockCycles(dut.clk, 1)
  if reset_wr_en:
    dut.wr_en.value = 0
  dut.addr.value = random.randint(0, 63)
  dut.data_in.value = random.randint(0, 255)

async def write(dut, addr, val, reset_wr_en = True, hold_address = False):
  await fast_write(dut, addr, val, reset_wr_en)
  if hold_address:
    dut.addr.value = addr
  await ClockCycles(dut.clk, 1)

async def read(dut, addr):
  # Not setting wr_en low because the cycle immedately after a write
  # is always a read regardless of wr_en
  dut.addr.value = addr
  await ClockCycles(dut.clk, 1)

  # Now setting wr_en low
  dut.wr_en.value = 0
  dut.addr.value = random.randint(0, 63)
  #await Timer(5, "ns")
  return dut.data_out.value

async def reset(dut):
  dut._log.info("Reset")
  await ClockCycles(dut.clk, 1)
  
  # Bidi IOs all used as inputs
  #assert dut.uio_out.value == 0
  #assert dut.uio_oe.value == 0

  # Reset
  dut.rst_n.value = 0
  await ClockCycles(dut.clk, 2)
  dut.rst_n.value = 1

@cocotb.test()
async def test_basic(dut):
  dut._log.info("Start")

  clock = Clock(dut.clk, 20, units="ns")
  cocotb.start_soon(clock.start())

  await reset(dut)
  
  dut._log.info("Write one")
  await write(dut, 0, 0xa5, hold_address=True)
  #await Timer(5, "ns")
  assert dut.data_out.value == 0xa5
  await fast_write(dut, 0, 0x11)
  assert dut.data_out.value == 0xa5
  #await Timer(5, "ns")
  assert dut.data_out.value == 0xa5, f"{dut.data_out.value} != 0xa5 {dut.clk.value}"
  dut.addr.value = 0
  await ClockCycles(dut.clk, 1)
  #await Timer(5, "ns")
  assert dut.data_out.value == 0x11


@cocotb.test()
async def test_all(dut):
  dut._log.info("Start")

  clock = Clock(dut.clk, 20, units="ns")
  cocotb.start_soon(clock.start())
  
  await reset(dut)
  
  dut._log.info("Write all locations")
  for i in range(64):
    await write(dut, i, i+5, hold_address=True)
    #await Timer(5, "ns")
    assert dut.data_out.value == i + 5

  dut._log.info("Read back")
  for i in range(64):
    assert await read(dut, i) == i + 5, f"Read {dut.data_out.value}, expected {i + 5}"

  dut._log.info("Write all locations, no wr_en reset")
  for i in range(64):
    await write(dut, i, i+15, False, True)
    #await Timer(5, "ns")
    assert dut.data_out.value == i + 15 

  dut._log.info("Read back")
  for i in range(64):
    assert await read(dut, i) == i + 15


@cocotb.test()
async def test_random(dut):
  dut._log.info("Start")

  clock = Clock(dut.clk, 20, units="ns")
  cocotb.start_soon(clock.start())
  
  await reset(dut)
  
  dut._log.info("Fill memory")
  state = []
  for i in range(64):
    val = random.randint(0, 255)
    await write(dut, i, val, False)
    state.append(val)

  dut._log.info("Random reads and writes")
  last_action = 1
  dut.wr_en.value = 0
  for i in range(1000):
    addr = random.randint(0, 63)
    
    if random.randint(0, 1) == 0:
      if last_action == 0:
        await ClockCycles(dut.clk, 1)
      # Write
      val = random.randint(0, 255)
      await fast_write(dut, addr, val, False)
      #await Timer(5, "ns")
      assert dut.data_out.value == state[addr]
      state[addr] = val
      last_action = 0
    
    else:
      # Read
      assert await read(dut, addr) == state[addr]
      last_action = 1
      
gc.collect()
gc.threshold(100000)

#def main():
if True:
    import ttboard.cocotb.dut
    
    class DUT(ttboard.cocotb.dut.DUT):
        def __init__(self):
            super().__init__('LatchMem')
            self.tt = DemoBoard.get()
            
            self.add_slice_attribute('addr', self.tt.ui_in, 5, 0) 
            self.add_bit_attribute('wr_en', self.tt.ui_in, 7)
            self.add_slice_attribute('data_in', self.tt.uio_in, 7, 0) 
            self.add_slice_attribute('data_out', self.tt.uo_out, 7, 0)

    tt = DemoBoard.get()
    
    # Use reset_and_clock_mux to select the project as this project has a bug
    # which causes internal contention until the first clock, so we want the
    # clock running fast while it is selected, and to ignore the danger level set on it.
    tt.clock_project_PWM(66000000)
    tt.shuttle.reset_and_clock_mux(620)
    sleep_ms(1)
    tt.clock_project_once()
    
    tt.mode = RPMode.ASIC_RP_CONTROL
        
    tt.uio_oe_pico.value = 0xff # all outputs
    
    
    TimeValue.ReBaseStringUnits = True # I like pretty strings
    
    
    runner = cocotb.get_runner(__name__)
    
    dut = DUT()
    dut._log.info(f"enabled latch memory.  Will test with {runner}")
    
    runner.test(dut)