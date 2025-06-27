# Squishy Nginx reverse-proxy

A containerized Nginx-based reverse-proxy setup for SquishyBadger data management with automatic initialization.

## Quick Start

### Using Docker Run

```bash
docker run -d \
  --name mysql-squishy-db \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=your_app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v $(pwd)/init_scripts:/docker-entrypoint-initdb.d \
  -p 3306:3306 \
  mysql:9.3
```

### Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
services:
  mysql:
    image: mysql:9.3
    container_name: mysql-squishy-db
    environment:
      MYSQL_ROOT_PASSWORD: your_root_password
      MYSQL_DATABASE: squishy_db
      MYSQL_USER: your_app_user
      MYSQL_PASSWORD: your_user_password
    volumes:
      - ./init_scripts:/docker-entrypoint-initdb.d
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  mysql_data:
```
**Note:** Both of these methods create a `docker volume` on the local machine and mount it at `/var/lib/mysql` 
to hold the persistent database data. In a production environment this mount should be a true data
store like a directory on the machine, or a network storage solution.

Then run:
```bash
docker-compose up -d
```

## Required Files
In the project directory there is subdirectory named `init_scripts` that contains the table
configurations mysql will apply on startup if there is no database found. Below are the contents
of the files found in that directory.

A `hashtable_init.sql` file with the following content:

```sql
CREATE TABLE IF NOT EXISTS hashtable (
    path TEXT NOT NULL,
    hashed_path VARCHAR(64) AS (SHA2(path, 256)) STORED PRIMARY KEY,
    current_hash VARCHAR(40) NOT NULL,
    current_dtg_latest INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),
    current_dtg_first INT UNSIGNED DEFAULT (`current_dtg_latest`),
    target_hash VARCHAR(40),
    prev_hash VARCHAR(40),
    prev_dtg_latest INT UNSIGNED,
    dirs TEXT,
    files TEXT,
    links TEXT
);
```
and a `logs_init.sql` file with the following content:

```sql
CREATE TABLE IF NOT EXISTS logs (
    log_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_id VARCHAR(5) DEFAULT ('Local'),
    log_level ENUM('ERROR', 'STATUS', 'WARNING', 'INFO') DEFAULT ('INFO'),
    timestamp INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),
    summary_message TEXT NOT NULL,
    detailed_message TEXT
);
```

## Environment Variables
None: The nginx image does not have any native support for using environment variables.

## Connection

- **Host**: localhost (or container name if using Docker network)
- **Port**: 3306
- **Database**: Value of `MYSQL_DATABASE`
- **Username**: Value of `MYSQL_USER`
- **Password**: Value of `MYSQL_PASSWORD`


## Interface
This container enforces the DB schema(s) it is initialized with

`hashtable`: 
1. Minimum required values are `path` and `current_hash`.
2. For new rows, `current_dtg_latest` and `current_dtg_first` are set to the current
time automatically.
3. A column `hashed_path` is generated automatically to enforce uniqueness and act as
primary key (Uniqueness can't be enforced directly on the path column because it is a TEXT column with no defined length limit).

`logs`:
1. Minimum required values are `summary_message`
2. `site_id` must be five or fewer characters, and is set to `local` by default
3. `log_level` is `INFO` by default. If this value is included in an insert or update 
operation it must be one of `ERROR`, `STATUS`, `WARNING`, or `INFO`


## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

### Roadmap
- [ ] Comprehensive logging and monitoring
- [ ] Web GUI to easily access status
- [ ] Enhanced authentication and authorization
- [ ] Rate limiting implementation
- [ ] Performance optimization
- [ ] Additional database backend support

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: For Detailed docs please refer to the nginx official docker image

## Acknowledgments

- Built with nginx reverse proxy server
- Containerization with Docker

---

**Made with 😠 by the SquishyBadger Team**