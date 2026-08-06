-- Run once, as an instance admin / superuser, against the shared Postgres instance.
-- Creates an isolated database + a dedicated least-privilege role for the DNS
-- self-service app. Postgres isolates databases from each other by default, so
-- this role will not be able to see or touch the other test application's
-- database at all.

-- 1. Dedicated login role for the app (change the password before running).
CREATE ROLE dns_selfservice_app WITH LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
ALTER ROLE dns_selfservice_app NOCREATEDB NOCREATEROLE NOSUPERUSER;

-- 2. Dedicated database owned by that role.
CREATE DATABASE dns_selfservice OWNER dns_selfservice_app;

-- 3. Connect to the new database and lock down the default schema so only
--    the app role can create/use objects in it (defense in depth).
\connect dns_selfservice

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO dns_selfservice_app;

-- After this:
--   1. Set DATABASE_URL in .env / App Service config, e.g.:
--      postgresql+psycopg2://dns_selfservice_app:<password>@<host>:5432/dns_selfservice?sslmode=require
--   2. Run `alembic upgrade head` to create all tables.
--   3. Run `python -m scripts.seed_users` to create the 6 local test users.
--   4. Store the password in Key Vault / App Service application settings — never commit it.
