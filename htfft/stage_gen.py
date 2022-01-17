import os

import jinja2
from fusesoc.capi2.generator import Generator

from htfft import helper, conversions, htfft_gen

basedir = os.path.abspath(os.path.dirname(__file__))


def generate_stage(n, size, width, suffix, pipelines=None, make_pipeline_pkg=False):
    assert size == pow(2, helper.logceil(size))

    twiddle_batches = []
    batch_size = size//2
    for batch_index in range(n//size):
        base_index = batch_index * batch_size
        twiddles = [conversions.int_to_str(conversions.complex_to_slv(
            helper.get_twiddle(base_index+index, n), width), width)
                    for index in range(batch_size)]
        twiddle_batches.append(twiddles)
    params = {
        'n': n,
        'size': size,
        'width': width,
        'suffix': suffix,
        'twiddle_batches': twiddle_batches,
        }
    template_filename = os.path.join(basedir, 'stage.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    output_filename = 'stage_{}{}.vhd'.format(n, suffix)
    with open(output_filename, 'w') as g:
        g.write(formatted_text)

    if make_pipeline_pkg:
        extra_filenames = [htfft_gen.make_pipeline_pkg(suffix, pipelines)]
    else:
        extra_filenames = []

    return extra_filenames + [output_filename]


class StageGenerator(Generator):

    def run(self):
        output_filenames = generate_stage(
            n=self.config['n'],
            size=self.config['size'],
            width=self.config['width'],
            suffix=self.config['suffix'],
            pipelines=self.config.get('pipelines', None),
            make_pipeline_pkg=self.config.get('make_pipeline_pkg', False),
            )
        self.add_files(output_filenames, file_type='vhdlSource')


def make_stage_core(directory, suffix, n, size, width, pipelines):
    """
    Utility function for generating a core file from python.
    """
    params = {
        'suffix': suffix,
        'n': n,
        'size': size,
        'width': width,
        'pipelines': pipelines,
        'make_pipeline_pkg': True,
        }
    template_filename = os.path.join(basedir, 'stage.core.j2')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    top_filename = os.path.join(directory, 'stage_{}{}.core'.format(n, suffix))
    with open(top_filename, 'w') as g:
        g.write(formatted_text)


if __name__ == '__main__':
    g = StageGenerator()
    g.run()
    g.write()
