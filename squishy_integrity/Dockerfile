FROM python:3.12-alpine as builder

# Install build dependencies
RUN #apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests


FROM python:3.12-alpine
LABEL authors="jdlowel"

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app/squishy_integrity/

# Set environment variables
ENV REST_API_HOST=squishy-rest-api
ENV REST_API_PORT=5000
ENV BASELINE="/baseline"
ENV DEBUG=False
ENV LOG_LEVEL=INFO

# Create baseline directory
RUN mkdir -p /baseline

## Start the application using the runnable package
CMD ["python", "-m", "squishy_integrity"]