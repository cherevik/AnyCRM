"""Database models and initialization for AnyCRM."""
import sqlite3
from contextlib import contextmanager
from typing import Optional


DATABASE_NAME = "anycrm.db"


def init_database():
    """Initialize the database with accounts and contacts tables."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            industry TEXT,
            website TEXT,
            notes TEXT,
            state INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            title TEXT,
            email TEXT,
            linkedin TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
        )
    """)
    
    # Create contact_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            contact_type TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
        )
    """)
    
    # Migration: Add updated_at column if it doesn't exist
    try:
        cursor.execute("SELECT updated_at FROM accounts LIMIT 1")
    except sqlite3.OperationalError:
        # SQLite doesn't support non-constant defaults in ALTER TABLE
        cursor.execute("ALTER TABLE accounts ADD COLUMN updated_at TIMESTAMP")
        cursor.execute("UPDATE accounts SET updated_at = created_at")
    
    try:
        cursor.execute("SELECT updated_at FROM contacts LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE contacts ADD COLUMN updated_at TIMESTAMP")
        cursor.execute("UPDATE contacts SET updated_at = created_at")

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row):
    """Convert sqlite3.Row to dictionary."""
    if row is None:
        return None
    return dict(zip(row.keys(), row))
