FROM python:3.12-alpine

# Install system dependencies for REST API
RUN apk add --no-cache \
    py3-flask \
    py3-gunicorn

# Install Python MySQL connector
RUN pip install --no-cache-dir \
    mysql-connector-python \
    PyMySQL \
    sqlalchemy

WORKDIR /app
COPY . .

# This needs to change to gunicorn or nginx
CMD ["python", "rest_api.py"]