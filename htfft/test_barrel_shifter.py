import os
import shutil
from random import Random
import collections

import pytest
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


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 4353453
        rnd = Random(seed)
        size = rnd.choice([8, 16, 32, 64, 128, 256])
        shift_increment = rnd.choice([3, 5, 8])
        pipeline = ''.join(rnd.choice(['0', '1'])
                           for i in range(helper.logceil(size)+1))
        generics = {
            'size': size,
            'shift_increment': shift_increment,
            'pipeline': pipeline,
            }
        n_data = 100
        test_params = {
            'test_index': test_index,
            'n_data': n_data,
            'seed': seed,
            'core_name': 'barrel_shifter',
            'top_name': 'barrel_shifter',
            'test_module_name': 'test_barrel_shifter',
            'generics': generics,
            }
        yield test_params


@cocotb.test()
async def barrel_shifter_test(dut):
    test_params = helper.get_test_params()
    generics = test_params['generics']
    rnd = Random(test_params['seed'])
    n_data = test_params['n_data']

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    shift_increment = generics['shift_increment']
    size = generics['size']
    pipeline = generics['pipeline']
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
    for i in range(n_data + pipeline_length):
        await triggers.RisingEdge(dut.clk)


def run_test(test_params, wave=False):
    working_directory = os.path.abspath(os.path.join(
        'temp', 'test_barrel_shifter_{}'.format(test_params['test_index'])))
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
