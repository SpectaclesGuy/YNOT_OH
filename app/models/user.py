from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    email: EmailStr
    display_name: str


class UserListResponse(BaseModel):
    data: list[UserOut]
