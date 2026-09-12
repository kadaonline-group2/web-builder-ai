# Strengthen Prompt + Edge Case Input Handling Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the LLM prompt more robust and add input validation to handle edge cases.

**Architecture:** Improve the system prompt with examples and stricter rules, add input sanitization before LLM calls.

**Tech Stack:** Python, regex for sanitization

## Global Constraints

- Must maintain backward compatibility with existing generate/revise functions
- Input validation happens before LLM call, not after
- Sanitization should not change valid inputs

---

### Task 1: Add Input Sanitization

**Files:**
- Modify: `app/services/llm_service.py`

**Interfaces:**
- Consumes: Raw user input string
- Produces: Sanitized input string

- [ ] **Step 1: Add sanitize_input function**

```python
import re

def sanitize_input(text: str) -> str:
    """Remove potentially dangerous content from user input."""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Strip script injection attempts
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    # Limit length to 2000 chars (NFR-05)
    if len(text) > 2000:
        text = text[:2000]
    return text.strip()
```

- [ ] **Step 2: Verify function works**

Run: `python -c "from app.services.llm_service import sanitize_input; print(sanitize_input('<script>alert(1)</script> Hello'))"`
Expected: "Hello"

---

### Task 2: Add Input Validation

**Files:**
- Modify: `app/services/llm_service.py`

**Interfaces:**
- Consumes: Sanitized input string
- Produces: Valid input or raises ValueError

- [ ] **Step 1: Add validate_input function**

```python
def validate_input(text: str) -> None:
    """Validate user input before LLM call. Raises ValueError if invalid."""
    if not text or not text.strip():
        raise ValueError("Deskripsi bisnis tidak boleh kosong")
    if len(text.strip()) < 3:
        raise ValueError("Deskripsi bisnis terlalu pendek")
```

- [ ] **Step 2: Verify function works**

Run: `python -c "from app.services.llm_service import validate_input; validate_input('')"`
Expected: ValueError: Deskripsi bisnis tidak boleh kosong

---

### Task 3: Integrate Sanitization into Generate

**Files:**
- Modify: `app/services/llm_service.py`

**Interfaces:**
- Consumes: Raw input from user
- Produces: Sanitized + validated input passed to LLM

- [ ] **Step 1: Update generate_website_state**

```python
def generate_website_state(business_desc: str) -> tuple[dict, bool]:
    try:
        # Sanitize and validate input
        business_desc = sanitize_input(business_desc)
        validate_input(business_desc)
        
        data = ask_llm(business_desc, GENERATE_SYSTEM_PROMPT)
        # ... rest of function
```

---

### Task 4: Strengthen System Prompt

**Files:**
- Modify: `app/services/llm_service.py`

**Interfaces:**
- Consumes: None
- Produces: Improved GENERATE_SYSTEM_PROMPT

- [ ] **Step 1: Add examples section to prompt**

Add after "SAFETY GUIDELINES":

```
# EXAMPLES

Contoh input yang baik:
- "Warung makan Bu Sari, menjual nasi goreng dan mie ayam"
- "Toko Budi Jaya, jual pakaian bekas berkualitas"
- "Bengkel Motor Mas Andi, service dan spare part"

Contoh output yang valid:
{
  "templateId": "template-fnb",
  "theme": { "primaryColor": "#E67E22", "accentColor": "#D35400", "fontFamily": "sans" },
  "meta": { "businessName": "Warung Bu Sari", "category": "Kuliner", "tagline": "Nasi Goreng Enak dan Murah" },
  ...
}

Contoh input yang TIDAK boleh ditolak (tetap hasilkan JSON):
- "" (kosong) → gunakan default
- "toko" (terlalu pendek) → infer dari kata "toko"
- "aku lapar" (bukan bisnis) → gunakan default netral
```

- [ ] **Step 2: Verify prompt updated**

Run: `python -c "from app.services.llm_service import GENERATE_SYSTEM_PROMPT; print('EXAMPLES' in GENERATE_SYSTEM_PROMPT)"`
Expected: True

---

### Task 5: Commit Changes

**Files:**
- `app/services/llm_service.py`

- [ ] **Step 1: Stage and commit**

```bash
git add app/services/llm_service.py
git commit -m "feat: add input sanitization, validation, and strengthen prompt"
```
