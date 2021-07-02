import os
import shutil
from random import Random
import collections

import pytest
from numpy import fft
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions
from htfft import test_butterfly
from htfft import unrolled_fft_gen, htfft_gen
from htfft.test_htfft import get_expected_discrepancy

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_data(rnd, dut, input_width, size, sent_data):
    while True:
        values = [helper.random_complex(rnd, input_width) for i in range(size)]
        values_as_slv = conversions.list_of_complex_to_slv(values, input_width)
        dut.i_data <= values_as_slv
        sent_data.append(values)
        await triggers.RisingEdge(dut.clk)


@cocotb.test()
async def unrolled_fft_test(dut):
    test_params = helper.get_test_params()
    seed = test_params['seed']
    generation_params = test_params['generation']
    rnd = Random(seed)
    size = int(dut.size.value)
    input_width = int(dut.input_width.value)
    output_width = int(dut.output_width.value)
    latency =  test_butterfly.get_latency(
        generation_params['pipelines']['butterfly']) * helper.logceil(size)
    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())
    expected_discrepancy = 2 * get_expected_discrepancy(input_width, size)

    sent_data = collections.deque()
    await triggers.RisingEdge(dut.clk)
    cocotb.fork(send_data(rnd, dut, input_width, size, sent_data))
    for i in range(latency):
        await triggers.RisingEdge(dut.clk)
    for i in range(10):
        await triggers.ReadOnly()
        sent_vector = sent_data.popleft()
        o_data = int(dut.o_data.value)
        received = conversions.list_of_complex_from_slv(o_data, output_width, size)
        scaled = [x * size for x in received]
        expected = fft.fft(sent_vector)
        assert len(scaled) == len(expected)
        discrepancy = pow(sum(pow(abs(a-b), 2)
                              for a, b in zip(scaled, expected))/size, 0.5)
        assert discrepancy < 2 * expected_discrepancy
        await  triggers.RisingEdge(dut.clk)


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 123214
        rnd = Random(seed)
        suffix = '_{}_test'.format(test_index)
        n = rnd.choice([8, 16, 32, 64, 128])
        input_width = rnd.choice([8, 32])
        generation_params = {
            'suffix': suffix,
            'n': n,
            'input_width': input_width,
            'twiddle_width': input_width,
            'pipelines': htfft_gen.random_pipeline(rnd, n),
            }
        test_params = {
            'seed': seed,
            'core_name': 'unrolled_fft' + suffix,
            'top_name': 'unrolled_fft' + suffix,
            'test_module_name': 'test_unrolled_fft',
            'generation': generation_params,
            }
        yield test_params


def run_test(test_params, wave=False):
    suffix = test_params['generation']['suffix']
    working_directory = os.path.abspath(os.path.join('temp', 'test_unrolled_fft_{}'.format(suffix)))
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    generated_directory = os.path.join(basedir, 'generated')
    if not os.path.exists(generated_directory):
        os.makedirs(generated_directory)
    unrolled_fft_gen.make_unrolled_fft_core(
        directory=generated_directory, **test_params['generation'])
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
        run_test(test_params, wave=True)


if __name__ == '__main__':
    run_tests(n_tests=10, base_seed=0)
