from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    content_type: str
    size_bytes: int = Field(gt=0)


class PresignResponse(BaseModel):
    upload_url: str
    key: str


class FotoConfirmar(BaseModel):
    key: str = Field(min_length=1, max_length=500)
    orden: int = Field(default=0, ge=0)
