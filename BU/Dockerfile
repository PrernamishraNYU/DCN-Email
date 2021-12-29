FROM python:3.8

WORKDIR /

RUN mkdir /shared
COPY *.py /
COPY shared/*.py /shared/

RUN pip install Flask

EXPOSE 8081

ENV FLASK_APP=bu_http_server.py

CMD flask run -h 0.0.0.0 -p 8081
