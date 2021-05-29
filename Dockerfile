FROM python:3.8.3-slim

RUN apt-get update --fix-missing
RUN apt-get install -y git
RUN apt-get install -y clang
RUN apt-get install -y gnat zlib1g-dev
RUN apt-get install -y make gcc libedit-dev
RUN apt-get install -y g++

# Install ghdl
RUN git clone --depth 1 https://github.com/ghdl/ghdl.git ghdl
RUN mkdir ghdl/build
RUN cd ghdl/build && ../configure && make && make install

RUN pip install --upgrade pip
ADD . ./project
RUN pip install -e ./project