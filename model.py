from pydantic import BaseModel, EmailStr,  StringConstraints, Field
from typing import Annotated

class RegisterData(BaseModel):
    account: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    password: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    email: EmailStr

class LoginData(BaseModel):
    account : Annotated[str, StringConstraints(strip_whitespace=True)]
    password : Annotated[str, StringConstraints(strip_whitespace=True)]

class UserUpdate(BaseModel):
    fullname: Annotated[str, StringConstraints(strip_whitespace=True)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True)]
    email: Annotated[EmailStr, StringConstraints(strip_whitespace=True)]
    level: Annotated[int, StringConstraints(strip_whitespace=True)]

class CartItem(BaseModel):
    name: str
    price: int = Field(ge=0)
    img: str
    quantity: int = Field(ge=1)