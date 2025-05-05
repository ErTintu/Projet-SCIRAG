"""
Database migration runner for SCIRAG.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment."""
    load_dotenv()
    return os.getenv("DATABASE_URL", "postgresql://localhost:5432/scirag")


def parse_database_url(url):
    """Parse database URL into components."""
    # Remove protocol
    url = url.replace("postgresql://", "")
    
    # Extract user:pass@host:port/dbname
    if "@" in url:
        auth, host_info = url.split("@")
        if ":" in auth:
            user, password = auth.split(":")
        else:
            user, password = auth, None
    else:
        user, password = None, None
        host_info = url
    
    if "/" in host_info:
        host_port, dbname = host_info.split("/")
    else:
        host_port, dbname = host_info, "scirag"
    
    if ":" in host_port:
        host, port = host_port.split(":")
    else:
        host, port = host_port, "5432"
    
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "dbname": dbname,
    }


def create_database_if_not_exists():
    """Create database if it doesn't exist."""
    db_url = get_database_url()
    db_params = parse_database_url(db_url)
    
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_params["user"],
            password=db_params["password"],
            host=db_params["host"],
            port=db_params["port"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_params["dbname"],)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_params["dbname"]}"')
            logger.info(f"Database '{db_params['dbname']}' created successfully")
        else:
            logger.info(f"Database '{db_params['dbname']}' already exists")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False


def run_migration(migration_file):
    """Run a single migration file."""
    db_url = get_database_url()
    db_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(
            dbname=db_params["dbname"],
            user=db_params["user"],
            password=db_params["password"],
            host=db_params["host"],
            port=db_params["port"],
        )
        cursor = conn.cursor()
        
        # Read and execute migration file
        with open(migration_file, "r") as f:
            sql = f.read()
        
        cursor.execute(sql)
        conn.commit()
        
        logger.info(f"Migration {os.path.basename(migration_file)} executed successfully")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error running migration {migration_file}: {e}")
        return False


def run_all_migrations():
    """Run all migration files in order."""
    migrations_dir = os.path.dirname(__file__)
    migration_files = sorted(
        [f for f in os.listdir(migrations_dir) if f.endswith(".sql")]
    )
    
    if not migration_files:
        logger.warning("No migration files found")
        return
    
    logger.info(f"Found {len(migration_files)} migration file(s)")
    
    for migration_file in migration_files:
        full_path = os.path.join(migrations_dir, migration_file)
        logger.info(f"Running migration: {migration_file}")
        
        if not run_migration(full_path):
            logger.error(f"Migration failed at {migration_file}")
            sys.exit(1)
    
    logger.info("All migrations completed successfully")


def main():
    """Main function."""
    logger.info("Starting database migration process")
    
    # Create database if it doesn't exist
    if not create_database_if_not_exists():
        logger.error("Failed to create database")
        sys.exit(1)
    
    # Run all migrations
    run_all_migrations()
    
    logger.info("Migration process completed")


if __name__ == "__main__":
    main()