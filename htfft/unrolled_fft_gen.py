import os

import jinja2
from fusesoc.capi2.generator import Generator

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


def generate_unrolled_fft_inner(size, input_width, twiddle_width, suffix):
    assert size == pow(2, helper.logceil(size))

    if size > 2:
        smaller_filenames = generate_unrolled_fft_inner(size//2, input_width, twiddle_width, suffix)
    else:
        smaller_filenames = []

    # Increasing the twiddle width with the other butterfly inputs.
    # Doesn't seem to help much, but probably worth doing.
    used_twiddle_width = twiddle_width + 2*(helper.logceil(size)-1)

    twiddles = [conversions.int_to_str(conversions.complex_to_slv(
        helper.get_twiddle(position, size), used_twiddle_width), used_twiddle_width)
                for position in range(size//2)]
    params = {
        'size': size,
        'input_width': input_width,
        'twiddle_width': used_twiddle_width,
        'suffix': suffix,
        'logceil_size': helper.logceil(size),
        'twiddles': twiddles,
        }
    template_filename = os.path.join(basedir, 'unrolled_fft_inner.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    output_filename = 'unrolled_fft_inner_{}{}.vhd'.format(size, suffix)
    with open(output_filename, 'w') as g:
        g.write(formatted_text)
    return smaller_filenames + [output_filename]


def generate_unrolled_fft(size, input_width, twiddle_width, suffix):
    filenames = generate_unrolled_fft_inner(size, input_width, twiddle_width, suffix)
    with open(os.path.join(basedir, 'unrolled_fft.vhd')) as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    params = {
        'size': size,
        'logceil_size': helper.logceil(size),
        'input_width': input_width,
        'suffix': suffix,
        }
    formatted_text = template.render(**params)
    output_filename = 'unrolled_fft_{}{}.vhd'.format(size, suffix)
    with open(output_filename, 'w') as g:
        g.write(formatted_text)
    return filenames + [output_filename]


class UnrolledFFTGenerator(Generator):

    def run(self):
        output_filenames = generate_unrolled_fft(
            size=self.config['size'],
            input_width=self.config['input_width'],
            twiddle_width=self.config['twiddle_width'],
            suffix=self.config['suffix'],
            )
        self.add_files(output_filenames, file_type='vhdlSource')


if __name__ == '__main__':
    g = UnrolledFFTGenerator()
    g.run()
    g.write()
