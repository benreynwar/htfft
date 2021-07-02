import os
import math
import shutil
from random import Random
import collections
import pytest

from numpy import fft
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions
import htfft_gen

basedir = os.path.abspath(os.path.dirname(__file__))


def get_expected_discrepancy(input_width, n):
    component_width = input_width/2
    n_increments = pow(2, component_width)
    increment_size = 2/n_increments  # because we go from -1 to 1
    average_error = increment_size*0.75
    # Empirically each time N doubles, error goes up by 1.6
    expected_error = pow(1.6, math.log(n)/math.log(2)) * average_error
    return expected_error


async def send_data(rnd, dut, sent_queue, n, spcc, input_width):
    while True:
        values = [helper.random_complex(rnd, input_width)
                  for i in range(n)]
        sent_queue.append(values)
        lumps = [values[index*spcc: (index+1)*spcc]
                 for index in range(n//spcc)]
        dut.i_first <= 1
        for lump in lumps:
            lump_as_slv = conversions.list_of_complex_to_slv(lump, input_width)
            dut.i_data <= lump_as_slv
            await triggers.RisingEdge(dut.clk)
            dut.i_first <= 0


async def check_data(rnd, dut, sent_queue, n, spcc, input_width, output_width, n_vectors):
    assert n % spcc == 0
    n_lumps = n//spcc
    await triggers.ReadOnly()
    expected_discrepancy = get_expected_discrepancy(input_width=input_width, n=n)
    discrepancies = []
    for vector_index in range(n_vectors):
        while True:
            if str(dut.o_first.value) == '1':
                break
            await triggers.RisingEdge(dut.clk)
            await triggers.ReadOnly()
        received_data = []
        for lump_index in range(n_lumps):
            assert dut.o_first.value == (1 if lump_index == 0 else 0)
            complexes = conversions.list_of_complex_from_slv(
                dut.o_data.value.integer, output_width, spcc)
            received_data += [x * n for x in complexes]
            await triggers.RisingEdge(dut.clk)
            await triggers.ReadOnly()
        sent_data = sent_queue.popleft()
        expected_data = fft.fft(sent_data)
        assert len(received_data) == len(expected_data)
        assert len(received_data) == n
        discrepancy = pow(sum(pow(abs(a-b), 2)
                              for a, b in zip(received_data, expected_data))/n, 0.5)
        discrepancies.append(discrepancy)
        assert discrepancy < 2 * expected_discrepancy


@cocotb.test()
async def htfft_test(dut):
    test_params = helper.get_test_params()
    generation_params = test_params['generation']
    spcc = generation_params['spcc']
    n = generation_params['n']
    input_width = generation_params['input_width']
    n_vectors = test_params['n_vectors']
    output_width = input_width + 2*helper.logceil(n)
    seed = test_params['seed']
    rnd = Random(seed)
    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())
    await triggers.RisingEdge(dut.clk)
    dut.reset <= 1
    await triggers.RisingEdge(dut.clk)
    dut.reset <= 0
    sent_queue = collections.deque()
    cocotb.fork(send_data(rnd, dut, sent_queue, n, spcc, input_width,))
    await cocotb.fork(check_data(rnd, dut, sent_queue, n, spcc,
                                 input_width, output_width, n_vectors=n_vectors))


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 123214
        rnd = Random(seed)
        suffix = '_{}_test'.format(test_index)
        n = rnd.choice([8, 16, 32, 64, 128, 256])
        possible_spcc = [spcc for spcc in (2, 4, 8, 16, 32)
                         if helper.logceil(spcc) <= helper.logceil(n)/2]
        spcc = rnd.choice(possible_spcc)
        input_width = rnd.choice([8, 32])
        generation_params = {
            'suffix': suffix,
            'n': n,
            'spcc': spcc,
            'input_width': input_width,
            'pipelines': htfft_gen.random_pipeline(rnd, spcc),
            }
        n_vectors = 10
        test_params = {
            'n_vectors': n_vectors,
            'seed': seed,
            'core_name': 'htfft' + suffix,
            'top_name': 'htfft' + suffix,
            'test_module_name': 'test_htfft',
            'generation': generation_params,
            }
        yield test_params


def run_test(test_params, wave=False):
    suffix = test_params['generation']['suffix']
    working_directory = os.path.abspath(os.path.join('temp', 'test_htfft_{}'.format(suffix)))
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    generated_directory = os.path.join(basedir, 'generated')
    if not os.path.exists(generated_directory):
        os.makedirs(generated_directory)
    htfft_gen.make_htfft_core(directory=generated_directory, **test_params['generation'])
    helper.run_core(
        working_directory,
        core_name=test_params['core_name'],
        top_name=test_params['top_name'],
        test_module_name=test_params['test_module_name'],
        wave=wave,
        test_params=test_params)


@pytest.mark.parametrize('test_params', get_test_params(n_tests=10))
def test_htfft(test_params):
    run_test(test_params, wave=False)


def run_tests(n_tests=10, base_seed=0):
    for test_params in get_test_params(n_tests=n_tests, base_seed=base_seed):
        run_test(test_params, wave=False)


if __name__ == '__main__':
    run_tests()
