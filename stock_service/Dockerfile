FROM python:3.8-slim-buster

ENV DB_HOST "172.17.0.2"

COPY . /stock_service

WORKDIR /stock_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--bind", "0.0.0.0:8000", "service:app"]