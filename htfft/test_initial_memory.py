import os
import shutil
from random import Random
import collections

import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_data(rnd, dut, width, spcc):
    max_chunk = pow(2, width * spcc)-1
    while True:
        dut.i_data <= rnd.randint(max_chunk)
        await triggers.RisingEdge(dut.clk)


async def check_data(dut, size, shift_increment, pipeline_length):
    expected_datas = collections.deque([None] * pipeline_length)
    while True:
        await triggers.ReadOnly()
        data = conversions.list_of_uints_from_slv(
            int(dut.i_data.value), width=shift_increment, size=size)
        shift = int(dut.i_shift.value)
        shifted_data = data[shift:] + data[:shift]
        expected_datas.append(shifted_data)

        expected_data = expected_datas.popleft()

        if expected_data is not None:
            received_data = conversions.list_of_uints_from_slv(
                int(dut.o_data.value), width=shift_increment, size=size)
            assert expected_data == received_data
        await triggers.RisingEdge(dut.clk)


@cocotb.test()
async def test_inital_memory(dut):
    seed = 0
    rnd = Random(seed)

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    fft_size = int(dut.n.value)
    width = int(dut.width.value)
    size = int(dut.size.value)

    # Ghdl doesn't support getting string generics yet.
    # pipeline = dut.pipeline.value
    # FIXME: Environment variables are a totally sensible way of passing the
    # pipeline to the test.
    barrel_shifter_pipeline = os.environ["TEST_INITIAL_MEMORY_BARREL_SHIFTER_PIPELINE_LENGTH"]

    cocotb.fork(send_data(
        rnd=rnd,
        dut=dut,
        width=width,
        spcc=spcc,
    ))
    cocotb.fork(check_data(
        dut=dut,
        size=size,
        shift_increment=shift_increment,
        pipeline_length=pipeline_length,
    ))
    for i in range(100):
        await triggers.RisingEdge(dut.clk)


def main():
    working_directory = os.path.abspath('temp_test_initial_memory')
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    core_name = 'initial_memory'
    top_name = 'initial_memory'
    test_module_name = 'test_initial_memory'
    generics = {
        'n': 4,
        'width': 2,
        'spcc': 2,
        'barrel_shifter_pipeline': "1010101",
        }
    wave = True
    env = {"TEST_INITIAL_MEMORY_BARREL_SHIFTER_PIPELINE_LENGTH": generics['barrel_shifter_pipeline']}
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave, generics=generics, extra_env=env)

if __name__ == '__main__':
    main()
