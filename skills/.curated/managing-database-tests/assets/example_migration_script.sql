-- Example SQL migration script for database-test-manager plugin tests.
-- This script demonstrates basic table creation and data insertion.

-- Table creation:  Replace 'your_table_name' with your actual table name.
CREATE TABLE IF NOT EXISTS your_table_name (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data insertion:  Replace with your initial data.  Use Faker for more realistic data during testing.
INSERT INTO your_table_name (name, email) VALUES
('John Doe', 'john.doe@example.com'),
('Jane Smith', 'jane.smith@example.com');

-- Add an index (optional): Useful for optimizing queries.
CREATE INDEX idx_name ON your_table_name (name);

-- Add a constraint (optional): Enforces data integrity.  Example: email must be in valid format
-- ALTER TABLE your_table_name ADD CONSTRAINT chk_email CHECK (email LIKE '%@%.%');

-- INSERT additional test data (example for parameterized testing):
-- INSERT INTO your_table_name (name, email) VALUES ('${test_name}', '${test_email}'); -- Placeholder for test parameters

-- Add a new column (example migration):
-- ALTER TABLE your_table_name ADD COLUMN phone_number VARCHAR(20);

-- Drop a column (example migration):
-- ALTER TABLE your_table_name DROP COLUMN phone_number;

-- Rename a column (example migration):
-- ALTER TABLE your_table_name RENAME COLUMN old_column_name TO new_column_name;

-- Modify a column (example migration):
-- ALTER TABLE your_table_name MODIFY COLUMN name VARCHAR(100);

-- Example of a more complex query (useful for testing query performance):
-- SELECT * FROM your_table_name WHERE name LIKE '%John%' ORDER BY created_at DESC LIMIT 10;