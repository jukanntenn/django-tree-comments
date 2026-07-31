-- Performance harness MySQL initialization script.
-- Executed automatically by the MySQL image on the container's first start
-- (/docker-entrypoint-initdb.d/).
--
-- Purpose: Django tests need to create a test_<dbname> test database, and the
-- ordinary user created via MYSQL_USER does not have CREATE DATABASE privileges
-- by default. This explicitly grants the global database-creation privilege so
-- that it remains in effect after container restarts.
-- Contrast: PostgreSQL's POSTGRES_USER is a superuser by default and can create
-- databases, so this step is not required there.

GRANT ALL PRIVILEGES ON *.* TO 'treecomments'@'%';
FLUSH PRIVILEGES;
