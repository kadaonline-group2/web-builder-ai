# First-Draft Generation API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a REST API endpoint `POST /api/v1/generate` that converts a business description into a structured WebsiteState JSON using the existing LLM service.

**Architecture:** Add FastAPI as the web framework, create request/response models, wire the existing `generate_website_state()` function to an HTTP endpoint, and add proper error handling per the API contract.

**Tech Stack:** FastAPI, Pydantic, uvicorn (existing: openai, python-dotenv)

## Global Constraints

- Endpoint path: `POST /api/v1/generate` (from API Contract §5, item #5)
- Response must include `isFallback` flag (from API Contract §2, item #2)
- HTTP 200 for success/fallback; HTTP 5xx for fatal LLM failure
- Request body: `{ "businessDescription": "string" }`
- Response body: `WebsiteState` object + `{ "isFallback": boolean }`

---

### Task 1: Add FastAPI Dependencies

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: None
- Produces: Updated requirements with FastAPI and uvicorn

- [ ] **Step 1: Update requirements.txt**

```txt
openai
python-dotenv
fastapi
uvicorn[standard]
pydantic
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Installation completes without errors

- [ ] **Step 3: Verify installation**

Run: `python -c "import fastapi; print(fastapi.__version__)"`
Expected: Version number printed (e.g., "0.104.1")

---

### Task 2: Create Request/Response Models

**Files:**
- Create: `app/models.py`

**Interfaces:**
- Consumes: None
- Produces: `GenerateRequest`, `GenerateResponse` models for the endpoint

- [ ] **Step 1: Create Pydantic models**

```python
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    businessDescription: str = Field(..., min_length=1, description="Deskripsi bisnis dalam bahasa Indonesia")


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
```

- [ ] **Step 2: Verify model works**

Run: `python -c "from app.models import GenerateRequest, GenerateResponse; print('Models OK')"`
Expected: "Models OK" printed

---

### Task 3: Create Generate Endpoint

**Files:**
- Create: `app/routes/__init__.py`
- Create: `app/routes/generate.py`
- Modify: `app/main.py`

**Interfaces:**
- Consumes: `GenerateRequest` from Task 2, `generate_website_state()` from llm_service
- Produces: `GenerateResponse` with WebsiteState + isFallback flag

- [ ] **Step 1: Create routes package**

```python
# app/routes/__init__.py
```

- [ ] **Step 2: Create generate route**

```python
# app/routes/generate.py
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
        raise HTTPException(status_code=500, detail=f"LLM service failed: {str(e)}")
```

- [ ] **Step 3: Update main.py to use FastAPI**

```python
# app/main.py
from fastapi import FastAPI
from app.routes.generate import router as generate_router

app = FastAPI(title="AI Website Builder for UMKM")
app.include_router(generate_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: Verify server starts**

Run: `python -m uvicorn app.main:app --reload`
Expected: Server starts on http://127.0.0.1:8000

---

### Task 4: Test the Endpoint

**Files:**
- None (testing only)

**Interfaces:**
- Consumes: Running FastAPI server
- Produces: Verified working endpoint

- [ ] **Step 1: Start server in background**

Run: `start python -m uvicorn app.main:app --reload`

- [ ] **Step 2: Test with curl**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate -H "Content-Type: application/json" -d "{\"businessDescription\": \"Warung makan Bu Sari, menjual nasi goreng dan mie ayam\"}"
```

Expected: JSON response with WebsiteState fields + `isFallback: false`

- [ ] **Step 3: Test with empty input**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate -H "Content-Type: application/json" -d "{\"businessDescription\": \"\"}"
```

Expected: HTTP 422 Validation Error

- [ ] **Step 4: Verify isFallback flag works**

Check the response from Step 2 — `isFallback` should be `false` for valid LLM output.

---

### Task 5: Add Error Handling for Fatal Failures

**Files:**
- Modify: `app/routes/generate.py`

**Interfaces:**
- Consumes: Exception from llm_service
- Produces: HTTP 500 for fatal errors, HTTP 200 for fallback

- [ ] **Step 1: Update error handling in generate route**

```python
# app/routes/generate.py
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
                    "message": f"Failed to generate website: {str(e)}"
                }
            }
        )
```

- [ ] **Step 2: Verify error handling**

Stop server, then restart and test with invalid input or mock LLM failure.

---

### Task 6: Commit Changes

**Files:**
- All modified/created files

**Interfaces:**
- Consumes: All previous tasks
- Produces: Committed code ready for review

- [ ] **Step 1: Stage all changes**

```bash
git add requirements.txt app/models.py app/routes/ app/main.py .opencode/plans/
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: add POST /api/v1/generate endpoint with retry/fallback"
```

- [ ] **Step 3: Verify commit**

Run: `git log --oneline -1`
Expected: Commit message displayed
