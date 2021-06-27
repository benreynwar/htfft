import os
from setuptools import setup

this_directory = os.path.abspath(os.path.dirname(__file__))

setup(
    name="htfft",
    packages=['htfft'],
    use_scm_version={
        "relative_to": __file__,
        "write_to": "htfft/version.py",
    },
    setup_requires=['setuptools_scm'],
    author="Ben Reynwar",
    author_email="ben@reynwar.net",
    description=("Generation and testing of a VHDL FFT implementation"),
    license="MIT",
    keywords=["FFT", "VHDL", "FPGA"],
    url="https://github.com/benreynwar/htfft",
    install_requires=[
        'jinja2',
        'cocotb-test',
        'fusesoc',
        'numpy',
    ],
)
