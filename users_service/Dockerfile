FROM python:3.8-slim-buster

ENV DATABASE_TYPE "scylla"
ENV DB_HOST "scylla_users"
ENV DATABASE_TYPE "scylla"

COPY . /users_service

WORKDIR /users_service

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn"]

CMD ["--bind", "0.0.0.0:80", "service:app"]
