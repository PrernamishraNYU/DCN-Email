FROM python:3.8

WORKDIR /

RUN mkdir /shared
COPY *.py /
COPY shared/*.py /shared/

EXPOSE 5000

CMD python3 dual_server.py
