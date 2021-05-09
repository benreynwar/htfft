import os
import shutil
from random import Random

import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))

async def send_input(dut, input_data, N, size, width):
    chunked_data = [input_data[index*size//2: (index+1)*size//2]
                    for index in range(2*N//size)]
    L = N//size
    for input_index in range(L):
        if input_index < L//2:
            input_data_a = chunked_data[input_index]
            input_data_b = chunked_data[input_index + L//2]
        else:
            input_data_a = chunked_data[input_index + L//2]
            input_data_b = chunked_data[input_index + L]
        dut.i_data_a <= conversions.list_of_complex_to_slv(input_data_a, width=width)
        dut.i_data_b <= conversions.list_of_complex_to_slv(input_data_b, width=width)
        await triggers.RisingEdge(dut.clk)


async def check_output(dut, input_data, N, size, width):
    expected_data = stage_model(input_data)
    chunked_data = [expected_data[index*size//2: (index+1)*size//2]
                    for index in range(2*N//size)]
    L = N//size
    for output_index in range(L):
        expected_data_a = chunked_data[output_index]
        expected_data_b = chunked_data[output_index + L]
        await triggers.ReadOnly()
        received_data_a = conversions.list_of_complex_from_slv(
            int(dut.o_data_a.value), width=width, size=size//2)
        received_data_a = [2 * x for x in received_data_a]
        received_data_b = conversions.list_of_complex_from_slv(
            int(dut.o_data_b.value), width=width, size=size//2)
        received_data_b = [2 * x for x in received_data_b]
        check_equal(expected_data_a, received_data_a)
        check_equal(expected_data_b, received_data_b)
        await triggers.RisingEdge(dut.clk)


def check_equal(complexes_a, complexes_b):
    for a, b in zip(complexes_a, complexes_b):
        assert abs(a - b) < 1e-2


def stage_model(input_data):
    output_data = [None] * len(input_data)
    N = len(input_data)
    for index in range(N//2):
        first_index = index
        second_index = index + N//2
        a = input_data[first_index]
        b = input_data[second_index]
        twiddle = helper.get_twiddle(index, N)
        bt = b * twiddle
        c = a + bt
        d = a - bt
        output_data[first_index] = c
        output_data[second_index] = d
    assert None not in output_data
    return output_data


@cocotb.test()
async def test_stage(dut):
    seed = 0
    rnd = Random(seed)

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    # Total FFT size
    N = int(dut.n.value)
    # Bits in one complex number
    width = int(dut.width.value)
    # Number of samples (complex numbers) received every clock cycle.
    size = int(dut.size.value)

    output_width = int(dut.output_width.value)

    allowed_diff = 2 * 1/pow(2, width//2 - 2)

    await triggers.RisingEdge(dut.clk)
    dut.i_reset <= 1
    await triggers.RisingEdge(dut.clk)
    dut.i_reset <= 0

    input_data = [0.2 - 0.3j, -1, 1, 0.3-0.2j, -1, 0.1, 0.5 - 0.5j, 0+0.1j]
    cocotb.fork(send_input(
        dut=dut,
        input_data=input_data,
        N=N,
        size=size,
        width=width,
    ))
    while True:
        await triggers.RisingEdge(dut.clk)
        await triggers.ReadOnly()
        if str(dut.o_reset.value) == '1':
            print('got it')
            break
    await triggers.RisingEdge(dut.clk)
    await cocotb.fork(check_output(
        dut=dut,
        input_data=input_data,
        N=N,
        size=size,
        width=output_width))


def main():
    working_directory = os.path.abspath('temp_test_stage')
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    core_name = 'stage_example'
    top_name = 'stage_8_example'
    test_module_name = 'test_stage'
    wave = True
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave)

if __name__ == '__main__':
    main()
