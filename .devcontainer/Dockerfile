# This is a Dockerized build environment

FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Install compression and editor tools
RUN yum install -y tar gzip unzip vim nano

# Install Git
RUN yum install -y git

# Install Python 3.11
RUN yum install -y python3.11 python3.11-pip
# Alias python3.11 and pip3.11
RUN ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/pip3.11 /usr/bin/pip

# Install required dependencies
RUN yum update -y && \
    yum install -y yum-utils device-mapper-persistent-data lvm2

# Install Docker
RUN yum install docker -y

RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.7.1 python3 -
ENV PATH="${PATH}:/root/.local/bin"
RUN poetry install --with dev,lint,typing,test,test_integration

RUN yum install -y make
RUN yum update -y && \
    yum install -y gcc python3-devel \

WORKDIR langchain

# Set the default command to run bash
CMD ["/bin/bash"]
