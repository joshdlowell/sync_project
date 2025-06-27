Here are the configuration files for your setup:

## nginx.conf

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

## conf.d/default.conf

```nginx
# Default server block - catch all undefined hosts
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Return 444 (connection closed without response) for undefined hosts
    return 444;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;
    
    # Use a self-signed cert for the default server
    ssl_certificate /etc/nginx/certs/default.crt;
    ssl_certificate_key /etc/nginx/certs/default.key;
    
    # Return 444 for undefined hosts
    return 444;
}
```

## conf.d/squishybadger.conf

```nginx
# HTTP server - redirect all traffic to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name squishybadger.local.org;

    # Redirect all HTTP requests to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server - main reverse proxy
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name squishybadger.local.org;

    # SSL configuration
    ssl_certificate /etc/nginx/certs/squishybadger.local.org.crt;
    ssl_certificate_key /etc/nginx/certs/squishybadger.local.org.key;
    
    # Optional: include intermediate certificates if you have them
    # ssl_trusted_certificate /etc/nginx/certs/ca-bundle.crt;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Buffer settings
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;

    # Main location - proxy to your API
    location / {
        proxy_pass http://squishy-rest-api:5000;
        
        # Handle WebSocket connections if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Optional: Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Optional: Block access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

## Expected Certificate Files

Make sure you have these certificate files in your `./certs/` directory:

```
certs/
├── squishybadger.local.org.crt    # Your SSL certificate
├── squishybadger.local.org.key    # Your private key
├── default.crt                    # Self-signed cert for default server (optional)
└── default.key                    # Self-signed key for default server (optional)
```

## Updated docker-compose.yml

Make sure your docker-compose.yml connects to the same network as your API container:

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginx:alpine
    container_name: nginx-reverse-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
      - ./logs:/var/log/nginx
    restart: unless-stopped
    networks:
      - proxy-network
    depends_on:
      - squishy-rest-api  # if the API is in the same compose file

networks:
  proxy-network:
    driver: bridge
```

## To generate a self-signed certificate for testing:

If you need to create certificates for testing:

```bash
# Create the certs directory
mkdir -p certs

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/squishybadger.local.org.key \
  -out certs/squishybadger.local.org.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=squishybadger.local.org"
```

This setup will:
- Force all HTTP traffic to HTTPS
- Proxy HTTPS requests to your API container
- Include security headers
- Handle WebSocket connections if needed
- Provide proper error handling for undefined hosts

# LOG forwarding to rest api
Yes! You can forward logs to a REST API endpoint. Here are several approaches:

## Option 1: Using nginx's access_log with a named pipe and a sidecar container

### Modified nginx.conf

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # JSON logging format for API consumption
    log_format json_combined escape=json
    '{'
        '"time_local":"$time_local",'
        '"remote_addr":"$remote_addr",'
        '"remote_user":"$remote_user",'
        '"request":"$request",'
        '"status": "$status",'
        '"body_bytes_sent":"$body_bytes_sent",'
        '"request_time":"$request_time",'
        '"http_referrer":"$http_referer",'
        '"http_user_agent":"$http_user_agent",'
        '"http_x_forwarded_for":"$http_x_forwarded_for",'
        '"http_host":"$http_host",'
        '"server_name":"$server_name",'
        '"request_uri":"$request_uri",'
        '"https":"$https"'
    '}';

    # Send access logs to named pipe
    access_log /tmp/access.log json_combined;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

### Log Forwarder Script

Create a `log-forwarder.sh` script:

