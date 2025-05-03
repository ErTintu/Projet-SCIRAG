# Database Management for SCIRAG

This directory contains all database-related code for the SCIRAG application.

## Structure

```
db/
├── models/           # SQLAlchemy models
│   ├── llm.py       # LLM configuration models
│   ├── conversation.py  # Conversation and message models
│   ├── rag.py       # RAG corpus and document models
│   └── note.py      # Note models
├── migrations/       # Database migrations
│   ├── 001_initial_schema.sql
│   └── run_migrations.py
├── utils/           # Database utility functions
│   └── database.py  # Helper functions
└── connection.py    # Database connection management
```

## Setup

1. Ensure PostgreSQL is installed and running
2. Create the database:
   ```bash
   createdb scirag
   ```
3. Enable required extensions:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "vector";
   ```

## Environment Variables

Configure the following in your `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/scirag
DATABASE_ECHO=false  # Set to true for SQL query logging
```

## Running Migrations

To initialize or update the database schema:

```bash
cd backend
python -m db.migrations.run_migrations
```

## Testing Models

Run the model tests to ensure everything is working:

```bash
cd backend
pytest tests/test_models.py -v
```

## Using Models in Code

Example usage:

```python
from db.connection import get_db
from db.models import Conversation, Message

# In a FastAPI route
def create_conversation(db: Session = Depends(get_db)):
    conversation = Conversation(title="New Chat")
    db.add(conversation)
    db.commit()
    return conversation
```

## Vector Support

The database includes support for vector operations using pgvector. Embeddings are stored in the `document_chunks` and `note_chunks` tables with dimension 384 (for all-MiniLM-L6-v2).

## Utility Functions

The `db.utils.database` module provides helpful functions:

- `get_or_create()`: Get existing or create new instance
- `update_or_create()`: Update existing or create new instance
- `bulk_create()`: Create multiple instances efficiently
- `paginate()`: Paginate query results
- `safe_commit()`: Safely commit with error handling