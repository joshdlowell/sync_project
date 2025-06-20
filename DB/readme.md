# Containerized MySQL Database

A containerized MySQL database setup for hash table management with automatic initialization.

## Quick Start

### Using Docker Run

```bash
docker run -d \
  --name mysql-hashtable \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=hashtable_db \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v $(pwd)/init.sql:/docker-entrypoint-initdb.d/init.sql \
  -p 3306:3306 \
  mysql:9.3
```

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:9.3
    container_name: mysql-hashtable
    environment:
      MYSQL_ROOT_PASSWORD: your_root_password
      MYSQL_DATABASE: hashtable_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: your_user_password
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  mysql_data:
```

Then run:
```bash
docker-compose up -d
```

## Required Files

Create an `init.sql` file in your project directory with the following content:

```sql
CREATE TABLE IF NOT EXISTS hashtable (
    path TEXT NOT NULL,
    hashed_path VARCHAR(64) AS (SHA2(path, 256)) STORED PRIMARY KEY,
    current_hash VARCHAR(40) NOT NULL,
    current_dtg_latest DOUBLE DEFAULT (UNIX_TIMESTAMP()),
    current_dtg_first DOUBLE DEFAULT 0,
    target_hash VARCHAR(40),
    prev_hash VARCHAR(40),
    prev_dtg_latest DOUBLE,
    dirs TEXT DEFAULT (''),
    files TEXT DEFAULT (''),
    links TEXT DEFAULT ('')
);
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MYSQL_ROOT_PASSWORD` | Root user password | Yes |
| `MYSQL_DATABASE` | Initial database name | Yes |
| `MYSQL_USER` | Application user name | Yes |
| `MYSQL_PASSWORD` | Application user password | Yes |

## Database Schema

The database will be automatically initialized with a `hashtable` table that tracks file paths and their associated hash values, timestamps, and directory contents.

## Connection

- **Host**: localhost (or container name if using Docker network)
- **Port**: 3306
- **Database**: Value of `MYSQL_DATABASE`
- **Username**: Value of `MYSQL_USER`
- **Password**: Value of `MYSQL_PASSWORD`