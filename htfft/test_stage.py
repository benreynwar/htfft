import os
import collections
import shutil
import itertools
from random import Random

import pytest
import cocotb
from cocotb import clock, triggers

from htfft import helper, conversions
import stage_gen

basedir = os.path.abspath(os.path.dirname(__file__))


async def send_input(rnd, dut, N, size, width, sent_queue):
    dut.i_reset = 1
    await triggers.RisingEdge(dut.clk)
    while True:
        pause_after = rnd.randint(0, 10)
        values = [helper.random_complex(rnd, width) for i in range(N)]
        sent_queue.append(values)
        chunked_data = [values[index*size//2: (index+1)*size//2]
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
            if (pause_after == 0) and (input_index == L-1):
                dut.i_reset <= 1
            await triggers.RisingEdge(dut.clk)
        if pause_after > 0:
            for i in range(pause_after-1):
                await triggers.RisingEdge(dut.clk)
            dut.i_reset <= 1
            await triggers.RisingEdge(dut.clk)


async def check_output(dut, N, size, width, sent_queue, n_vectors):
    # Wait for the first o_reset 
    for index in itertools.count():
        await triggers.RisingEdge(dut.clk)
        await triggers.ReadOnly()
        if str(dut.o_reset.value) == '1':
            print('got it')
            break
        if index > 20:
            assert 'Never got output reset signal'
    for vector_index in itertools.count():
        if vector_index == n_vectors:
            break
        assert dut.o_reset.value.integer == 1
        received_vector = []
        for output_index in range(N//size):
            await triggers.RisingEdge(dut.clk)
            await triggers.ReadOnly()
            received_data_a = conversions.list_of_complex_from_slv(
                int(dut.o_data_a.value), width=width, size=size//2)
            received_data_a = [2 * x for x in received_data_a]
            received_data_b = conversions.list_of_complex_from_slv(
                int(dut.o_data_b.value), width=width, size=size//2)
            received_data_b = [2 * x for x in received_data_b]
            received_vector.append((received_data_a, received_data_b))
            if output_index != N//size - 1:
                assert dut.o_reset.value.integer == 0
        input_data = sent_queue.popleft()
        compare_output(input_data, received_vector, N, size)
        while True:
            if dut.o_reset.value.integer == 1:
                break
            await triggers.RisingEdge(dut.clk)
            await triggers.ReadOnly()


async def compare_output(input_data, received_vector, N, size):
    expected_data = stage_model(input_data)
    chunked_data = [expected_data[index*size//2: (index+1)*size//2]
                    for index in range(2*N//size)]
    L = N//size
    assert len(received_vector) == L
    for output_index, (received_a, received_b) in enumerate(received_vector):
        expected_a = chunked_data[output_index]
        expected_b = chunked_data[output_index + L]
        check_equal(expected_a, received_a)
        check_equal(expected_b, received_b)


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
async def stage_test(dut):
    test_params = helper.get_test_params()
    seed = test_params['seed']
    rnd = Random(seed)
    n_vectors = 2

    cocotb.fork(clock.Clock(dut.clk, 2, 'ns').start())

    # Total FFT size
    N = int(dut.n.value)
    # Bits in one complex number
    width = int(dut.width.value)
    # Number of samples (complex numbers) received every clock cycle.
    size = int(dut.size.value)

    output_width = int(dut.output_width.value)
    sent_queue = collections.deque()

    cocotb.fork(send_input(
        rnd=rnd,
        dut=dut,
        N=N,
        size=size,
        width=width,
        sent_queue=sent_queue,
    ))
    cocotb.fork(check_output(
        dut=dut,
        N=N,
        size=size,
        width=output_width,
        sent_queue=sent_queue,
        n_vectors=n_vectors,
    ))


def get_test_params(n_tests, base_seed=0):
    for test_index in range(n_tests):
        seed = (base_seed + test_index) * 9247253
        rnd = Random(seed)
        suffix = '_{}_test'.format(test_index)
        n = rnd.choice([8, 16, 32, 64, 128, 256])
        possible_spcc = [spcc for spcc in (2, 4, 8, 16, 32)
                         if spcc < n]
        spcc = rnd.choice(possible_spcc)
        width = rnd.randint(4, 16)*2

        generation_params = {
            'suffix': suffix,
            'n': n,
            'size': spcc,
            'width': width,
            'twiddle_width': width,
            }
        n_vectors = 10
        test_params = {
            'n_vectors': n_vectors,
            'seed': seed,
            'core_name': 'stage_{}{}'.format(n, suffix),
            'top_name': 'stage_{}{}'.format(n, suffix),
            'test_module_name': 'test_stage',
            'generation': generation_params,
            }
        yield test_params


def run_test(test_params, wave=False):
    suffix = test_params['generation']['suffix']
    n = test_params['generation']['n']
    working_directory = os.path.abspath(
        os.path.join('temp', 'test_stage_{}{}'.format(n, suffix)))
    if os.path.exists(working_directory):
        shutil.rmtree(working_directory)
    os.makedirs(working_directory)
    generated_directory = os.path.join(basedir, 'generated')
    if not os.path.exists(generated_directory):
        os.makedirs(generated_directory)
    stage_gen.make_stage_core(directory=generated_directory, **test_params['generation'])
    helper.run_core(
        working_directory,
        core_name=test_params['core_name'],
        top_name=test_params['top_name'],
        test_module_name=test_params['test_module_name'],
        wave=wave,
        test_params=test_params)


@pytest.mark.parametrize('test_params', get_test_params(n_tests=10))
def test_stage(test_params):
    run_test(test_params, wave=False)


def run_tests(n_tests=10):
    for test_params in get_test_params(n_tests=n_tests):
        run_test(test_params, wave=False)


if __name__ == '__main__':
    run_tests()
