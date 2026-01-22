# 🚨 Widget Network Error - Diagnostic Report

**Date:** January 22, 2026  
**Issue:** Network error on talking to widget agent at widget.lemontechno.org  
**Severity:** CRITICAL

---

## 1. BACKEND ARCHITECTURE PROBLEMS

### Problem 1.1: Duplicate Endpoint Definitions ⚠️
**File:** `app/main.py`  
**Impact:** CRITICAL - Routing broken

The file has **MASSIVE DUPLICATION** starting at line 300. Multiple routes are defined twice:
- `/chat` endpoint (lines ~105 and ~1000+)
- `/admin/prompt` (lines ~150 and ~1000+)
- `/admin/history` (lines ~250 and ~1000+)
- `/admin/leads` and more...

**Result:** Only the LAST definition is registered. Entire routing is unpredictable.

### Problem 1.2: Modular Routes Never Imported ⚠️
**Files:** 
- `app/routes/chat.py` (proper implementation!)
- `app/routes/leads.py` (proper implementation!)
- `app/routes/admin.py` (proper implementation!)
- `app/routes/clinics.py`
- `app/main.py` (never imports these)

**Impact:** CRITICAL - The good, clean implementations in `app/routes/` are NEVER used! The app ignores them completely.

**Current behavior:**
```python
# app/main.py has old hardcoded implementation
# app/routes/ has clean modular implementation
# Result: app/routes/ is dead code, never called
```

### Problem 1.3: Conflicting Architecture ⚠️
**Two completely different implementations exist:**

**Old (in main.py):**
- In-memory storage (CHAT_LOGS, LEADS, SESSIONS)
- No database persistence
- All endpoints hardcoded

**New (in app/routes/):**
- Uses Supabase database
- Uses Redis for rate limiting
- Proper async implementation
- Better error handling

**Result:** The app is a Frankenstein of both approaches. Routing is unpredictable.

### Problem 1.4: Missing Route Registration ⚠️
**File:** `app/main.py` - Missing these critical imports:

```python
# MISSING - Should be present but isn't!
from app.routes import chat, leads, admin, clinics, public
app.include_router(chat.router)
app.include_router(leads.router, prefix="/lead")
app.include_router(leads.router2, prefix="/leads")
app.include_router(admin.router)
app.include_router(clinics.router)
app.include_router(public.router)
```

### Problem 1.5: Database Not Initialized ⚠️
**File:** `app/main.py`
- No startup event to initialize Redis connection
- No Supabase client setup
- Missing CORS configuration for actual deployed domain

---

## 2. FRONTEND WIDGET PROBLEMS

### Problem 2.1: Variable Scope Error ⚠️
**File:** `static/widget.js` (line ~280)

```javascript
async function submitLead(ui, state) {
    // ... code ...
    const res = await fetch(`${opts.apiUrl}/leads`, {  // ❌ opts is undefined here!
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            clinic_id: opts.clinicId,  // ❌ opts is undefined
            session_id: state.sessionId, 
            name, phone, message 
        })
    });
}
```

**Impact:** CRITICAL - Lead submission endpoint will fail with "opts is not defined"

**Root cause:** `opts` is only available inside `init()` and `sendMessage()` functions. `submitLead()` needs access to it.

### Problem 2.2: Missing Error Details ⚠️
**File:** `static/widget.js`

Widget catches network errors but doesn't provide enough debugging info:
```javascript
} catch (err) {
    const msg = err?.message || err;
    addMessage(ui.messages, `Network error: ${msg}`, "bot");  // Too generic
}
```

Should include:
- Response status
- Server URL being called
- Full error details

### Problem 2.3: Hard-Coded Default API URL ⚠️
**File:** `static/widget.js` (line ~13)

```javascript
const defaultOptions = {
    apiUrl: "http://localhost:8000",  // ❌ Will never work in production!
    clinicId: "",
    buttonLabel: "Chat with us",
    title: "Dental Assistant",
};
```

When embedded on `widget.lemontechno.org`, the widget tries to reach `http://localhost:8000` instead of your actual API domain.

---

## 3. ENVIRONMENT CONFIGURATION PROBLEMS

### Problem 3.1: Supabase Not Configured ⚠️
**File:** `app/config.py`

```python
supabase_url: str = Field(default="", alias="SUPABASE_URL")
supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
```

If these env vars are missing:
- `get_supabase_client()` will raise `RuntimeError` ❌
- All database queries will fail
- No fallback to in-memory storage

### Problem 3.2: Redis Not Initialized ⚠️
**File:** `app/rate_limit.py`

```python
async def _redis_limit(request: Request, max_requests: int, window_seconds: int):
    try:
        r = request.app.state.redis  # ❌ This attribute is never set!
    except Exception:
        r = None  # Falls back to in-memory
```

Redis connection is never established in startup event.

---

## 4. CORS & NETWORK PROBLEMS

### Problem 4.1: Wildcard CORS in Code but Production Domain Unknown ⚠️
**File:** `app/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This works but is too permissive
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This should use:
```python
ALLOWED_ORIGINS = settings.allowed_origins_list()
# Then restrict to actual domains
```

### Problem 4.2: Widget Domain Not Trusted ⚠️
The widget on `widget.lemontechno.org` should be explicitly allowed.

---

## 5. DEPENDENCY & IMPORT ISSUES

### Missing imports in app/main.py:
```python
# Currently missing:
from app.routes import chat, leads, admin, clinics, public

# Missing startup setup:
@app.on_event("startup")
async def startup():
    # Initialize Redis
    # Initialize Supabase
    pass
```

### Unused imports cluttering the codebase:
- `app.db` module is obsolete
- `app/routes/clinics.py` references `app.db` which is not Supabase

---

## 6. VERSION MISMATCH

There appear to be **TWO GENERATIONS** of this codebase:

**Generation 1 (OLD - in main.py):**
- Single file monolithic design
- In-memory storage
- Simple hardcoded routes

**Generation 2 (NEW - in app/routes/):**
- Modular design
- Supabase integration
- Async streams
- Rate limiting with Redis

**Problem:** Code is mixing both versions! The new version is never actually used because the old version is in `main.py` and never imports the new routes.

---

## RECOMMENDED FIXES

### Immediate (Blocking Issues):
1. ✅ Refactor `app/main.py` to properly import and register routes from `app/routes/`
2. ✅ Fix widget.js `opts` scope issue in `submitLead()` function
3. ✅ Initialize Redis in FastAPI startup event
4. ✅ Set up Supabase client properly with error handling
5. ✅ Update widget.js to receive correct apiUrl from data attributes

### Short-term (Production Readiness):
6. ✅ Remove all duplicate code/endpoints from main.py
7. ✅ Remove `app/db.py` (obsolete in-memory store)
8. ✅ Add proper error logging
9. ✅ Configure CORS for actual domains (not wildcard)
10. ✅ Add request/response logging for debugging

### Medium-term (Quality):
11. ✅ Add health check endpoint
12. ✅ Add request validation
13. ✅ Add rate limit headers in response
14. ✅ Add proper exception handlers
15. ✅ Update dependencies (FastAPI 0.115 is old)

---

## NEXT STEPS
See `FIXES_IMPLEMENTATION.md` for detailed code changes.
