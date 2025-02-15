import machine
from ttboard.demoboard import DemoBoard
import ttboard.cocotb as cocotb
from ttboard.cocotb.clock import Clock
from ttboard.cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


BITS = 144
BYTES = BITS >> 3
READ_PATH_RECORD_BIT = 1 << 5
START_COMPUTING_BIT = 1 << 6
DONE_COMPUTING_BIT = 1 << 7
WRITE_ENABLE_BIT = 1 << 7


@cocotb.test()
async def test_collatz(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    tests = [
        (8, 3, 8),
        (5, 5, 16),
        (57, 32, 196),
        (578745, 128, 1953268),
        (87234789, 112, 261704368),
        (87233489, 236, 261700468),
        (517791692, 91, 622051648),
        (2201842808, 344, 2786707312),
        (803982451, 141, 3617921032),
        (3609942504, 112, 3659193952),
        (3083255988, 161, 3083255988),
        (463021824, 179, 463021824),
        (3267781108, 280, 3267781108),
        (2421305922, 96, 3631958884),
        (1971691608, 269, 1971691608),
        (3499967984, 112, 3499967984),
        (978115257, 224, 3301138996),
        (771835010, 252, 1157752516),
        (1226612421, 245, 3679837264),
        (1183962468, 188, 1183962468),
        (2105577732, 251, 2105577732),
        (175642554, 268, 263463832),
        (3965035960, 363, 3965035960),
        (1685248072, 354, 1685248072),
        (463810068, 153, 463810068),
        (350641295, 207, 3550243120),
        (425895361, 202, 1277686084),
        (553388553, 156, 2801529556),
        (1199953526, 188, 3037382368),
        (299936535, 212, 2024571616),
        (616267482, 244, 924401224),
        (1934622276, 256, 1934622276),
        (1619815328, 160, 1619815328),
        (446335366, 210, 1004254576),
        (3040231372, 205, 3702227776),
        (1732127988, 116, 1732127988),
        (847903897, 185, 2861675656),
        (3528879920, 187, 3528879920),
        (2480469920, 308, 2480469920),
        (1518424872, 204, 1518424872),
        (1278187560, 183, 1278187560),
        (219017438, 183, 2104941544),
        (778189056, 234, 778189056),
        (647255766, 288, 1456325476),
        (471175373, 166, 1413526120),
        (87013076, 117, 87013076),
        (216927658, 139, 325391488),
        (1983222946, 238, 3176739700),
        (371886186, 220, 557829280),
        (2401413698, 163, 3602120548),
        (3765123600, 226, 3765123600),
        (3207120428, 187, 3852890116),
        (122734474, 221, 184101712),
        (562919287, 187, 3799705192),
        (2222673568, 127, 2222673568),
        (276616221, 235, 829848664),
        (2105028314, 199, 3157542472),
        (1394410682, 240, 2091616024),
        (60456907, 176, 272056084),
        (126710349, 128, 380131048),

        # expected overflows:
        (1487063479, 191, 10037678488),
        (1487063479, 191, 10037678488),
        (3744461465, 213, 12637557448),
        (4045380941, 301, 12136142824),
        (3328045995, 161, 14976206980),
        (609787903, 262, 600800394580),
        (3277473346, 187, 4916210020),
        (1980890718, 194, 10028259268),
        (3374936602, 231, 5062404904),
        (1273462655, 245, 43516606696),
        (1668429215, 186, 72157526944),
        (1378381212, 271, 13247401120),
        (2630975025, 246, 182263904944),
        (3183903831, 174, 21491350864),
        (3737972453, 205, 11213917360),
        (3882955187, 182, 17473298344),
        (2568484190, 427, 13002951220),
        (1756674699, 292, 9757656736),
        (1278924513, 201, 14766501256),
        (2147753997, 176, 6443261992),
        (3882398953, 164, 29481967060),
        (2573139127, 202, 17368689112),
        (2355062134, 401, 42969471784),
        (3361024734, 156, 19142086192),
        (471343081, 285, 6040003840),
        (3533988353, 156, 10601965060),
        (3585668161, 213, 10757004484),
        (4139110934, 231, 551788260244),
        (1903667965, 199, 10841983972),
        (3535674805, 107, 10607024416),
        (1133736201, 294, 5739539524),
        (1565016040, 173, 7623164392),
        (1991700587, 186, 36339730000),
        (1391268039, 209, 9391059268),
        (2018450137, 194, 6812269216),
        (796021339, 301, 218067215200),
        (3852828572, 288, 10971531376),
        (2162764140, 189, 4619106628),
        (2893424721, 316, 8680274164),
        (1628671260, 191, 5571759364),
        (3893436958, 195, 19710524608),
        (3557777921, 231, 10673333764),

        # 64-bit test cases:
        (7842936325854527010, 306, 11764404488781790516),
        (4371101319062825892, 543, 13292212235092547956),
        (10594431906321232920, 508, 10594431906321232920),
        (890868634783200835, 564, 4008908856524403760),
        (4534089962051137564, 388, 7651276810961294644),

        # overflowing 64-bit test cases:
        (4871825635628666919, 432, 36995425920555189424),  #  << OVERFLOW
        (14052403568816099079, 449, 94853724089508668788),  #  << OVERFLOW
        (8880985985428114876, 332, 25289995247566780264),  #  << OVERFLOW
        (7646221149529662555, 399, 97982142504031476628),  #  << OVERFLOW
        (11368048319433266005, 384, 34104144958299798016),  #  << OVERFLOW

        # 144-bit test cases:
        (76812719373007741932564975958306103955618, 746, 115219079059511612898847463937459155933428),
        (5840564564390311183599505531297529631750036, 1135, 11239222584029864994745896324979731114827620),
        (5552450647653480327512907765576451030192913, 848, 16657351942960440982538723296729353090578740),
        (19412885625565463697736663712899211592860020, 1010, 19412885625565463697736663712899211592860020),
        (3012445987290400330380289851637892354190268, 891, 19301423947863590398071368863863488023283572),

        # overflowing 144-bit test cases:
        # (9538163849286484684936098584142661875319637, 797, 28614491547859454054808295752427985625958912),  #  << OVERFLOW
        # (12457369670021871660614460498630620828179883, 1066, 161812313805977923553639899721950033920419728),  #  << OVERFLOW
        # (19091159896150669357805683577582932025193609, 1147, 2975765996704769158177325654959293037770170992),  #  << OVERFLOW
        # (9524856959679701030992026265084759236957493, 1195, 28574570879039103092976078795254277710872480),  #  << OVERFLOW
        # (20547317868323463498998361184730124261402691, 899, 92462930407455585745492625331285559176312112),  #  << OVERFLOW

        # few of the previous path records:
        (48503373501652785087, 1234, 593393421816294729494460596878576979284),
        (55247846101001863167, 1534, 964385262182693753484691749002792632456),
        (71149323674102624415, 1687, 9055383924226744340579466230337749396932),
        (274133054632352106267, 1805, 113298124744388651798242538014293435290632),
        (1378299700343633691495, 1500, 146323898913724962892154638143488597621248),
    ]

    for t in tests:
        input, want_orbit, want_record = t

        # reset
        dut._log.info("reset")
        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 2)
        dut.rst_n.value = 1
        await ClockCycles(dut.clk, 2)

        # set input
        await set_input(dut, input)
        await start_computing(dut)
        await done_computing(dut)

        # read output and assert
        orbit_len, path_record_h16 = await read_output(dut)
        dut._log.info(f"Ran test: {input}, want {want_orbit} = {orbit_len}")
        assert orbit_len == want_orbit
        want_record_h16 = extract_upper_bits(want_record, 16)
        assert path_record_h16 == want_record_h16, f'for len {orbit_len}'


