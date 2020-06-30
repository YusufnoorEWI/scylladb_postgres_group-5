FROM python:3.8-slim-buster

COPY . /stock_service

WORKDIR /stock_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--worker-class", "gevent", "--worker-connections", "5", "--bind", "0.0.0.0:80", "service:app"]
