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
    created_at INT UNSIGNED DEFAULT UNIX_TIMESTAMP(),

    -- Index for performance
    INDEX idx_hash_value (hash_value),
    INDEX idx_created_at (created_at)
);

-- Sites and their current hash states - references site_list, state_history
CREATE TABLE sites (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL UNIQUE,
    current_hash VARCHAR(40) NULL,
    last_updated INT UNSIGNED DEFAULT UNIX_TIMESTAMP(),

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
    current_hash VARCHAR(40) NOT NULL, -- Not case sensitive
    last_updated INT UNSIGNED DEFAULT UNIX_TIMESTAMP(),

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
-- Create a trigger to auto-update the timestamp
DELIMITER //
CREATE TRIGGER sites_update_timestamp
    BEFORE UPDATE ON sites
    FOR EACH ROW
BEGIN
    SET NEW.last_updated = UNIX_TIMESTAMP();
END//
DELIMITER ;
-- Create trigger to update last_updated on row updates
DELIMITER //
CREATE TRIGGER update_last_updated
    BEFORE UPDATE ON remotes_hash_status
    FOR EACH ROW
BEGIN
    SET NEW.last_updated = UNIX_TIMESTAMP();
END//
DELIMITER ;