def extract_upper_bits(number, nbits):
    return number >> (BITS - nbits)


def extract_ith_byte(number, i):
    return (number >> (i*8)) & 0xff


async def pulse_write_enable(dut):
    dut.uio_in.value |= WRITE_ENABLE_BIT
    await ClockCycles(dut.clk, 1)
    dut.uio_in.value &= ~WRITE_ENABLE_BIT


async def set_input(dut, input):
    for i in range(BYTES):
        data_byte = extract_ith_byte(input, i)
        dut.uio_in.value = i         # set address of i'th byte
        dut.ui_in.value = data_byte  # set the data byte
        await ClockCycles(dut.clk, 1)
        await pulse_write_enable(dut)


async def start_computing(dut):
    dut.tt.uio_oe_pico.value = 0x7f
    dut.uio_in.value = START_COMPUTING_BIT
    await ClockCycles(dut.clk, 2)
    dut.uio_in.value = 0x00


async def done_computing(dut):
    while int(dut.uio_out.value) & DONE_COMPUTING_BIT:
        await ClockCycles(dut.clk, 1)
    await ClockCycles(dut.clk, 1)
    dut.tt.uio_oe_pico.value = 0xff
    dut.uio_in.value = 0x00


async def read_n_byte_num(dut, nbytes, extra_bits=0):
    number = 0
    for i in range(nbytes):
        dut.uio_in.value = i | extra_bits
        await ClockCycles(dut.clk, 2)
        b = int(dut.uo_out.value)
        number |= b << (i*8)
    return number


async def read_output(dut):
    orbit_len = await read_n_byte_num(dut, 2)
    path_rec = await read_n_byte_num(dut, 2, READ_PATH_RECORD_BIT)
    return orbit_len, path_rec


def main():
    # import examples.tt_um_factory_test.tt_um_factory_test as ft
    from ttboard.cocotb.dut import DUTWrapper, FakeSignal
    
    class DUT(DUTWrapper):
        def __init__(self):
            super().__init__()
            self.tt = DemoBoard.get()
            
                
    tt = DemoBoard.get()
    tt.shuttle.tt_um_rtfb_collatz.enable()
    tt.clock_project_stop()
    tt.uio_oe_pico.value = 0xff # MOSI is output
    Clock.clear_all()
    
    # Go faster
    machine.freq(200000000)
    
    dut = DUT()
    dut._log.info("enabled factory test project, running")
    runner = cocotb.get_runner()
    runner.test(dut)
    
if __name__ == '__main__':
    main()