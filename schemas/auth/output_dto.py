from pydantic import BaseModel, EmailStr


class TokenOutputDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    client_id: int
    email: EmailStr
    age: int
    name: str


class RefreshOutputDTO(BaseModel):
    access_token: str
