"""
Script to initialize the test database.
Run this script before running tests.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def main():
    """Initialize the test database."""
    load_dotenv()
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scirag")
    
    # Parse database URL
    db_parts = db_url.replace("postgresql://", "").split("/")
    db_auth_host = db_parts[0].split("@")
    
    auth = db_auth_host[0].split(":")
    host_port = db_auth_host[1].split(":")
    
    db_config = {
        "user": auth[0],
        "password": auth[1],
        "host": host_port[0],
        "port": host_port[1] if len(host_port) > 1 else "5432",
        "database": db_parts[1] if len(db_parts) > 1 else "scirag"
    }
    
    try:
        # Connect to PostgreSQL
        print(f"Connecting to PostgreSQL at {db_config['host']}:{db_config['port']} as {db_config['user']}...")
        conn = psycopg2.connect(
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"]
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Enable the vector extension
        print("Enabling vector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        
        # Check if the extension is enabled
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        
        if result and result[0] == 'vector':
            print("✅ Vector extension is enabled.")
        else:
            print("❌ Failed to enable vector extension.")
            return
        
        print("Database initialized successfully!")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()