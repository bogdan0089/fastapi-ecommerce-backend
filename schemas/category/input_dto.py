from pydantic import BaseModel, Field


class CategoryCreateDTO(BaseModel):
    name: str = Field(..., min_length=1)
