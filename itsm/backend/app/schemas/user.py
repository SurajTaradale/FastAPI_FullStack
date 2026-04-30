from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserSchema(BaseModel):
    title: Optional[str] = None
    first_name: str
    last_name: str
    login: str
    password: Optional[str] = None
    email: EmailStr
    valid_id: int
    mobile: Optional[str] = None
