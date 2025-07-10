To modify your Dockerfile to meet the requirements for installing `pyodbc` and the ODBC Driver 17 for SQL Server, here's the updated version:

```dockerfile
FROM python:3.12-alpine AS builder

# Install build dependencies including those needed for pyodbc and ODBC driver
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    unixodbc-dev \
    g++ \
    make

# Install Microsoft ODBC Driver 17 for SQL Server
RUN apk add --no-cache curl gnupg && \
    curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
    curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.10.1.1-1_amd64.apk && \
    apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
    apk add --allow-untrusted mssql-tools_17.10.1.1-1_amd64.apk

# Install Python dependencies including pyodbc
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Install runtime dependencies for ODBC
RUN apk add --no-cache \
    unixodbc \
    curl \
    gnupg

# Install Microsoft ODBC Driver 17 for SQL Server in final image
RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
    curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.10.1.1-1_amd64.apk && \
    apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
    apk add --allow-untrusted mssql-tools_17.10.1.1-1_amd64.apk && \
    rm -f msodbcsql17_17.10.5.1-1_amd64.apk mssql-tools_17.10.1.1-1_amd64.apk

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Set environment variables
# All non-required env vars are running v2 defaults

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

### Key changes made:

1. **Added build dependencies**: Added `unixodbc-dev`, `g++`, and `make` to the builder stage for compiling pyodbc.

2. **Added pyodbc**: Included `pyodbc` in the pip install command in the builder stage.

3. **Installed ODBC Driver 17**: Added installation of Microsoft ODBC Driver 17 for SQL Server in both the builder and final stages.

4. **Runtime dependencies**: Added `unixodbc` to the final image as it's required at runtime.

### Alternative approach using Debian-based image:

If you encounter issues with the Alpine-based approach, you might consider switching to a Debian-based image which can be easier for ODBC driver installation:

```dockerfile
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-slim
LABEL authors="jdlowel"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    unixodbc \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

The Debian-based approach is often more straightforward for ODBC driver installation, but the Alpine version should work as well with the proper dependencies installed.

If you have the RPM for the ODBC driver locally, you'll need to modify your approach since Alpine Linux uses `apk` and doesn't natively support RPM packages. Here are two solutions:

## Option 1: Switch to a Red Hat-based image (Recommended)

Since you have an RPM, it's better to use a Red Hat-based image that natively supports RPM packages:

```dockerfile
FROM registry.access.redhat.com/ubi8/python-39 AS builder

# Switch to root to install packages
USER root

# Install build dependencies
RUN dnf install -y \
    gcc \
    gcc-c++ \
    unixODBC-devel \
    make \
    && dnf clean all

# Copy and install the local ODBC driver RPM
COPY path/to/your/odbc-driver.rpm /tmp/
RUN rpm -ivh /tmp/odbc-driver.rpm

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM registry.access.redhat.com/ubi8/python-39
LABEL authors="jdlowel"

# Switch to root to install packages
USER root

# Install runtime dependencies
RUN dnf install -y \
    unixODBC \
    && dnf clean all

# Copy and install the local ODBC driver RPM
COPY path/to/your/odbc-driver.rpm /tmp/
RUN rpm -ivh /tmp/odbc-driver.rpm && rm -f /tmp/odbc-driver.rpm

# Copy installed packages from builder
COPY --from=builder /opt/app-root/lib/python3.9/site-packages /opt/app-root/lib/python3.9/site-packages
COPY --from=builder /opt/app-root/bin /opt/app-root/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Switch back to default user
USER 1001

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

## Option 2: Use CentOS/Rocky Linux base image

```dockerfile
FROM python:3.12-slim AS temp-extractor

