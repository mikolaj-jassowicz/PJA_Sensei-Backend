from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .hint_manager import HintManager
from .models import TutorRequestPayload, TutorResponsePayload


load_dotenv()

app = FastAPI(title="PJASensei Socratic Tutor API")
hint_manager = HintManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "Invalid tutor request."})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post(
    "/api/tutor/hint",
    response_model=TutorResponsePayload,
    response_model_exclude_none=True,
)
async def tutor_hint(payload: TutorRequestPayload) -> TutorResponsePayload:
    try:
        return await hint_manager.handle_tutor_request(payload)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/tutor/session/{session_id}")
async def reset_session(session_id: str) -> dict[str, bool]:
    return {"deleted": hint_manager.reset_session(session_id)}
