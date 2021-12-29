FROM python:3.8

WORKDIR /

RUN mkdir /shared
COPY *.py /
COPY shared/*.py /shared/

EXPOSE 4000

CMD python3 ae_server.py
