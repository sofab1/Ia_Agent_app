from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class UserQuery(BaseModel):
    question: str
    user_id: int = 0
    name: str = "Anonymous"
    email: str = "anonymous@example.com"
    role: str = "guest"

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
