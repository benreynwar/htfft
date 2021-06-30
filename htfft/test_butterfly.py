import os
import shutil
import collections
from random import Random

import pytest
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))

async def send_data(rnd, dut, width, sent_queue):
    while True:
        a = helper.random_complex(rnd, width)
        b = helper.random_complex(rnd, width)
        t = helper.random_complex(rnd, width)
        dut.i_a <= conversions.complex_to_slv(a, width)
        dut.i_b <= conversions.complex_to_slv(b, width)
        dut.i_t <= conversions.complex_to_slv(t, width)
        sent_queue.append((a, b, t))
        await triggers.RisingEdge(dut.clk)


async def check_data(dut, width, sent_queue, latency):
    # Allow errors equal to twice the spacing between representatable
    # complex numbers.
    # FIXME: I think we could improve this with better rounding in the
    # implementation.

    increment_size = 2 / pow(2, width//2)
    max_input_dev = increment_size / pow(2, 0.5)
    # But we have 3 inputs that contribute to the output so
    # and the output could get rounded by this amount to so
    max_output_dev = max_input_dev * 4
    # FIXME: Fudge factor is large.  Should look into this.
    fudge_factor = 2.5
    allowed_diff = max_output_dev * fudge_factor
    # But sometimes by chance it will be bigger
    for i in range(latency):
        await triggers.RisingEdge(dut.clk)
    while True:
        await triggers.ReadOnly()
        a, b, t = sent_queue.popleft()
        bt = b * t
        c = a + bt
        d = a - bt
        o_c = conversions.complex_from_slv(int(dut.o_c.value), width+2)
        o_d = conversions.complex_from_slv(int(dut.o_d.value), width+2)
        # Remove the scaling by two that we did.
        o_c = o_c*2
        o_d = o_d*2
        assert abs(c - o_c) < allowed_diff
        assert abs(d - o_d) < allowed_diff
        await triggers.RisingEdge(dut.clk)


def get_latency(generics):
    latency = (
        generics['mult_latency'] +
        sum(generics['reg_{}'.format(x)]
            for x in ('i_p', 'q_r', 'r_s', 's_o')))
    return latency


@cocotb.test()
async def butterfly_test(dut):
    test_params = helper.get_test_params()
    seed = test_params['seed']
    generics = test_params['generics']
    width = generics['width']
    latency = get_latency(generics)
    rnd = Random(seed)
    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())
    await triggers.RisingEdge(dut.clk)
    sent_queue = collections.deque()
    cocotb.fork(send_data(rnd, dut, width, sent_queue))
    cocotb.fork(check_data(dut, width, sent_queue, latency))
    for i in range(test_params['n_data'] + latency):
        await triggers.RisingEdge(dut.clk)


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 2391
        rnd = Random(seed)
        width = rnd.randint(4, 16)*2
        generics = {
            'width': width,
            'twiddle_width': width,
            'mult_latency': rnd.randint(1, 4),
            'reg_i_p': rnd.choice([True, False]),
            'reg_q_r': rnd.choice([True, False]),
            'reg_r_s': rnd.choice([True, False]),
            'reg_s_o': rnd.choice([True, False]),
            }
        test_params = {
            'test_index': test_index,
            'n_data': 100,
            'seed': seed,
            'core_name': 'butterfly',
            'top_name': 'butterfly',
            'test_module_name': 'test_butterfly',
            'generics': generics,
            }
        yield test_params


def run_test(test_params, wave=False):
    working_directory = os.path.abspath(os.path.join(
        'temp', 'test_butterfly_{}'.format(test_params['test_index'])))
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
        run_test(test_params, wave=True)


if __name__ == '__main__':
    run_tests(n_tests=1, base_seed=0)
