from pydantic import BaseModel , Field, EmailStr, StringConstraints
from typing import Annotated

#=======carts models=======================
class AddToCartRequest(BaseModel):
    name: str
    quantity: int = Field(ge=1) 

class SetQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)
#==========login models================
class LoginData(BaseModel):
    account: str
    password: str    

#===========products models ============
class ProductUpdate(BaseModel):
    price: int | None = None
    description: str | None = None
    img: str | None = None

class ProductBuild(BaseModel):
    name: str 
    price: int 
    description: str 
    img: str 
#========register models============

class RegisterData(BaseModel):
    account: str
    password: str
    username: str
    phone: str
    email: EmailStr

#=========users models =========
class UserUpdate(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True)]
    phone: Annotated[str, StringConstraints(strip_whitespace=True)]
    email: EmailStr
    level: int