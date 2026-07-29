# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import random

import machine
from ttboard.boot.demoboard_detect import DemoboardDetect
from ttboard.demoboard import DemoBoard
import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import ClockCycles

from encdec8b10b import EncDec8B10B

cocotb.set_runner_scope(__name__)

async def sync_streams(dut, disp_a = 0, disp_b = 0):
    a = 0b0011111010 if disp_a == 0 else 0b1100000101
    b = 0b0011111010 if disp_b == 0 else 0b1100000101    

    for i in range(10):
        dut.ui_in.value = ((a >> 9) & 1) | ((b >> 8) & 2) | 0x84

        a <<= 1
        b <<= 1

        await ClockCycles(dut.clk, 1)

        assert dut.uo_out.value == 0x0

async def send_data(dut, a, b, disp_a, disp_b, ctrl, expect_updated = True, last_a = -1, last_b = -1):
    disp_a, a = EncDec8B10B.enc_8b10b(a, disp_a) if a >= 0 else EncDec8B10B.enc_8b10b(0b10111100, disp_a, 1)
    disp_b, b = EncDec8B10B.enc_8b10b(b, disp_b) if b >= 0 else EncDec8B10B.enc_8b10b(0b10111100, disp_a, 1)

    # Enable bidir outputs
    ctrl |= 0x80

    for i in range(10):
        dut.ui_in.value = (a & 1) | ((b << 1) & 2) | ctrl

        a >>= 1
        b >>= 1
        
        await ClockCycles(dut.clk, 1)

        if ctrl == 0x84:
            if i == 0 and expect_updated: 
                assert dut.uo_out.value == 0xF
                dut.ui_in.value = 0xc0
                if last_a != -1: assert dut.uo_out.value == last_a
                if last_b != -1: assert dut.uio_out.value == last_b
            else: assert dut.uo_out.value == 0x5

    return disp_a, disp_b

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 ns (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 1)

    for i in range(8):
        dut.ui_in.value = 1 << i
        await ClockCycles(dut.clk, 1)
        #assert dut.uio_oe.value == 0xFF
        if i < 4: assert dut.uo_out.value == 0xAA ^ (3 << (2 * i))
        else: assert dut.uo_out.value == 0xAA
        if i < 4: assert dut.uio_out.value == 0xAA
        else: assert dut.uio_out.value == 0xAA ^ (3 << (2 * (i - 4)))

    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 1)
    #assert dut.uio_oe.value == 0xFF

    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    #assert dut.uio_oe.value == 0
    dut.ui_in.value = 0x80
    #assert dut.uio_oe.value == 0xff

    await sync_streams(dut)

    disp_a = 0
    disp_b = 0

    # Send range of values, peeking at the result
    for i in range(256):
        disp_a, disp_b = await send_data(dut, i, 255 - i, disp_a, disp_b, 0x04, i != 0, i - 1, 256 - i)

    # Send range of values, check registered result
    last_a = 255
    last_b = 0
    for i in range(256):
        disp_a, disp_b = await send_data(dut, i, 255 - i, disp_a, disp_b, 0x20)
        
        assert dut.uo_out.value == last_a
        assert dut.uio_out.value == last_b
        last_a = i
        last_b = 255 - i

    # Send random values, check multiplied result
    last_ab = 0
    for i in range(256):
        a = random.randint(0, 255)
        b = random.randint(0, 255)
        disp_a, disp_b = await send_data(dut, a, b, disp_a, disp_b, 0x08)
        
        assert dut.uo_out.value == last_ab & 0xFF
        assert dut.uio_out.value == last_ab >> 8
        last_ab = a * b

    for i in range(512):
        a = random.randint(0, 255)
        b = random.randint(0, 255)
        if random.randint(0, 1) == 0:
            disp_a, disp_b = await send_data(dut, a, b, disp_a, disp_b, 0x10)
            
            assert dut.uo_out.value == last_ab & 0xFF
            assert dut.uio_out.value == last_ab >> 8
            last_ab = a * b
        else:
            keep = random.randint(1, 3)
            if keep & 1: a = -1
            if keep & 2: b = -1
            disp_a, disp_b = await send_data(dut, a, b, disp_a, disp_b, 0x10)
            
            assert dut.uo_out.value == last_ab & 0xFF
            assert dut.uio_out.value == last_ab >> 8

@cocotb.test()
async def test_sync(dut):
    dut._log.info("Start")

    # Set the clock period to 10 ns (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)

    dut.rst_n.value = 1
    dut.ui_in.value = 0x84

    dut._log.info("Test sync and desync")

    for i in range(100):
        await ClockCycles(dut.clk, random.randint(10,20))
        assert dut.uo_out.value == 0
        await sync_streams(dut, i & 2, i & 4)
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == 5
        
def main():
    # import examples.tt_um_factory_test.tt_um_factory_test as ft
    import ttboard.cocotb.dut
    
    class DUT(ttboard.cocotb.dut.DUT):
        def __init__(self):
            super().__init__('8b10b')
            self.tt = DemoBoard.get()
            
    DemoboardDetect.probe()            
    tt = DemoBoard.get()
    tt.shuttle.tt_um_MichaelBell_hs_mul.enable()
    tt.clock_project_stop()
    tt.uio_oe_pico.value = 0
    Clock.clear_all()
    
    # Go faster
    machine.freq(200000000)
    
    dut = DUT()
    dut._log.info("enabled 8b10b project, running")
    runner = cocotb.get_runner(__name__)
    runner.test(dut)
    
if __name__ == '__main__':
    main()
