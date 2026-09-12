# Revise Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `POST /api/v1/revise` endpoint that merges partial LLM changes with current WebsiteState.

**Architecture:** Add merge function, ReviseRequest model, and route that calls existing `revise_website_state()` then merges result with currentState.

**Tech Stack:** FastAPI, existing llm_service

## Global Constraints

- Endpoint path: `POST /api/v1/revise` (from API Contract §3)
- Request: `{ "currentState": WebsiteState, "instruction": "string" }`
- Response: Full merged WebsiteState (not partial diff)
- State is stateless — client sends full currentState each request

---

### Task 1: Add merge_state function

**Files:**
- Modify: `app/services/llm_service.py`

**Interfaces:**
- Consumes: current_state (dict), partial_changes (dict)
- Produces: merged full state (dict)

- [ ] **Step 1: Add merge_state function**

```python
def merge_state(current_state: dict, partial_changes: dict) -> dict:
    """Merge partial LLM changes into current state."""
    merged = copy.deepcopy(current_state)
    for key, value in partial_changes.items():
        if key not in merged:
            continue
        if isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update(value)
        elif isinstance(value, list) and isinstance(merged[key], list):
            merged[key] = value
        else:
            merged[key] = value
    return merged
```

- [ ] **Step 2: Verify function works**

Run: `python -c "from app.services.llm_service import merge_state; print(merge_state({'a': 1, 'b': 2}, {'b': 3}))"`
Expected: `{'a': 1, 'b': 3}`

---

### Task 2: Add ReviseRequest model

**Files:**
- Modify: `app/models.py`

**Interfaces:**
- Consumes: None
- Produces: `ReviseRequest` model

- [ ] **Step 1: Add ReviseRequest to models.py**

```python
class ReviseRequest(BaseModel):
    currentState: dict = Field(..., description="WebsiteState saat ini")
    instruction: str = Field(..., min_length=1, description="Instruksi revisi dari pengguna")
```

- [ ] **Step 2: Verify model works**

Run: `python -c "from app.models import ReviseRequest; print('OK')"`

---

### Task 3: Add revise route

**Files:**
- Modify: `app/routes/generate.py`

**Interfaces:**
- Consumes: `ReviseRequest`, `revise_website_state()`, `merge_state()`
- Produces: Full merged WebsiteState

- [ ] **Step 1: Add revise endpoint**

```python
from app.services.llm_service import revise_website_state, merge_state

@router.post("/api/v1/revise", response_model=GenerateResponse)
async def revise(req: ReviseRequest):
    try:
        partial = revise_website_state(json.dumps(req.currentState), req.instruction)
        merged = merge_state(req.currentState, partial)
        return GenerateResponse(**merged)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"code": "LLM_SERVICE_FAILURE", "message": str(e)}})
```

- [ ] **Step 2: Verify server starts**

Run: `python -c "from app.main import app; print('OK')"`

---

### Task 4: Test the endpoint

**Files:**
- None

- [ ] **Step 1: Test with valid input**

```bash
python -c "
import requests, json
url = 'http://127.0.0.1:8000/api/v1/revise'
data = {
    'currentState': {'templateId': 'template-fnb', 'hero': {'title': 'Old Title'}},
    'instruction': 'Ganti title jadi Nasi Goreng Enak'
}
r = requests.post(url, json=data)
print(r.status_code, r.json().get('hero', {}).get('title'))
"
```

Expected: 200 + updated title

---

### Task 5: Commit

- [ ] **Step 1: Stage and commit**

```bash
git add app/models.py app/routes/generate.py app/services/llm_service.py
git commit -m "feat: add POST /api/v1/revise endpoint"
```
