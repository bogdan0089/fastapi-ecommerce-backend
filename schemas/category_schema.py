from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str

class ResponseCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str