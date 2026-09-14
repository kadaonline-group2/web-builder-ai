from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    businessDescription: str = Field(
        ..., min_length=10, max_length=4000, description="Deskripsi bisnis dalam bahasa Indonesia"
    )


class GenerateResponse(BaseModel):
    templateId: str
    theme: dict
    meta: dict
    hero: dict
    about: dict
    services: list
    testimonials: list = []
    contact: dict
    isFallback: bool = False


class ReviseRequest(BaseModel):
    currentState: dict = Field(..., description="WebsiteState saat ini")
    instruction: str = Field(..., min_length=1, description="Instruksi revisi dari pengguna")
