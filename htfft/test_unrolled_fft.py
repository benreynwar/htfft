import os
from random import Random

from numpy import fft
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


@cocotb.test()
async def test_unrolled_fft(dut):
    seed = 0
    rnd = Random(seed)
    size = int(dut.size.value)
    input_width = int(dut.input_width.value)
    output_width = int(dut.output_width.value)
    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())
    # FIXME: Try to improve implementation to get fudge down to 1.
    fudge = 4
    allowed_diff = fudge * 1/pow(2, input_width//2 - 2)
    for i in range(1):
        values = [helper.random_complex(rnd, input_width)
                for i in range(size)]
        await triggers.RisingEdge(dut.clk)
        values_as_slv = conversions.list_of_complex_to_slv(values, input_width)
        dut.i_data <= values_as_slv
        for i in range(10*6):
            await triggers.RisingEdge(dut.clk)
        await triggers.ReadOnly()
        o_data = int(dut.o_data.value)
        received = conversions.list_of_complex_from_slv(o_data, output_width, size)
        scaled = [x * size for x in received]
        expected = fft.fft(values)
        assert len(scaled) == len(expected)
        max_diff = max(abs(a - b) for a, b in zip(scaled, expected))
        assert max_diff < allowed_diff


def main():
    working_directory = os.path.abspath('test_blahblah')
    os.makedirs(working_directory)
    core_name = 'unrolled_fft_example'
    top_name = 'unrolled_fft_64_example'
    test_module_name = 'test_unrolled_fft'
    wave = True
    helper.run_core(working_directory, core_name, top_name, test_module_name, wave=wave)


if __name__ == '__main__':
    main()
