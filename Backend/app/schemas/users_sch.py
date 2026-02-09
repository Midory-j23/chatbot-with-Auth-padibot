# schemas/users_sch.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime  # Make sure this is imported here

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # Use ConfigDict for Pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"