import os

import jinja2
from fusesoc.capi2.generator import Generator

from htfft import helper, unrolled_fft_gen, stage_gen

basedir = os.path.abspath(os.path.dirname(__file__))


def random_pipeline(rnd, spcc):
    pipelines = {
        'barrel_shifter': ''.join(rnd.choice(('0', '1')) for i in range(helper.logceil(spcc)+1)),
        'butterfly': {
            'mult_latency': rnd.randint(1, 4),
            'reg_i_p': rnd.choice([True, False]),
            'reg_q_r': rnd.choice([True, False]),
            'reg_r_s': rnd.choice([True, False]),
            'reg_s_o': rnd.choice([True, False]),
            },
        'stage': {
            'reg_fromread_buffered': rnd.choice([True, False]),
            'reg_buffered_tobutterfly': rnd.choice([True, False]),
            },
        'reg_s_': rnd.choice([True, False]),
        }
    return pipelines


def make_pipeline_pkg(suffix, pipelines):
    pipeline_template = os.path.join(basedir, 'htfft_pipeline.vhd')
    with open(pipeline_template, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(suffix=suffix, pipelines=pipelines)
    pipeline_filename = 'htfft{}_pipeline.vhd'.format(suffix)
    with open(pipeline_filename, 'w') as g:
        g.write(formatted_text)
    return pipeline_filename


def generate_htfft(n, spcc, input_width, suffix, pipelines):
    assert spcc == pow(2, helper.logceil(spcc))
    assert n == pow(2, helper.logceil(n))

    output_width = 2*helper.logceil(n) + input_width

    unrolled_filenames = unrolled_fft_gen.generate_unrolled_fft_inner(
        spcc, input_width, suffix)

    n_stages = helper.logceil(n//spcc)
    stage_filenames = []
    stage_ns = []
    for stage_index in range(n_stages):
        stage_n = spcc * pow(2, stage_index+1)
        stage_ns.append(stage_n)
        width = input_width + (helper.logceil(stage_n)-1)*2
        stage_filenames += stage_gen.generate_stage(stage_n, spcc, width, suffix)

    params = {
        'n': n,
        'spcc': spcc,
        'input_width': input_width,
        'output_width': output_width,
        'suffix': suffix,
        'stage_ns': stage_ns,
        'n_stages': len(stage_ns),
        'pipelines': pipelines,
        }

    template_filename = os.path.join(basedir, 'htfft.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    top_filename = 'htfft{}.vhd'.format(suffix)
    with open(top_filename, 'w') as g:
        g.write(formatted_text)

    template_filename = os.path.join(basedir, 'htfft_params.vhd')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    params_filename = 'htfft{}_params.vhd'.format(suffix)
    with open(params_filename, 'w') as g:
        g.write(formatted_text)

    pipeline_filename = make_pipeline_pkg(suffix, pipelines)

    return [params_filename, pipeline_filename] + unrolled_filenames + stage_filenames + [top_filename]


class HTFFTGenerator(Generator):

    def run(self):
        output_filenames = generate_htfft(
            n=self.config['n'],
            spcc=self.config['spcc'],
            input_width=self.config['input_width'],
            suffix=self.config['suffix'],
            pipelines=self.config['pipelines'],
            )
        self.add_files(output_filenames, file_type='vhdlSource')


def make_htfft_core(directory, suffix, n, spcc, input_width, pipelines):
    """
    Utility function for generating a core file from python.
    """
    params = {
        'suffix': suffix,
        'n': n,
        'spcc': spcc,
        'input_width': input_width,
        'pipelines': pipelines,
        }
    template_filename = os.path.join(basedir, 'htfft.core.j2')
    with open(template_filename, 'r') as f:
        template_text = f.read()
        template = jinja2.Template(template_text)
    formatted_text = template.render(**params)
    top_filename = os.path.join(directory, 'htfft{}.core'.format(suffix))
    with open(top_filename, 'w') as g:
        g.write(formatted_text)


if __name__ == '__main__':
    g = HTFFTGenerator()
    g.run()
    g.write()
