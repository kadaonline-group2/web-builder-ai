import json
from fastapi import APIRouter, HTTPException
from app.models import GenerateRequest, GenerateResponse, ReviseRequest
from app.services.llm_service import generate_website_state, revise_website_state, merge_state

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


@router.post("/api/v1/revise", response_model=GenerateResponse)
async def revise(req: ReviseRequest):
    try:
        partial = revise_website_state(json.dumps(req.currentState), req.instruction)
        merged = merge_state(req.currentState, partial)
        return GenerateResponse(**merged)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "LLM_SERVICE_FAILURE",
                    "message": f"Failed to revise website: {str(e)}",
                }
            },
        )
