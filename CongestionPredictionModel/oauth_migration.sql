-- Add OAuth columns to users table
ALTER TABLE users 
ADD COLUMN email VARCHAR(255) UNIQUE AFTER username,
ADD COLUMN oauth_provider VARCHAR(50) AFTER password,
ADD COLUMN oauth_provider_id VARCHAR(255) AFTER oauth_provider,
ADD INDEX idx_oauth (oauth_provider, oauth_provider_id);

-- Make password nullable for OAuth users
ALTER TABLE users 
MODIFY COLUMN password VARCHAR(255) NULL;

-- Update existing users to have email
UPDATE users SET email = CONCAT(username, '@local.com') WHERE email IS NULL;
