-- Authoritative list of sites
CREATE TABLE site_list (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    site_name VARCHAR(5) NOT NULL UNIQUE,
    online BOOLEAN DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_SITE_name (name),
    INDEX idx_online (online)
);

-- History of hash states
CREATE TABLE state_history (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    update_id TEXT NOT NULL,
    hash_value VARCHAR(64) NOT NULL UNIQUE,
    record_count INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Index for performance
    INDEX idx_hash_value (hash_value),
    INDEX idx_created_at (created_at)
);

-- Sites and their current hash states - references site_list, state_history
CREATE TABLE sites (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL UNIQUE,
    current_hash VARCHAR(64) NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key to authoritative list
    FOREIGN KEY (site_name) REFERENCES site_list(site_name) ON DELETE CASCADE,
    FOREIGN KEY (current_hash) REFERENCES state_history(hash_value) ON DELETE SET NULL,

    INDEX idx_site_name (site_name),
    INDEX idx_current_hash (current_hash),
    INDEX idx_last_updated (last_updated)
);

-- Sites and their current hash states - references site_list
CREATE TABLE remotes_hash_status (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL,
    path TEXT NOT NULL,
    current_hash VARCHAR(64) NOT NULL, -- Not case sensitive
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key to authoritative list
    FOREIGN KEY (site_name) REFERENCES site_list(site_name) ON DELETE CASCADE,

    INDEX idx_site_name (site_name)
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




