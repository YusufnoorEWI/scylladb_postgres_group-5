FROM python:3.8-slim-buster

COPY . /stock_service

WORKDIR /stock_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["service:app"]