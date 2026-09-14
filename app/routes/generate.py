import json
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.models import GenerateRequest, GenerateResponse, ReviseRequest
from app.services.llm_service import generate_website_state, revise_website_state, merge_state, diff_paths, validate_website_state

router = APIRouter()


def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


@router.post("/api/v1/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    request_id = generate_request_id()
    start = time.time()
    try:
        data, is_fallback = generate_website_state(req.businessDescription)
        latency_ms = int((time.time() - start) * 1000)
        return GenerateResponse(**data, isFallback=is_fallback)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Failed to generate website: {str(e)}",
                }
            },
        )


@router.post("/api/v1/revise", response_model=GenerateResponse)
async def revise(req: ReviseRequest):
    request_id = generate_request_id()
    start = time.time()
    try:
        partial = revise_website_state(json.dumps(req.currentState), req.instruction)

        if not partial or partial == {}:
            latency_ms = int((time.time() - start) * 1000)
            return GenerateResponse(**req.currentState, isFallback=True)

        merged = merge_state(req.currentState, partial)
        is_valid, _ = validate_website_state(merged)

        if not is_valid:
            latency_ms = int((time.time() - start) * 1000)
            return GenerateResponse(**req.currentState, isFallback=True)

        changed = diff_paths(req.currentState, merged)
        latency_ms = int((time.time() - start) * 1000)
        return GenerateResponse(**merged, isFallback=False)
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return GenerateResponse(**req.currentState, isFallback=True)
