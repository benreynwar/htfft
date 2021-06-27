import os
from random import Random

import cocotb
from cocotb import triggers

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


@cocotb.test()
async def test_comb_reordering(dut):
    seed = 0
    rnd = Random(seed)
    size = int(dut.size.value)
    width = int(dut.width.value)

    max_value = pow(2, width)-1
    for i in range(100):
        await triggers.Timer(1000)
        i_data = [rnd.randint(0, max_value) for i in range(size)]
        dut.i_data <= conversions.list_of_uints_to_slv(i_data, width)
        await triggers.ReadOnly()
        o_data = conversions.list_of_uints_from_slv(
            int(dut.o_data.value), width=width, size=size)
        for address in range(size):
            reversed_address = helper.reverse_bits(address, helper.logceil(size))
            assert i_data[address] == o_data[reversed_address]


def main():
    working_directory = os.path.abspath('temp_comb_reordering')
    os.makedirs(working_directory)
    core_name = 'comb_reordering'
    top_name = 'comb_reordering'
    test_module_name = 'test_comb_reordering'
    wave = True
    generics = {
        'width': 10,
        'size': 8,
        }
    helper.run_core(working_directory, core_name, top_name, test_module_name,
                    wave=wave, generics=generics)


if __name__ == '__main__':
    main()
