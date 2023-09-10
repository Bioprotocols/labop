FROM ubuntu:20.04

RUN apt update && apt install -y --no-install-recommends \
    # autoconf \
    # automake \
    # bison \
    # cmake \
    # curl \
    # flex \
    # g++ \
    # gcc \
    git \
    # libtool \
    # m4 \
    # make \
    # ninja-build \
    # patch \
    graphviz \
    pkg-config \
    python-is-python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root
SHELL ["/bin/bash", "-c"]
RUN git clone \
    --depth 1 \
    --branch ecl \
    https://github.com/Bioprotocols/labop.git

RUN python -mvenv labop_venv
RUN source labop_venv/bin/activate
RUN pip install ./labop
RUN pip install IPython
RUN mkdir -p /root/home
WORKDIR /root/home

ENV PROTOCOL_SCRIPT ""

CMD python ${PROTOCOL_SCRIPT}
