import os
import shutil
import itertools
from random import Random
import collections

import pytest
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_data(rnd, dut, width, spcc, n, sent_queue):
    max_chunk = pow(2, width * spcc/2)-1
    count = 0
    await triggers.RisingEdge(dut.clk)
    dut.i_beforefirst <= 1
    await triggers.RisingEdge(dut.clk)
    while True:
        data_a = rnd.randint(0, max_chunk)
        dut.i_data_a <= data_a
        data_b = rnd.randint(0, max_chunk)
        dut.i_data_b <= data_b
        sent_queue.append((
            conversions.list_of_uints_from_slv(data_a, width=width, size=spcc//2),
            conversions.list_of_uints_from_slv(data_b, width=width, size=spcc//2),
        ))
        dut.i_beforefirst <= (1 if (count % (n/spcc)) == n//spcc-1 else 0)
        count += 1
        await triggers.RisingEdge(dut.clk)


async def check_data(dut, width, spcc, n, sent_queue):
    while True:
        await triggers.ReadOnly()
        if str(dut.o_beforefirst.value) == '1':
            await triggers.RisingEdge(dut.clk)
            break
        await triggers.RisingEdge(dut.clk)
    for vector_index in itertools.count():
        received_values = []
        for chunk_index in range(n//spcc):
            await triggers.ReadOnly()
            received_values += conversions.list_of_uints_from_slv(
                dut.o_data.value.integer, width=width, size=spcc)
            await triggers.RisingEdge(dut.clk)
        sent_a_values = []
        sent_b_values = []
        for chunk_index in range(n//spcc):
            a_values, b_values = sent_queue.popleft()
            sent_a_values += a_values
            sent_b_values += b_values
        # For the expected value should be all the values that came in
        # on _a followed by all the values that came in on _b.
        expected_values = sent_a_values + sent_b_values
        assert expected_values == received_values


@cocotb.test()
async def final_memory_test(dut):
    test_params = helper.get_test_params()
    seed = test_params['seed']
    rnd = Random(seed)

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    fft_size = int(dut.n.value)
    width = int(dut.width.value)
    spcc = int(dut.spcc.value)

    sent_queue = collections.deque()

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
        sent_queue=sent_queue,
    ))
    for i in range(fft_size//spcc*100):
        await triggers.RisingEdge(dut.clk)


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 13987
        rnd = Random(seed)
        n = rnd.choice([8, 16, 32, 64, 128, 256])
        possible_spcc = [spcc for spcc in (2, 4, 8, 16, 32)
                         if helper.logceil(spcc) <= helper.logceil(n)/2]
        spcc = rnd.choice(possible_spcc)
        width = rnd.choice([8, 32])
        generics = {
            'n': n,
            'spcc': spcc,
            'width': width,
            }
        test_params = {
            'test_index': test_index,
            'seed': seed,
            'core_name': 'final_memory',
            'top_name': 'final_memory',
            'test_module_name': 'test_final_memory',
            'generics': generics,
            }
        yield test_params


def run_test(test_params, wave=False):
    working_directory = os.path.abspath(os.path.join(
        'temp', 'test_final_memory_{}'.format(test_params['test_index'])))
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    helper.run_core(
        working_directory,
        core_name=test_params['core_name'],
        top_name=test_params['top_name'],
        test_module_name=test_params['test_module_name'],
        generics=test_params['generics'],
        wave=wave,
        test_params=test_params)


@pytest.mark.parametrize('test_params', get_test_params(n_tests=10))
def test_htfft(test_params):
    run_test(test_params, wave=False)


def run_tests(n_tests=10):
    for test_params in get_test_params(n_tests=n_tests):
        run_test(test_params, wave=False)


if __name__ == '__main__':
    run_tests()
