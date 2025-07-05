# Containerized MySQL Database

A lightweight MySQL database container built on the official MySQL image, pre-configured 
with initialization scripts and environment variables for seamless SquishyBadger integration.

## Table of Contents

- [Service Operation](#service-operation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Required Files](#required-files)
- [API Reference](#api-reference)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Project Status](#project-status)
- [Version and Change Log](#version)
- [Roadmap](#roadmap)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

## Service Operation
The squishy-db service requires the provided [initialization scripts](#required-files) and 
specific [environment variables](#environment-variables) on the first run to
construct the expected database for the SquishyBadger pod.

On first time run (no database found) it will: 
1. Use environment variables to define usernames and passwords
2. Use environment variables to initialize a named database
3. Create the tables and procedures defined in .sql scripts found in the `/docker-entrypoint-initdb.d` directory

On subsequent runs it will
1. Utilize the configuration found in the existing database

## Quick Start
There is a quick start for all the services in the root README.md, if you want to start only the MySQL 
database use the instructions below.
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
**Note:** This method creates a `docker volume` on the local machine and mounts it at `/var/lib/mysql` 
inside the container to hold the persistent database data. In a production environment this mount should 
be a true data store like a directory on the machine, or a network storage solution.

## Configuration
### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MYSQL_ROOT_PASSWORD` | Root user password | Yes |
| `MYSQL_DATABASE` | Initial database name | Yes |
| `MYSQL_USER` | Application user name | Yes |
| `MYSQL_PASSWORD` | Application user password | Yes |

**NOTE** The environment variables are only used when no existing database/configuration
is found. When mysql finds an existing configuration at `/var/lib/mysql`, it will ignore 
the environment variables.

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
A `logs_init.sql` file with the following content:

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

And `sites_state_init.sql` file with the following content:

```sql
-- Authoritative list of sites
CREATE TABLE site_list (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL UNIQUE,
    online BOOLEAN DEFAULT 1,

    INDEX idx_site_name (site_name)
);

-- History of hash states
CREATE TABLE state_history (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    update_id TEXT NOT NULL,
    hash_value VARCHAR(40) NOT NULL UNIQUE,
    record_count INT,
    created_at INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),

    -- Index for performance
    INDEX idx_hash_value (hash_value),
    INDEX idx_created_at (created_at)
);

-- Sites and their current hash states - references site_list, state_history
CREATE TABLE sites (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL UNIQUE,
    current_hash VARCHAR(40),
    last_updated INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),

    -- Foreign key to authoritative list
    FOREIGN KEY (site_name) REFERENCES site_list(site_name) ON DELETE CASCADE,
    FOREIGN KEY (current_hash) REFERENCES state_history(hash_value),

    INDEX idx_site_name (site_name),
    INDEX idx_current_hash (current_hash),
    INDEX idx_last_updated (last_updated)
);
-- Procedure to sync operational tables when site_list changes
DELIMITER //
CREATE PROCEDURE SyncSiteOperationalData()
BEGIN
    -- Add new sites to operational table
    INSERT IGNORE INTO sites (site_name)
    SELECT site_name FROM site_list
    WHERE site_name NOT IN (SELECT site_name FROM sites);
END //
DELIMITER ;
-- Create a trigger to auto-update the timestamp
DELIMITER //
CREATE TRIGGER sites_update_timestamp
    BEFORE UPDATE ON sites
    FOR EACH ROW
BEGIN
    SET NEW.last_updated = UNIX_TIMESTAMP();
END//
DELIMITER ;
```

## API reference

### Database Schema

The database will be automatically initialized on the first run with the tables:

`hashtable`: Tracks file paths and their associated hash values, timestamps, and directory contents.

`logs`: Stores log entries for review or forwarding to a core site

`site_list`: Authoritative list of sites with online status

`state_history`: Historical record of hash states and updates

`sites`: Current hash state for each site with foreign key relationships

### Connection

- **Host**: localhost (or container name if using Docker network)
- **Port**: 3306
- **Database**: Value of `MYSQL_DATABASE`
- **Username**: Value of `MYSQL_USER`
- **Password**: Value of `MYSQL_PASSWORD`


### Interface
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

`site_list`:
1. Minimum required values are `site_name` (max 5 characters, must be unique)
2. `online` defaults to `1` (true)

`state_history`:
1. Minimum required values are `update_id` and `hash_value`
2. `created_at` defaults to current timestamp

`sites`:
1. Must reference valid `site_name` from `site_list` (foreign key constraint)
2. If `current_hash` is specified, must reference valid `hash_value` from `state_history`
3. `last_updated` auto-updates on record modification

## Development

### Project Structure

```
squishy_db/
├── init_scripts/               # Initialzation script for required tables and procedures
│   ├── hashtable_init.sql
│   ├── logs_init.sql
│   └── sites_states_init.sql   
├── tests/                      # Test suite (ensures desired table schema enforcement)
│   ├── test_hashtable.sql
│   ├── test_logs.sql
│   └── test_sites_state.sql
└── README.md
```

### Local Development Setup
Start by cloning the repository to your workspace.
```bash
# Clone the repository
git clone <repository-url>
cd squishy-db
```
1. **Prerequisites**: mysql:9.3, initialization scripts
2**Environment**: [Environment variables](#environment-variables) are required to set usernames and passwords on first run
3**Run**: see [quick start](#quick-start)

## Testing
This package also includes tests, in the form of SQL scripts, which can be used to verify that the 
tables exist and are configured in compliance with the Database interface. The scripts use 
transactions that get rolled back at the end, so they won't leave test data in your table.

To run the scripts in your MySQL 9.3 container:

1. **Copy the scripts to your container**:
      ```bash
      docker cp tests/. mysql-squishy-db:/tmp/
      ```
2. **Execute the scripts in the container**:
   ```bash
   docker exec -it mysql-squishy-db mysql -u root -pyour_root_password -e "source /tmp/test_hashtable.sql"
   ```
   ```bash
   docker exec -it mysql-squishy-db mysql -u root -pyour_root_password -e "source /tmp/test_logs.sql"
   ```
   ```bash
   docker exec -it mysql-squishy-db mysql -u root -pyour_root_password -e "source /tmp/test_sites_state.sql"
   ```

Or run them directly:
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_hashtable.sql
```
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_logs.sql
```
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_sites_state.sql
```

### **What the test_hashtable.sql script tests:**

1. **Basic inserts** - Tests simple minimum record insertion
2. **Generated column** - Verifies the hash unique key generation works correctly
3. **Default values** - Verifies default values are applied
4. **Timestamp functionality** - Verifies automatic timestamp generation
5. **Insert all fields** - Verifies that record insertion with all fields works correctly
6. **Update operations** - Tests record updates
7. **Ordered update operations** - Verifies 'in database' field shift then update operations work correctly
8. **Complex queries** - Tests aggregation functions
9. **Data integrity** - Verifies field lengths and constraints
10. **Special characters** - Tests handling of special characters in text fields
11. **Case in-sensitivity** - Verifies current_hash, target_hash, and prev_hash are case-insensitive
12. **Required field enforcement** - Verifies records without required fields are rejected.


### **What the test_logs.sql script tests:**

1. **Basic inserts** - Tests simple record insertion.
2. **Auto increment log_id** - Verifies that log_id auto increments.
3. **Required field enforcement** - Verifies records without required fields are rejected.
4. **Default values** - Verifies default values are applied.
5. **Length enforcement** Verifies length constraints are enforced.
6. **ENUM permitted** Verifies 'log_levels' in the table's list are accepted.
7. **ENUM enforcement** Verifies 'log_levels' must be from table's list.
8. **Full field insertion** - Tests full record insertion.
9. **Case in-sensitivity** - Verifies site_id and log_level are case-insensitive.

### **What the test_sites_state.sql script tests:**

1. **site_list table** - Basic inserts, defaults, constraints, and unique enforcement
2. **state_history table** - Required fields, timestamp generation, and data integrity
3. **sites table** - Foreign key constraints, cascade deletes, and update triggers
4. **Stored procedure** - SyncSiteOperationalData functionality
5. **Data relationships** - Cross-table consistency and referential integrity

## Project Status

🟢 **Completed/Done** - This project will be updated as required.

## Version

Current version: 1.0

## Changelog

**v1.0 - 2025-06-26**

-   Baseline of current project state.

### Roadmap
N/A

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: Less detailed docs available on the [confluence space](http://confluence)

## Acknowledgments

- Containerization with Docker
- MySQL container maintained by the Docker Community and the MySQL Team

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!