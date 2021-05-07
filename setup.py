import os
from setuptools import setup

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = "htfft",
    packages=['htfft'],
    use_scm_version = {
        "relative_to": __file__,
        "write_to": "htfft/version.py",
    },
    setup_requires=['setuptools_scm'],
    author = "Ben Reynwar",
    author_email = "ben@reynwar.net",
    description = ("Generation and testing of a VHDL FFT implementation"),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license = "MIT",
    keywords = ["FFT", "VHDL", "FPGA"],
    url = "https://github.com/benreynwar/htfft",
    install_requires=[
        'jinja2',
        'cocotb-test',
        'fusesoc',
    ],
)
