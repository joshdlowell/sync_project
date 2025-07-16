USE squishy_db;
CREATE TABLE pipeline_site_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    site_name VARCHAR(5) NOT NULL UNIQUE, -- Added for compatibility with other queries
    online TINYINT(1) DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_site_name (site_name),
    INDEX idx_name (name),
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
    INDEX idx_unprocessed (hash_value, timestamp),  -- Composite for unprocessed queries

    -- Constraints
    UNIQUE KEY uk_update_path (update_path(500))     -- Prevent duplicate paths
);

-- =====================================================
-- Table: site_pipeline_status
-- Purpose: Track pipeline completion status for each site
-- =====================================================
CREATE TABLE site_pipeline_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(5) NOT NULL,
    completed TINYINT(1) DEFAULT 0,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    pipeline_run_id VARCHAR(100) DEFAULT NULL,      -- Optional: link to specific pipeline run
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_site_name (site_name),
    INDEX idx_completed (completed),
    INDEX idx_completed_at (completed_at),
    INDEX idx_pipeline_run (pipeline_run_id),
    
    -- Foreign key constraint
    CONSTRAINT fk_site_pipeline_site 
        FOREIGN KEY (site_name) 
        REFERENCES pipeline_site_list(site_name)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- Insert sample data for testing
-- =====================================================

-- Sample sites
INSERT INTO pipeline_site_list (name, site_name, online, description) VALUES
('SIT1', 'SIT1', 1, 'Primary production site'),
('SIT2', 'SIT2', 1, 'Secondary production site'),
('SIT3', 'SIT3', 1, 'Development site'),
('SIT4', 'SIT4', 0, 'Maintenance site - currently offline');

-- Sample authorized updates
INSERT INTO authorized_updates (TC_id, timestamp, update_path, update_size, hash_value) VALUES
('12345', UNIX_TIMESTAMP('2024-01-15 10:30:00'), '/updates/release-1.0.0.zip', 1048576, 'abc123def4567890123456789012345678901234'),
('12346', UNIX_TIMESTAMP('2024-01-15 11:00:00'), '/updates/hotfix-1.0.1.zip', 524288, 'def456abc1234567890123456789012345678901'),
('12347', UNIX_TIMESTAMP('2024-01-15 12:30:00'), '/updates/release-1.1.0.zip', 2097152, NULL), -- Unprocessed
('12348', UNIX_TIMESTAMP('2024-01-15 13:00:00'), '/updates/security-patch-1.0.2.zip', 786432, NULL); -- Unprocessed

-- Sample pipeline status entries
INSERT INTO site_pipeline_status (site_name, completed, completed_at, pipeline_run_id) VALUES
('SIT1', 1, '2024-01-15 10:45:00', '12345'),
('SIT2', 1, '2024-01-15 10:50:00', '12345'),
('SIT3', 0, NULL, '12347'),
('SIT4', 0, NULL, NULL);