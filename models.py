from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    """Model for user registration."""
    username: str
    password: str
    role: Optional[str] = 'user'


class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str


class FileDeleteRequest(BaseModel):
    """Model for file deletion request."""
    filename: str
    access_token: Optional[str] = None


class FileResponse(BaseModel):
    """Model for file operation response."""
    success: bool
    message: str
    filename: Optional[str] = None
