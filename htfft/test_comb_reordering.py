import os
import shutil
from random import Random

import pytest
import cocotb
from cocotb import triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


@cocotb.test()
async def comb_reordering_test(dut):
    test_params = helper.get_test_params()
    seed = test_params['seed']
    n_data = test_params['n_data']
    rnd = Random(seed)
    size = int(dut.size.value)
    width = int(dut.width.value)

    max_value = pow(2, width)-1
    for i in range(n_data):
        await triggers.Timer(1e6)
        i_data = [rnd.randint(0, max_value) for i in range(size)]
        dut.i_data <= conversions.list_of_uints_to_slv(i_data, width)
        await triggers.ReadOnly()
        o_data = conversions.list_of_uints_from_slv(
            int(dut.o_data.value), width=width, size=size)
        for address in range(size):
            reversed_address = helper.reverse_bits(address, helper.logceil(size))
            assert i_data[address] == o_data[reversed_address]


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 284704
        rnd = Random(seed)
        generics = {
            'width': rnd.randint(2, 64),
            'size': rnd.choice([4, 8, 16, 32, 64, 128]),
            }
        test_params = {
            'test_index': test_index,
            'n_data': 100,
            'seed': seed,
            'core_name': 'comb_reordering',
            'top_name': 'comb_reordering',
            'test_module_name': 'test_comb_reordering',
            'generics': generics,
            }
        yield test_params


def run_test(test_params, wave=False):
    working_directory = os.path.abspath(os.path.join(
        'temp', 'test_comb_reordering_{}'.format(test_params['test_index'])))
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
    run_tests()
