from fastapi import APIRouter, HTTPException
from app.models import GenerateRequest, GenerateResponse
from app.services.llm_service import generate_website_state

router = APIRouter()


@router.post("/api/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        data, is_fallback = generate_website_state(req.businessDescription)
        return GenerateResponse(**data, isFallback=is_fallback)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "LLM_SERVICE_FAILURE",
                    "message": f"Failed to generate website: {str(e)}",
                }
            },
        )
