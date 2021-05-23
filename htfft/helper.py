import os
import math
import cmath
import subprocess

import yaml
from cocotb_test.run import run

basedir = os.path.abspath(os.path.dirname(__file__))


def logceil(argument):
    if argument < 2:
        value = 0
    else:
        value = int(math.ceil(math.log(argument)/math.log(2)))
    return value


def get_twiddle(position, size):
    twiddle = cmath.exp(-2*math.pi*(0+1j)*((position % size)/size))
    return twiddle


def reverse_bits(value, n_bits):
    bits = bin(value)[2:]
    bits = '0' * (n_bits - len(bits)) + bits
    bits = ''.join(list(reversed(bits)))
    new_value = int(bits, 2)
    return new_value


def random_complex(rnd, width):
    """
    Get a random complex number with amplitude less than or
    equal to 1.
    We pass the width so we can choose a number that is exactly
    represented with that width.
    """
    while True:
        max_mag = pow(2, width//2 - 2)
        real_int = rnd.randint(-max_mag, max_mag)
        imag_int = rnd.randint(-max_mag, max_mag)
        comp = (real_int/max_mag + (0+1j)*imag_int/max_mag)
        if abs(comp) <= 1:
            break
    return comp


def get_files(core_name, working_directory, verbose=False, config_filename=None):
    cmd = ['fusesoc']
    if verbose:
        cmd += ['--verbose']
    if config_filename:
        cmd += ['--config', config_filename]
    tool = 'vivado'
    cores_root = basedir
    cmd += ['--cores-root', cores_root, 'run', '--target', 'default',
            '--tool', tool, '--setup', core_name]
    print(' '.join(cmd))
    subprocess.call(cmd, cwd=working_directory)
    output_dir = os.path.join(
        working_directory, 'build', '{}_0'.format(core_name), 'default-vivado')
    #if not os.path.exists(output_dir):
    #    output_dir = os.path.join(
    #        working_directory, 'build', '{}_0'.format(core_name), 'bld-vivado')
    yaml_filename = os.path.join(output_dir, '{}_0.eda.yml'.format(core_name))
    with open(yaml_filename, 'r') as f:
        data = yaml.load(f.read(), Loader=yaml.Loader)
    base_filenames = [f['name'] for f in data['files']]
    filenames = [f if f[0] == '/' else
                 os.path.abspath(os.path.join(output_dir, f)) for f in base_filenames]
    return filenames


def run_core(working_directory, core_name, top_name, test_module_name,
             wave=False, generics=None, extra_env=None):
    filenames = get_files(core_name, working_directory, verbose=True)
    run_with_cocotb(working_directory, filenames, top_name, test_module_name,
                    wave, generics, extra_env=extra_env)


def run_with_cocotb(working_directory, filenames, top_name, test_module_name, wave=False,
                    generics={}, extra_env={}):
    os.environ['SIM'] = 'ghdl'
    if wave:
        simulation_args = ['--wave=dump.ghw']
    else:
        simulation_args = []
    if generics:
        for key, value in generics.items():
            simulation_args.append('-g{}={}'.format(key, value))
    pwd = os.getcwd()
    os.chdir(working_directory)
    run(
        vhdl_sources=filenames,
        sim_args=simulation_args,
        toplevel=top_name,
        module=test_module_name,
        extra_env=extra_env,
        )
    os.chdir(pwd)
