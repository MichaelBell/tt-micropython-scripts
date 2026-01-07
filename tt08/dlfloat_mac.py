import gc
gc.threshold(80000)
from ttboard.boot.demoboard_detect import DemoboardDetect
DemoboardDetect.probe()
from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.time.value import TimeValue
import microcotb as cocotb
from microcotb.utils import get_sim_time
gc.collect()


# get the detected @cocotb tests into a namespace
# so we can load multiple such modules
cocotb.set_runner_scope(__name__)

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")
    #######1ST SET###########
    # Set the input values a1=1
    dut.ui_in.value = 0
    dut.uio_in.value = 62
    await ClockCycles(dut.clk, 1)
    # Set the input values b1=3
    dut.ui_in.value = 0
    dut.uio_in.value = 65
    await ClockCycles(dut.clk, 1)
    ######2ND SET############
    # Set the input values a2=1
    dut.ui_in.value = 0
    dut.uio_in.value = 62
    await ClockCycles(dut.clk, 1)
    # Set the input values b2=2
    dut.ui_in.value = 0
    dut.uio_in.value = 64
    await ClockCycles(dut.clk, 1)
    ######3RD SET###############
     # Set the input values a3=1
    dut.ui_in.value = 0
    dut.uio_in.value = 62
    await ClockCycles(dut.clk, 1)
    # Set the input values b3=4
    dut.ui_in.value = 0
    dut.uio_in.value = 66
    
    #1ST SET OUTPUT VERIF MSB
    assert dut.uo_out.value == 65
    
    await ClockCycles(dut.clk, 1)
    ######4TH SET###############
     # Set the input values a4=1
    dut.ui_in.value = 0
    dut.uio_in.value = 62
    
    #1ST SET OUTPUT VERIF LSB
    assert dut.uo_out.value == 0 
    await ClockCycles(dut.clk, 1)  
    # Set the input values b4=2
    dut.ui_in.value = 0
    dut.uio_in.value = 64
    
    #2ND SET OUTPUT VERIF MSB
    assert dut.uo_out.value == 66
    
    await ClockCycles(dut.clk, 1)
    ######5TH SET###############
     # Set the input values a5=1
    dut.ui_in.value = 0
    dut.uio_in.value = 62
    
    #2ND SET OUTPUT VERIF LSB
    assert dut.uo_out.value == 128 
    await ClockCycles(dut.clk, 1)  
    # Set the input values b5=2
    dut.ui_in.value = 0
    dut.uio_in.value = 64
    ##########3RD SET verif msb#############
   
    assert dut.uo_out.value == 68 
    await ClockCycles(dut.clk, 1)
    #6th set input a6=1.32
    dut.ui_in.value = 163
    dut.uio_in.value = 62
    #3rd set verif lsb
   
    assert dut.uo_out.value == 64
    await ClockCycles(dut.clk, 1)
    #6th set input b6=2.45
    dut.ui_in.value = 115
    dut.uio_in.value = 64
    ##########4TH SET verif msb#############
    
    assert dut.uo_out.value == 68
    await ClockCycles(dut.clk, 1)
    #7th input a7 = -1.32
    dut.ui_in.value = 163
    dut.uio_in.value = 190
    #4th set lsb verif
    assert dut.uo_out.value == 192
    await ClockCycles(dut.clk, 1)
    #7th input b7 = -2.45
    dut.ui_in.value = 115
    dut.uio_in.value = 192
    ##########5TH SET verif msb#############
    
    assert dut.uo_out.value == 69
    await ClockCycles(dut.clk, 1)
    #8th set a8 = -1.89
    dut.ui_in.value = 199
    dut.uio_in.value = 191
    #5th verif lsb
    assert dut.uo_out.value == 64
    await ClockCycles(dut.clk, 1)
    #8th set b8 = 2.67
    dut.ui_in.value = 171
    dut.uio_in.value = 64
    #6th set verif msb
    assert dut.uo_out.value == 70
    await ClockCycles(dut.clk, 1)
    #9th set a9 = -2.45
    dut.ui_in.value = 115
    dut.uio_in.value = 192
    #6th set verif lsb
    assert dut.uo_out.value == 7
    await ClockCycles(dut.clk, 1)
    #9th set b9 = 1.32
    dut.ui_in.value = 163
    dut.uio_in.value = 62
    #7th set verif msb
    assert dut.uo_out.value == 70
    await ClockCycles(dut.clk, 1)
    #10th set a10 = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    #7th set verif lsb
    assert dut.uo_out.value == 110
    await ClockCycles(dut.clk, 1)
    #10th set b10 = 0.98
    dut.ui_in.value = 235
    dut.uio_in.value = 61
    #8th set verif msb
    assert dut.uo_out.value == 69
    await ClockCycles(dut.clk, 1)
    #8th set verif lsb
    assert dut.uo_out.value == 154
    await ClockCycles(dut.clk, 1)
    #9th set verif msb
    assert dut.uo_out.value == 68
    await ClockCycles(dut.clk, 1)
    #9th set verif lsb
    assert dut.uo_out.value == 204
    await ClockCycles(dut.clk, 1)
    #10th set verif msb
    assert dut.uo_out.value == 68
    await ClockCycles(dut.clk, 1)
    #10th set verif lsb
    assert dut.uo_out.value == 204
    await ClockCycles(dut.clk, 1)

def main():
    import ttboard.cocotb.dut
    
    class DUT(ttboard.cocotb.dut.DUT):
        def __init__(self):
            super().__init__('DLFloat MAC')
            self.tt = DemoBoard.get()
    
    tt = DemoBoard.get()
    tt.shuttle.tt_um_dlfloatmac.enable()
    
    if tt.mode != RPMode.ASIC_RP_CONTROL:
        print("Setting mode to ASIC_RP_CONTROL")
        tt.mode = RPMode.ASIC_RP_CONTROL
        
    tt.uio_oe_pico.value = 0xff # all outputs
    
    
    TimeValue.ReBaseStringUnits = True # I like pretty strings
    
    
    runner = cocotb.get_runner(__name__)
    
    dut = DUT()
    dut._log.info(f"enabled dlfloat mac project.  Will test with {runner}")
    
    runner.test(dut)