# Install rpm2cpio to extract RPM contents
RUN apt-get update && apt-get install -y rpm2cpio cpio && rm -rf /var/lib/apt/lists/*

# Copy and extract RPM contents
COPY path/to/your/odbc-driver.rpm /tmp/
WORKDIR /tmp
RUN rpm2cpio odbc-driver.rpm | cpio -idmv

FROM centos:8 AS builder

# Install build dependencies
RUN dnf install -y \
    python3 \
    python3-pip \
    gcc \
    gcc-c++ \
    unixODBC-devel \
    make \
    && dnf clean all

# Copy and install the local ODBC driver RPM
COPY path/to/your/odbc-driver.rpm /tmp/
RUN rpm -ivh /tmp/odbc-driver.rpm

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM centos:8
LABEL authors="jdlowel"

# Install runtime dependencies
RUN dnf install -y \
    python3 \
    unixODBC \
    && dnf clean all

# Copy and install the local ODBC driver RPM
COPY path/to/your/odbc-driver.rpm /tmp/
RUN rpm -ivh /tmp/odbc-driver.rpm && rm -f /tmp/odbc-driver.rpm

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python3", "-m", "squishy_REST_API"]
```

## Option 3: Extract RPM contents manually (if you must use Alpine)

If you absolutely need to stick with Alpine, you can extract the RPM contents manually:

```dockerfile
FROM alpine:latest AS rpm-extractor

# Install rpm2cpio to extract RPM contents
RUN apk add --no-cache rpm2cpio

# Copy and extract RPM contents
COPY path/to/your/odbc-driver.rpm /tmp/
WORKDIR /tmp
RUN rpm2cpio odbc-driver.rpm | cpio -idmv

FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    unixodbc-dev \
    g++ \
    make

# Copy extracted ODBC driver files from rpm-extractor
COPY --from=rpm-extractor /tmp/opt/microsoft/msodbcsql17/ /opt/microsoft/msodbcsql17/
COPY --from=rpm-extractor /tmp/usr/lib64/ /usr/lib/
COPY --from=rpm-extractor /tmp/etc/ /etc/

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Install runtime dependencies
RUN apk add --no-cache unixodbc

# Copy extracted ODBC driver files
COPY --from=rpm-extractor /tmp/opt/microsoft/msodbcsql17/ /opt/microsoft/msodbcsql17/
COPY --from=rpm-extractor /tmp/usr/lib64/ /usr/lib/
COPY --from=rpm-extractor /tmp/etc/ /etc/

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

## Recommendation

I'd recommend **Option 1** (Red Hat UBI) or **Option 2** (CentOS/Rocky) since they natively support RPM packages and will be more reliable. Just replace `path/to/your/odbc-driver.rpm` with the actual path to your RPM file relative to your build context.

The exact paths in the extraction method (Option 3) will depend on the contents of your specific RPM file. You can examine the RPM contents first by running:
```bash
rpm -qlp your-odbc-driver.rpm
```

Yes! There is a native Alpine APK solution. Microsoft provides ODBC Driver 17 for SQL Server as APK packages specifically for Alpine Linux. Here's the updated Dockerfile:

```dockerfile
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    unixodbc-dev \
    g++ \
    make

# Add Microsoft's Alpine repository and install ODBC driver
RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
    curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.10.1.1-1_amd64.apk && \
    apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
    apk add --allow-untrusted mssql-tools_17.10.1.1-1_amd64.apk

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Install runtime dependencies
RUN apk add --no-cache \
    unixodbc \
    curl

# Install Microsoft ODBC Driver 17 for SQL Server
RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
    apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
    rm -f msodbcsql17_17.10.5.1-1_amd64.apk

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

## Even better - using Alpine's edge repository:

If you want to use the most up-to-date version, you can also try using Alpine's edge repository which might have more recent packages:

```dockerfile
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    unixodbc-dev \
    g++ \
    make

# Add Microsoft's repository key and install ODBC driver from edge
RUN apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    msodbcsql17

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Install runtime dependencies including ODBC driver
RUN apk add --no-cache \
    unixodbc && \
    apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing \
    msodbcsql17

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

## Most reliable Alpine solution:

Here's the most reliable version that combines both approaches as fallback:

```dockerfile
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    unixodbc-dev \
    g++ \
    make \
    curl

# Try to install from Alpine edge repository, fallback to Microsoft APK
RUN apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing msodbcsql17 || \
    (curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
     apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
     rm -f msodbcsql17_17.10.5.1-1_amd64.apk)

# Install Python dependencies
RUN pip install --no-cache-dir \
    mysql-connector-python \
    flask \
    Flask-Moment \
    gunicorn \
    requests \
    pyodbc

FROM python:3.12-alpine
LABEL authors="jdlowel"

# Install runtime dependencies
RUN apk add --no-cache \
    unixodbc \
    curl

# Install Microsoft ODBC Driver 17 for SQL Server (same fallback approach)
RUN apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing msodbcsql17 || \
    (curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \
     apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
     rm -f msodbcsql17_17.10.5.1-1_amd64.apk)

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY squishy_REST_API /app/squishy_REST_API/

# Expose port
EXPOSE 5000

## Start the application using the runnable package
CMD ["python", "-m", "squishy_REST_API"]
```

The key points:
1. **msodbcsql17** is available as a native Alpine APK package
2. It's in the `testing` repository of Alpine edge
3. Microsoft also provides pre-built APK packages as a fallback
4. You need `unixodbc` and `unixodbc-dev` (for building) as dependencies

This approach keeps your image size smaller and is more "Alpine-native" than extracting RPM contents.