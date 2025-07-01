CREATE TABLE IF NOT EXISTS logs (
    log_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_id VARCHAR(5) DEFAULT ('local'), -- Not case sensitive
    session_id VARCHAR(32),
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT ('INFO'), -- Not case sensitive
    timestamp INT UNSIGNED DEFAULT (UNIX_TIMESTAMP()),
    summary_message TEXT NOT NULL,
    detailed_message TEXT
);