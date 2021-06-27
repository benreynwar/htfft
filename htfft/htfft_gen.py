import os

import jinja2
from fusesoc.capi2.generator import Generator

from htfft import helper, conversions, unrolled_fft_gen, stage_gen

basedir = os.path.abspath(os.path.dirname(__file__))


def generate_htfft(n, size, input_width, twiddle_width, suffix):
    assert size == pow(2, helper.logceil(size))
    assert n == pow(2, helper.logceil(n))

    output_width = 2*helper.logceil(n) + input_width

    unrolled_filenames = unrolled_fft_gen.generate_unrolled_fft_inner(
        size, input_width, twiddle_width, suffix)

    n_stages = helper.logceil(n//size)
    stage_filenames = []
    stage_ns = []
    for stage_index in range(n_stages):
        stage_n = size * pow(2, stage_index+1)
        stage_ns.append(stage_n)
        width = input_width + (helper.logceil(stage_n)-1)*2
        stage_filenames += stage_gen.generate_stage(stage_n, size, width, twiddle_width, suffix)

    params = {
        'n': n,
        'size': size,
        'input_width': input_width,
        'output_width': output_width,
        'suffix': suffix,
        'stage_ns': stage_ns,
        'n_stages': len(stage_ns),
        }
    template_filename = os.path.join(basedir, 'htfft.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    top_filename = 'htfft{}.vhd'.format(suffix)
    with open(top_filename, 'w') as g:
        g.write(formatted_text)
    return unrolled_filenames + stage_filenames + [top_filename]


class HTFFTGenerator(Generator):

    def run(self):
        output_filenames = generate_htfft(
            n=self.config['n'],
            size=self.config['size'],
            input_width=self.config['input_width'],
            twiddle_width=self.config['twiddle_width'],
            suffix=self.config['suffix'],
            )
        self.add_files(output_filenames, file_type='vhdlSource')


if __name__ == '__main__':
    g = HTFFTGenerator()
    g.run()
    g.write()
