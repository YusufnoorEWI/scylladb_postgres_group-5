FROM python:3.8-slim-buster

COPY . /order_service

WORKDIR /order_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--bind", "0.0.0.0:80", "service:app"]
