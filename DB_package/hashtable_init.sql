CREATE TABLE IF NOT EXISTS hashtable (
    path TEXT NOT NULL,
    hashed_path VARCHAR(64) AS (SHA2(path, 256)) STORED PRIMARY KEY, -- Not case sensitive
    current_hash VARCHAR(40) NOT NULL, -- Not case sensitive
    current_dtg_latest DOUBLE DEFAULT (UNIX_TIMESTAMP()),
    current_dtg_first DOUBLE DEFAULT (`current_dtg_latest`),
    target_hash VARCHAR(40), -- Not case sensitive
    prev_hash VARCHAR(40), -- Not case sensitive
    prev_dtg_latest DOUBLE,
    dirs TEXT,
    files TEXT,
    links TEXT
);