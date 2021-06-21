import os
import shutil
import itertools
from random import Random
import collections

import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_data(rnd, dut, width, spcc, n, sent_queue):
    max_chunk = pow(2, width * spcc)-1
    count = 0
    dut.i_beforefirst <= 1
    await triggers.RisingEdge(dut.clk)
    while True:
        data = rnd.randint(0, max_chunk)
        dut.i_data <= data
        sent_queue.append(conversions.list_of_uints_from_slv(
            data, width=width, size=spcc))
        dut.i_beforefirst <= (1 if count == n//spcc-1 else 0)
        count = (count + 1) % (n//spcc)
        await triggers.RisingEdge(dut.clk)


async def check_data(dut, width, spcc, n, pipeline_length, sent_queue):
    while True:
        await triggers.ReadOnly()
        if dut.i_beforefirst.value.integer == 1:
            await triggers.RisingEdge(dut.clk)
            break
        await triggers.RisingEdge(dut.clk)
    for i in range(pipeline_length):
        await triggers.RisingEdge(dut.clk)
    for vector_index in itertools.count():
        received_values = []
        for chunk_index in range(n//spcc):
            await triggers.ReadOnly()
            received_values += conversions.list_of_uints_from_slv(
                dut.o_data.value.integer, width=width, size=spcc)
            await triggers.RisingEdge(dut.clk)
        sent_values = []
        for chunk_index in range(n//spcc):
            sent_values += sent_queue.popleft()
        expected_values = []
        for index in range(n):
            reversed_index = helper.reverse_bits(
                index, n_bits=helper.logceil(n))
            expected_values.append(sent_values[reversed_index])
        assert expected_values == received_values
        print('yay!')


@cocotb.test()
async def test_initial_memory(dut):
    seed = 0
    rnd = Random(seed)

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    fft_size = int(dut.n.value)
    width = int(dut.width.value)
    spcc = int(dut.spcc.value)

    # Ghdl doesn't support getting string generics yet.
    # pipeline = dut.pipeline.value
    # FIXME: Environment variables are a totally sensible way of passing the
    # pipeline to the test.
    barrel_shifter_pipeline = os.environ["TEST_INITIAL_MEMORY_BARREL_SHIFTER_PIPELINE_LENGTH"]
    barrel_shifter_pipeline_length = sum(int(s) for s in barrel_shifter_pipeline)
    pipeline_length = barrel_shifter_pipeline_length*2+1+fft_size//spcc
    sent_queue = collections.deque()

    await triggers.RisingEdge(dut.clk)
    dut.reset <= 1
    await triggers.RisingEdge(dut.clk)
    dut.reset <= 0

    cocotb.fork(send_data(
        rnd=rnd,
        dut=dut,
        width=width,
        spcc=spcc,
        n=fft_size,
        sent_queue=sent_queue,
    ))
    cocotb.fork(check_data(
        dut=dut,
        width=width,
        spcc=spcc,
        n=fft_size,
        pipeline_length=pipeline_length,
        sent_queue=sent_queue,
    ))
    for i in range(pipeline_length + fft_size//spcc*100):
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
        'n': 64,
        'width': 4,
        'spcc': 8,
        'barrel_shifter_pipeline': "1111",
        }
    wave = True
    env = {"TEST_INITIAL_MEMORY_BARREL_SHIFTER_PIPELINE_LENGTH": generics['barrel_shifter_pipeline']}
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave, generics=generics, extra_env=env)

if __name__ == '__main__':
    main()
