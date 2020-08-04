FROM quay.io/powercloud/ibm-cloud:latest

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev qemu-utils \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY . /usr/local/bin/
