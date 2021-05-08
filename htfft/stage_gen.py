import os

import jinja2
from fusesoc.capi2.generator import Generator

from htfft import helper, conversions

basedir = os.path.abspath(os.path.dirname(__file__))


def generate_stage(n, size, width, twiddle_width, suffix):
    assert size == pow(2, helper.logceil(size))

    twiddle_batches = [[
        conversions.int_to_str(conversions.complex_to_slv(
            helper.get_twiddle(position, n), twiddle_width), twiddle_width)
                for position in range(base, base+size//2)]
                       for base in range(0, n//size)]
    params = {
        'n': n,
        'size': size,
        'width': width,
        'twiddle_width': twiddle_width,
        'suffix': suffix,
        'twiddle_batches': twiddle_batches,
        }
    template_filename = os.path.join(basedir, 'stage.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    output_filename = 'stage_{}{}.vhd'.format(size, suffix)
    with open(output_filename, 'w') as g:
        g.write(formatted_text)
    return [output_filename]


class StageGenerator(Generator):

    def run(self):
        output_filenames = generate_stage(
            n=self.config['n'],
            size=self.config['size'],
            width=self.config['width'],
            twiddle_width=self.config['twiddle_width'],
            suffix=self.config['suffix'],
            )
        self.add_files(output_filenames, file_type='vhdlSource')


if __name__ == '__main__':
    g = StageGenerator()
    g.run()
    g.write()
