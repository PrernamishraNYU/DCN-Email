FROM python:3.8

WORKDIR /

RUN mkdir /shared
COPY *.py /
COPY shared/*.py /shared/

RUN pip install Flask

EXPOSE 8080

ENV FLASK_APP=au_http_server.py

CMD flask run -h 0.0.0.0 -p 8080
