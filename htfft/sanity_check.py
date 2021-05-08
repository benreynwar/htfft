"""
Just a sanity check to make sure I know how a FFT works.
"""
import math
import cmath
from random import Random

from numpy import fft

from htfft import helper


def builtin(values):
    ffted = fft.fft(values)


def butterfly(a, b, twiddle_factor):
    bt = b * twiddle_factor
    return (a + bt, a - bt)


def initial_reorder(values):
    N = len(values)
    n_bits = len(bin(N)) - 3
    assert pow(2, n_bits) == N
    new_values = [None] * N
    for address, value in enumerate(values):
        new_address = helper.reverse_bits(address, n_bits)
        new_values[new_address] = value
    assert None not in new_values
    return new_values


def stage(stage_index, values):
    N = len(values)
    new_values = [None] * N
    size = pow(2, stage_index) * 2
    n_lumps = N//size
    for outer_index in range(n_lumps):
        for inner_index in range(size//2):
            first_index = outer_index * size + inner_index
            second_index = first_index + pow(2, stage_index)
            twiddle_factor = cmath.exp(-2*math.pi*(0+1j)*((first_index % size)/size))
            c, d = butterfly(values[first_index], values[second_index], twiddle_factor)
            new_values[first_index] = c
            new_values[second_index] = d
    assert None not in new_values
    return new_values


def my_fft(values):
    values = initial_reorder(values)
    N = len(values)
    n_levels = len(bin(N)) - 3
    for stage_index in range(n_levels):
        values = stage(stage_index, values)
    return values


if __name__ == '__main__':
    n = 4
    seed = 0
    rnd = Random(seed)
    #values = [rnd.random() * 2 - 1 for i in range(n)]
    #values = [1, -1, 1, -1, 1, -1, 1, -1]
    values = [1, 0, 1, 0]
    expected = fft.fft(values)
    received = my_fft(values)
    diff = sum(abs(a - b) for a, b in zip(expected, received))
    print(expected)
    print(received)
    assert diff < 1e-6
