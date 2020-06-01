FROM python:3.8-slim-buster

ENV DB_HOST "scylla_payment"

COPY . /payment_service

WORKDIR /payment_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--bind", "0.0.0.0:80", "service:app"]
