"""
User models for the IoTSphere platform.

This module defines user-related models including roles, permissions, and user profile structures
for authentication, authorization, and user management.
"""
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """
    Enum for user roles in the system.

    The roles are organized in order of increasing privileges:
    - READ_ONLY: Can only view data, cannot make changes
    - MAINTENANCE: Can view data and perform maintenance operations
    - FACILITY_MANAGER: Can manage devices and view all facility data
    - ADMIN: Has full system access
    """

    READ_ONLY = "read_only"
    MAINTENANCE = "maintenance"
    FACILITY_MANAGER = "facility_manager"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model with common fields."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.READ_ONLY
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Model for updating an existing user."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class User(UserBase):
    """Complete user model with system-generated fields."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = (
            True  # Updated from orm_mode=True for Pydantic v2 compatibility
        )


class UserInDB(User):
    """User model as stored in the database with hashed password."""

    hashed_password: str


class Token(BaseModel):
    """Authentication token model."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    """Token payload data."""

    sub: str  # User ID
    username: str
    role: UserRole
    exp: datetime  # Expiration timestamp
