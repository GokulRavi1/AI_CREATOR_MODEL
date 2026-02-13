from backend.database.session import engine, Base
from backend.database.models import Character, Generation, Tag
import sys
import os

# Add project root to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text

print("Creating database tables...")
try:
    # Enable vector extension
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()
        print("Enabled pgvector extension.")

    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
except Exception as e:
    print(f"Error creating tables: {e}")
