CREATE TABLE IF NOT EXISTS hashtable (
    path TEXT NOT NULL,
    hashed_path VARCHAR(64) AS SHA2(path, 256) STORED PRIMARY KEY, -- Not case sensitive
    current_hash VARCHAR(40) NOT NULL, -- Not case sensitive
    current_dtg_latest INT UNSIGNED DEFAULT UNIX_TIMESTAMP(),
    current_dtg_first INT UNSIGNED DEFAULT (`current_dtg_latest`),
    target_hash VARCHAR(40), -- Not case sensitive
    prev_hash VARCHAR(40), -- Not case sensitive
    prev_dtg_latest INT UNSIGNED,
    dirs JSON,
    files JSON,
    links JSON,

    -- Index for performance
    INDEX idx_path (path(255)),  -- Index with prefix length for path
    INDEX idx_dirs ((CAST(dirs->'$[0]' AS CHAR(100)))),
    INDEX idx_files ((CAST(files->'$[0]' AS CHAR(100)))),
    INDEX idx_links ((CAST(links->'$[0]' AS CHAR(100))))
);