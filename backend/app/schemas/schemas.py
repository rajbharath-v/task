# Make sure top of schemas.py has this:
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# --- Auth Schemas ---

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")   # ← indented inside class
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 characters or fewer")
        return v                   # ← don't forget this line

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# --- Task Schemas ---

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskOut]
    total: int
    page: int
    page_size: int
    total_pages: int
