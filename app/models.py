from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    businessDescription: str = Field(
        ..., min_length=1, description="Deskripsi bisnis dalam bahasa Indonesia"
    )


class GenerateResponse(BaseModel):
    templateId: str
    theme: dict
    meta: dict
    hero: dict
    about: dict
    services_products: list
    testimonials: list = []
    contact: dict
    isFallback: bool = False


class ReviseRequest(BaseModel):
    currentState: dict = Field(..., description="WebsiteState saat ini")
    instruction: str = Field(..., min_length=1, description="Instruksi revisi dari pengguna")
