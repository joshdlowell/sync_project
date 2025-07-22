USE squishy_db;
GO

-- =====================================================
-- Table: pipeline_site_list
-- Purpose: Store site information for pipeline operations
-- =====================================================
CREATE TABLE pipeline_site_list (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255),
    site_name NVARCHAR(5) NOT NULL,
    online BIT DEFAULT 1,
    description NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),

    -- Unique constraints
    CONSTRAINT uk_pipeline_site_site_name UNIQUE (site_name)
);
GO

-- Create indexes for pipeline_site_list
CREATE INDEX idx_site_name ON pipeline_site_list (site_name);
CREATE INDEX idx_online ON pipeline_site_list (online);
GO

-- Create trigger for updated_at timestamp
CREATE TRIGGER tr_pipeline_site_list_updated_at
ON pipeline_site_list
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE pipeline_site_list
    SET updated_at = GETDATE()
    FROM pipeline_site_list p
    INNER JOIN inserted i ON p.id = i.id;
END;
GO

-- =====================================================
-- Table: authorized_updates
-- Purpose: Store TeamCity pipeline updates and their processing status
-- =====================================================
CREATE TABLE authorized_updates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    TC_id NVARCHAR(25) NOT NULL,
    timestamp BIGINT NOT NULL,
    update_path NVARCHAR(1000) NOT NULL,
    update_size BIGINT DEFAULT 0,
    hash_value NVARCHAR(64) DEFAULT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Create indexes for authorized_updates
CREATE INDEX idx_hash_value ON authorized_updates (hash_value);
CREATE INDEX idx_update_path ON authorized_updates (update_path);
CREATE INDEX idx_timestamp ON authorized_updates (timestamp);
CREATE INDEX idx_tc_id ON authorized_updates (TC_id);
CREATE INDEX idx_unprocessed ON authorized_updates (hash_value, timestamp);
GO

-- Create trigger for updated_at timestamp
CREATE TRIGGER tr_authorized_updates_updated_at
ON authorized_updates
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE authorized_updates
    SET updated_at = GETDATE()
    FROM authorized_updates a
    INNER JOIN inserted i ON a.id = i.id;
END;
GO
