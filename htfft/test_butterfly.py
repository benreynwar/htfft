import os
from random import Random

import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))

@cocotb.test()
async def test_unrolled_fft(dut):
    seed = 0
    rnd = Random(seed)
    values = [1, 0]
    width = int(dut.width.value)
    twiddle_width = int(dut.twiddle_width.value)
    # Allow errors equal to twice the spacing between representatable
    # complex numbers.
    # FIXME: I think we could improve this with better rounding in the
    # implementation.
    allowed_diff = 2 * 1/pow(2, width//2 - 2)
    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())
    await triggers.RisingEdge(dut.clk)
    for i in range(100):
        a = helper.random_complex(rnd, width)
        b = helper.random_complex(rnd, width)
        t = helper.random_complex(rnd, twiddle_width)
        bt = b * t
        c = a + bt
        d = a - bt
        dut.i_a <= conversions.complex_to_slv(a, width)
        dut.i_b <= conversions.complex_to_slv(b, width)
        dut.i_t <= conversions.complex_to_slv(t, width)
        for i in range(10):
            await triggers.RisingEdge(dut.clk)
        await triggers.ReadOnly()
        o_c = conversions.complex_from_slv(int(dut.o_c.value), width+2)
        o_d = conversions.complex_from_slv(int(dut.o_d.value), width+2)
        # Remove the scaling by two that we did.
        o_c = o_c*2
        o_d = o_d*2
        assert abs(c - o_c) < allowed_diff
        assert abs(d - o_d) < allowed_diff
        await triggers.RisingEdge(dut.clk)


def main():
    working_directory = os.path.abspath('temp_test_butterfly')
    os.makedirs(working_directory)
    core_name = 'butterfly'
    top_name = 'butterfly'
    test_module_name = 'test_butterfly'
    wave = True
    generics = {
        'width': 10,
        'twiddle_width': 10,
        'mult_pipeline_length': 3,
        'reg_i_p': 'true',
        'reg_q_r': 'true',
        'reg_r_s': 'true',
        'reg_s_o': 'true',
        }
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave, generics=generics)

if __name__ == '__main__':
    main()
