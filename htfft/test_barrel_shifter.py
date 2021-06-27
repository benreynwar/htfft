import os
import shutil
from random import Random
import collections

import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_data(rnd, dut, size, shift_increment):
    max_chunk = pow(2, shift_increment)-1
    while True:
        data = [rnd.randint(0, max_chunk) for i in range(size)]
        dut.i_data <= conversions.list_of_uints_to_slv(data, width=shift_increment)
        dut.i_shift <= rnd.randint(0, shift_increment-1)
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
async def test_barrel_shifter(dut):
    seed = 0
    rnd = Random(seed)

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    shift_increment = int(dut.shift_increment.value)
    size = int(dut.size.value)

    # Ghdl doesn't support getting string generics yet.
    # pipeline = dut.pipeline.value
    # FIXME: Environment variables are a totally sensible way of passing the
    # pipeline to the test.
    pipeline = os.environ["TEST_BARREL_SHIFTER_PIPELINE_LENGTH"]
    pipeline_length = sum(int(s) for s in pipeline)

    cocotb.fork(send_data(
        rnd=rnd,
        dut=dut,
        size=size,
        shift_increment=shift_increment,
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
    working_directory = os.path.abspath('temp_test_barrel_shifter')
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    core_name = 'barrel_shifter'
    top_name = 'barrel_shifter'
    test_module_name = 'test_barrel_shifter'
    generics = {
        'size': 64,
        'shift_increment': 5,
        'pipeline': "1010101",
        }
    wave = True
    env = {"TEST_BARREL_SHIFTER_PIPELINE_LENGTH": generics['pipeline']}
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave, generics=generics, extra_env=env)


if __name__ == '__main__':
    main()
