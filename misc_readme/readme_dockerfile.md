Based on your docker run command and setup steps, here's a Dockerfile that builds a container image with the `squishy_REST_API` package included:

```dockerfile
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    PyMySQL \
    sqlalchemy \
    cryptography \
    flask \
    gunicorn \
    requests

# Copy the squishy_REST_API package into the container
COPY squishy_REST_API/ /app/squishy_REST_API/

# Copy gunicorn configuration file
COPY gunicorn.conf.py /app/

# Set environment variables with default values
ENV LOCAL_MYSQL_NAME=local_squishy_db
ENV LOCAL_USER=squishy
ENV LOCAL_PASSWORD=squishy
ENV LOCAL_DATABASE=local_squishy_db
ENV LOCAL_PORT=5000

# Expose the port
EXPOSE 5000

# Create baseline directory for mounting
RUN mkdir -p /baseline

# Set the default command
CMD ["gunicorn", "squishy_REST_API.main:app", "-c", "gunicorn.conf.py"]
```

With this Dockerfile, you can build the image:

```bash
docker build -t squishy-rest-api .
```

And then run it much more simply:

```bash
docker run -it --rm \
  --name restapi \
  --network DB-net \
  -p 80:5000 \
  -v /baseline:/baseline \
  squishy-rest-api
```

**Key changes from your original approach:**

1. **Dependencies pre-installed**: All Python packages are installed during the build process
2. **Code included**: The `squishy_REST_API` package is copied into the image
3. **Default environment variables**: Set in the Dockerfile but can still be overridden at runtime
4. **Automatic startup**: The container starts the gunicorn server automatically
5. **Only /baseline needs mounting**: The application code is now part of the image

**Optional: Multi-stage build for smaller image**

If you want a smaller final image, you could use a multi-stage build:

```dockerfile
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

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API/ /app/squishy_REST_API/
COPY gunicorn.conf.py /app/

# Set environment variables
ENV LOCAL_MYSQL_NAME=local_squishy_db
ENV LOCAL_USER=squishy
ENV LOCAL_PASSWORD=squishy
ENV LOCAL_DATABASE=local_squishy_db
ENV LOCAL_PORT=5000

# Expose port and create baseline directory
EXPOSE 5000
RUN mkdir -p /baseline

# Start the application
CMD ["gunicorn", "squishy_REST_API.main:app", "-c", "gunicorn.conf.py"]
```