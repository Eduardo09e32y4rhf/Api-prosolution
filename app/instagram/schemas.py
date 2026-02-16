from pydantic import BaseModel, HttpUrl, Field

class InstagramPostSchema(BaseModel):
    image_url: HttpUrl = Field(..., example="https://example.com/image.jpg")
    caption: str = Field(..., min_length=1, max_length=2200)

    class Config:
        extra = "forbid"  # evita campos inválidos

from pydantic import BaseModel, HttpUrl


class InstagramPostRequest(BaseModel):
    image_url: HttpUrl
    caption: str