"""
SQLAlchemy Base declaration and core model setup.
This module defines the SQLAlchemy Base class used by all models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the SQLAlchemy base
Base = declarative_base()