```bash
#!/bin/bash

LOG_API_ENDPOINT="${LOG_API_ENDPOINT:-http://your-log-api:3000/logs}"
LOG_FILE="${LOG_FILE:-/tmp/access.log}"
BATCH_SIZE="${BATCH_SIZE:-10}"
FLUSH_INTERVAL="${FLUSH_INTERVAL:-5}"

echo "Starting log forwarder..."
echo "API Endpoint: $LOG_API_ENDPOINT"
echo "Log File: $LOG_FILE"

# Create named pipe if it doesn't exist
if [[ ! -p $LOG_FILE ]]; then
    mkfifo $LOG_FILE
fi

# Buffer for batch sending
declare -a log_buffer=()
last_flush=$(date +%s)

# Function to send logs to API
send_logs() {
    if [ ${#log_buffer[@]} -eq 0 ]; then
        return
    fi
    
    # Create JSON array
    json_payload="["
    for i in "${!log_buffer[@]}"; do
        if [ $i -ne 0 ]; then
            json_payload+=","
        fi
        json_payload+="${log_buffer[$i]}"
    done
    json_payload+="]"
    
    # Send to API
    curl -X POST \
         -H "Content-Type: application/json" \
         -d "$json_payload" \
         "$LOG_API_ENDPOINT" \
         --max-time 10 \
         --retry 3 \
         --retry-delay 1 \
         --silent || echo "Failed to send logs to API"
    
    # Clear buffer
    log_buffer=()
}

# Read logs and forward them
while IFS= read -r line; do
    log_buffer+=("$line")
    current_time=$(date +%s)
    
    # Send if buffer is full or time interval reached
    if [ ${#log_buffer[@]} -ge $BATCH_SIZE ] || [ $((current_time - last_flush)) -ge $FLUSH_INTERVAL ]; then
        send_logs
        last_flush=$current_time
    fi
done < "$LOG_FILE"
```

### Updated docker-compose.yml

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginx:alpine
    container_name: nginx-reverse-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
      - log-pipe:/tmp
    restart: unless-stopped
    networks:
      - proxy-network
    depends_on:
      - log-forwarder

  log-forwarder:
    image: alpine:latest
    container_name: log-forwarder
    volumes:
      - ./log-forwarder.sh:/usr/local/bin/log-forwarder.sh:ro
      - log-pipe:/tmp
    environment:
      - LOG_API_ENDPOINT=http://your-log-api:3000/logs
      - BATCH_SIZE=10
      - FLUSH_INTERVAL=5
    command: |
      sh -c "
        apk add --no-cache curl &&
        chmod +x /usr/local/bin/log-forwarder.sh &&
        /usr/local/bin/log-forwarder.sh
      "
    restart: unless-stopped
    networks:
      - proxy-network

networks:
  proxy-network:
    driver: bridge

volumes:
  log-pipe:
```

## Option 2: Using Fluentd (More robust solution)

### docker-compose.yml with Fluentd

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginx:alpine
    container_name: nginx-reverse-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
    restart: unless-stopped
    networks:
      - proxy-network
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: nginx.access
    depends_on:
      - fluentd

  fluentd:
    image: fluentd:v1.16-debian-1
    container_name: log-forwarder
    ports:
      - "24224:24224"
      - "24224:24224/udp"
    volumes:
      - ./fluent.conf:/fluentd/etc/fluent.conf:ro
    networks:
      - proxy-network
    restart: unless-stopped

networks:
  proxy-network:
    driver: bridge
```

### fluent.conf

```xml
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match nginx.access>
  @type http
  endpoint http://your-log-api:3000/logs
  http_method post
  
  <format>
    @type json
  </format>
  
  <buffer>
    @type memory
    flush_interval 5s
    chunk_limit_size 1MB
    retry_max_times 3
    retry_wait 1s
  </buffer>
</match>
```

## Option 3: Simple syslog forwarding

### Modified nginx.conf (syslog approach)

```nginx
# In the http block, replace the access_log line with:
access_log syslog:server=log-forwarder:514,facility=local0,tag=nginx,severity=info json_combined;
```

### Syslog forwarder docker-compose.yml

```yaml
version: '3.8'

services:
  nginx-proxy:
    image: nginx:alpine
    container_name: nginx-reverse-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
    restart: unless-stopped
    networks:
      - proxy-network
    depends_on:
      - log-forwarder

  log-forwarder:
    image: alpine:latest
    container_name: log-forwarder
    ports:
      - "514:514/udp"
    volumes:
      - ./syslog-forwarder.sh:/usr/local/bin/syslog-forwarder.sh:ro
    environment:
      - LOG_API_ENDPOINT=http://your-log-api:3000/logs
    command: |
      sh -c "
        apk add --no-cache curl rsyslog &&
        chmod +x /usr/local/bin/syslog-forwarder.sh &&
        /usr/local/bin/syslog-forwarder.sh
      "
    restart: unless-stopped
    networks:
      - proxy-network

networks:
  proxy-network:
    driver: bridge
```

## Recommendation

I recommend **Option 1** (named pipe with sidecar) for simplicity, or **Option 2** (Fluentd) for production environments as it provides:

- Better error handling and retry logic
- Buffering capabilities
- Built-in JSON parsing
- More reliable delivery guarantees

Which approach would you prefer to implement?