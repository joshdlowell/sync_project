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
