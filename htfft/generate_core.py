import os
import argparse
import shutil

from htfft import htfft_gen, helper

def make_barrel_shifter_pipeline(spcc):
    # This should create a barrelshifter with two logic levels
    # between pipeline stages.  (1000100010...)
    pipeline = ['0'] * (helper.logceil(spcc) + 1)
    for index in range(len(pipeline)):
        if index % 4 == 0:
            pipeline[index] = '1'
    return ''.join(pipeline)

def generate_core(n, spcc, width):
    suffix = '_n{}_spcc{}_width{}'.format(n, spcc, width)
    core_name = 'htfft{}'.format(suffix)
    directory = os.path.abspath('htfft{}'.format(suffix))
    os.makedirs(directory)
    # Make the core file that fusesoc will find and use.
    pipelines = {
        'barrel_shifter': make_barrel_shifter_pipeline(spcc),
        'butterfly': {
            'mult_latency': 3,
            'reg_i_p': True,
            'reg_q_r': True,
            'reg_r_s': True,
            'reg_s_o': True,
            },
        'stage': {
            'reg_fromread_buffered': True,
            'reg_buffered_tobutterfly': True,
            },
        'reg_s_': True,
        }
    htfft_gen.make_htfft_core(directory, suffix, n, spcc, width, pipelines)
    filenames = helper.get_files(core_name, directory, verbose=False, config_filename=None)
    for filename in filenames:
        shutil.copy2(filename, os.path.join(directory, os.path.basename(filename)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', dest='n', type=int, required=True)
    parser.add_argument('--spcc', dest='spcc', type=int, required=True)
    parser.add_argument('--width', dest='width', type=int, required=True)
    args = parser.parse_args()
    generate_core(n=args.n, spcc=args.spcc, width=args.width)

if __name__ == '__main__':
    main()
