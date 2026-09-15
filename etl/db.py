"""
db.py

Shared database connection helper. Reads connection details from
environment variables (loaded from a .env file via python-dotenv)
so no credentials are ever hardcoded in source files.
"""

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "edu_dw")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_engine(echo: bool = False):
    """Returns a SQLAlchemy engine connected to the MySQL warehouse."""
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url, echo=echo, pool_pre_ping=True)
