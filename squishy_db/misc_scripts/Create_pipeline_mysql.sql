USE squishy_db;
CREATE TABLE pipeline_site_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    site_name VARCHAR(5) NOT NULL UNIQUE, -- Added for compatibility with other queries
    online BOOLEAN DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_site_name (site_name),
    INDEX idx_online (online)
);

-- =====================================================
-- Table: authorized_updates
-- Purpose: Store TeamCity pipeline updates and their processing status
-- =====================================================
CREATE TABLE authorized_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    TC_id VARCHAR(25) NOT NULL,                    -- TeamCity job number
    timestamp INT UNSIGNED NOT NULL,                -- Unix timestamp
    update_path VARCHAR(1000) NOT NULL,             -- Path to the update
    update_size BIGINT UNSIGNED DEFAULT 0,          -- Size in bytes
    hash_value VARCHAR(64) DEFAULT NULL,            -- SHA256 hash (NULL = unprocessed)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_hash_value (hash_value),
    INDEX idx_update_path (update_path(255)),       -- Partial index for long paths
    INDEX idx_timestamp (timestamp),
    INDEX idx_tc_id (TC_id),
    INDEX idx_unprocessed (hash_value, timestamp)  -- Composite for unprocessed queries
);
