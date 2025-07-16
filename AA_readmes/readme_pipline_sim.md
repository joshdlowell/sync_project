Based on the queries and methods in the pipeline class, here are the MySQL table creation scripts:

```sql
-- =====================================================
-- Pipeline Database Table Creation Scripts for MySQL
-- =====================================================

-- Drop tables if they exist (for clean recreation)
DROP TABLE IF EXISTS site_pipeline_status;
DROP TABLE IF EXISTS authorized_updates;
DROP TABLE IF EXISTS site_list;

-- =====================================================
-- Table: site_list
-- Purpose: Authoritative list of valid sites
-- =====================================================
CREATE TABLE site_list (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    site_name VARCHAR(255) NOT NULL UNIQUE, -- Added for compatibility with other queries
    online TINYINT(1) DEFAULT 1,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_site_name (site_name),
    INDEX idx_name (name),
    INDEX idx_online (online)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: authorized_updates
-- Purpose: Store TeamCity pipeline updates and their processing status
-- =====================================================
CREATE TABLE authorized_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    TC_id VARCHAR(100) NOT NULL,                    -- TeamCity job number
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: site_pipeline_status
-- Purpose: Track pipeline completion status for each site
-- =====================================================
CREATE TABLE site_pipeline_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(255) NOT NULL,
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
        REFERENCES site_list(site_name) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Insert sample data for testing
-- =====================================================

-- Sample sites
INSERT INTO site_list (name, site_name, online, description) VALUES
('site-alpha', 'site-alpha', 1, 'Primary production site'),
('site-beta', 'site-beta', 1, 'Secondary production site'),
('site-gamma', 'site-gamma', 1, 'Development site'),
('site-delta', 'site-delta', 0, 'Maintenance site - currently offline');

-- Sample authorized updates
INSERT INTO authorized_updates (TC_id, timestamp, update_path, update_size, hash_value) VALUES
('TC-12345', UNIX_TIMESTAMP('2024-01-15 10:30:00'), '/updates/release-1.0.0.zip', 1048576, 'abc123def456789012345678901234567890123456789012345678901234567890'),
('TC-12346', UNIX_TIMESTAMP('2024-01-15 11:00:00'), '/updates/hotfix-1.0.1.zip', 524288, 'def456abc123456789012345678901234567890123456789012345678901234567890'),
('TC-12347', UNIX_TIMESTAMP('2024-01-15 12:30:00'), '/updates/release-1.1.0.zip', 2097152, NULL), -- Unprocessed
('TC-12348', UNIX_TIMESTAMP('2024-01-15 13:00:00'), '/updates/security-patch-1.0.2.zip', 786432, NULL); -- Unprocessed

-- Sample pipeline status entries
INSERT INTO site_pipeline_status (site_name, completed, completed_at, pipeline_run_id) VALUES
('site-alpha', 1, '2024-01-15 10:45:00', 'TC-12345'),
('site-beta', 1, '2024-01-15 10:50:00', 'TC-12345'),
('site-gamma', 0, NULL, 'TC-12347'),
('site-delta', 0, NULL, NULL);

-- =====================================================
-- Useful queries for testing the implementation
-- =====================================================

-- Test query: Get unprocessed updates
SELECT id, TC_id, timestamp, update_path, update_size, hash_value
FROM authorized_updates
WHERE hash_value IS NULL
ORDER BY timestamp ASC;

-- Test query: Get all sites
SELECT name FROM site_list ORDER BY name;

-- Test query: Get processed updates
SELECT id, TC_id, timestamp, update_path, update_size, hash_value
FROM authorized_updates
WHERE hash_value IS NOT NULL
ORDER BY timestamp DESC;

-- Test query: Check pipeline completion status
SELECT sl.site_name, sps.completed, sps.completed_at, sps.pipeline_run_id
FROM site_list sl
LEFT JOIN site_pipeline_status sps ON sl.site_name = sps.site_name
ORDER BY sl.site_name;

-- =====================================================
-- Optional: Create views for common queries
-- =====================================================

-- View: Unprocessed updates summary
CREATE VIEW v_unprocessed_updates AS
SELECT 
    id,
    TC_id,
    FROM_UNIXTIME(timestamp) as update_time,
    update_path,
    ROUND(update_size / 1024 / 1024, 2) as size_mb,
    DATEDIFF(NOW(), FROM_UNIXTIME(timestamp)) as days_pending
FROM authorized_updates
WHERE hash_value IS NULL
ORDER BY timestamp ASC;

-- View: Site pipeline status summary
CREATE VIEW v_site_pipeline_summary AS
SELECT 
    sl.site_name,
    sl.online,
    COALESCE(sps.completed, 0) as completed,
    sps.completed_at,
    sps.pipeline_run_id,
    CASE 
        WHEN sl.online = 0 THEN 'Offline'
        WHEN sps.completed = 1 THEN 'Completed'
        WHEN sps.completed = 0 THEN 'Pending'
        ELSE 'Unknown'
    END as status
FROM site_list sl
LEFT JOIN site_pipeline_status sps ON sl.site_name = sps.site_name
ORDER BY sl.site_name;

-- =====================================================
-- Performance optimization queries
-- =====================================================

-- Show table sizes
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME IN ('site_list', 'authorized_updates', 'site_pipeline_status');

-- Show index usage
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    CARDINALITY
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME IN ('site_list', 'authorized_updates', 'site_pipeline_status')
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
```

## Key Features of These Tables:

### 1. **site_list**
- Stores authoritative list of valid sites
- Includes both `name` and `site_name` columns for compatibility
- `online` flag to indicate active sites
- Proper indexing for performance

### 2. **authorized_updates**
- Stores TeamCity pipeline updates
- `hash_value` NULL indicates unprocessed updates
- Unix timestamp for cross-platform compatibility
- Partial index on `update_path` for long paths
- Composite index for efficient unprocessed queries

### 3. **site_pipeline_status**
- Tracks pipeline completion for each site
- Foreign key relationship with site_list
- Timestamps for audit trail
- Optional pipeline run ID for traceability

### 4. **Performance Considerations**
- Proper indexing for all common query patterns
- UTF8MB4 charset for full Unicode support
- InnoDB engine for ACID compliance and foreign keys
- Composite indexes for multi-column queries

### 5. **Sample Data**
- Test data for all tables
- Examples of both processed and unprocessed updates
- Various site states for testing

### 6. **Useful Views**
- `v_unprocessed_updates`: Human-readable pending updates
- `v_site_pipeline_summary`: Overall pipeline status

This schema supports all the operations in your pipeline class and provides good performance characteristics for typical usage patterns.