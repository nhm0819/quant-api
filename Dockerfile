FROM python:3.11-slim-buster

COPY requirements.txt /app/quant-api/requirements.txt
RUN pip install -r /app/quant-api/requirements.txt

COPY ../.. /app/quant-api
WORKDIR /app/quant-api

CMD ["sh", "-c", "gunicorn quant_api.apps.v1:app -c gunicorn.conf.py"]
