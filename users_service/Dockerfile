FROM python:3.8-slim-buster

COPY . /users_service

WORKDIR /users_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--worker-class", "gevent", "--worker-connections", "1000", "--bind", "0.0.0.0:80", "service:app"]
