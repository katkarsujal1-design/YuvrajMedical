-- Run against existing MySQL installations; safe to run more than once.
SET @drop_staff_religion = (
    SELECT IF(COUNT(*) > 0,
              'ALTER TABLE staff DROP COLUMN religion',
              'SELECT 1')
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'staff'
      AND column_name = 'religion'
);
PREPARE migration FROM @drop_staff_religion;
EXECUTE migration;
DEALLOCATE PREPARE migration;
