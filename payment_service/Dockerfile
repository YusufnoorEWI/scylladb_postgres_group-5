FROM python:3.8-slim-buster

ENV DB_HOST "scylla_payment"

COPY . /payment_service

WORKDIR /payment_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

EXPOSE 5000

CMD ["--bind", "0.0.0.0:5000", "service:app"]