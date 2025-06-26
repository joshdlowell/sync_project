FROM python:3.12-alpine as builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    PyMySQL \
    sqlalchemy \
    cryptography \
    flask \
    gunicorn \
    requests

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app/squishy_REST_API/

# Set environment variables
ENV LOCAL_DB_TYPE=mysql
ENV LOCAL_MYSQL_HOST=mysql-squishy-db
ENV LOCAL_MYSQL_DATABASE=squishy_db
ENV LOCAL_MYSQL_PORT=3306
ENV API_HOST=0.0.0.0
ENV API_PORT=5000
ENV DEBUG=False
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]