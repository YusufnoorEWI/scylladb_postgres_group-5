FROM python:3.8-slim-buster

ENV DB_HOST "scylla_order"
ENV USERS_SERVICE "users_service"
ENV STOCK_SERVICE "stock_service"
ENV PAYMENT_SERVICE "payment_service"
ENV DATABASE_TYPE "scylla"

COPY . /order_service

WORKDIR /order_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--bind", "0.0.0.0:80", "service:app"]
