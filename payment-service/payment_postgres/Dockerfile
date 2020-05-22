FROM python:3.8-slim

WORKDIR /home/app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# t: timeout
# w: #processes
# threads: # threads
CMD gunicorn -b 0.0.0.0:5000 payment_service:app -t 1 -w 1 --threads 1