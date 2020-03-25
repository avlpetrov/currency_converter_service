FROM python:3.8.2-alpine

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /currency_converter_service

COPY poetry.lock pyproject.toml ./

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev libressl-dev alpine-sdk \
    && pip install poetry==1.0.* \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev \
    && apk del .build-deps gcc musl-dev libffi-dev libressl-dev alpine-sdk

COPY . ./

CMD gunicorn -b 0.0.0.0:8000 \
    currency_converter_service.main:app \
    -w 16 -k uvicorn.workers.UvicornWorker
