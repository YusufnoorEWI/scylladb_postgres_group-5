FROM python:3.8-slim-buster

COPY . /payment_service

WORKDIR /payment_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--worker-class", "gevent", "--worker-connections", "1000", "--bind", "0.0.0.0:80", "service:app"]
