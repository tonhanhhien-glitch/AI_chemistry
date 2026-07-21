"""FastAPI application entrypoint: creates the app, configures CORS, and mounts the v1 API router."""


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import ChemistryDomainError, FormulaParseError

app = FastAPI(title="VSEPR-AI", version="1.0.0", description="API giáo dục Lewis/VSEPR với bộ quy tắc xác định.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ChemistryDomainError)
async def chemistry_error_handler(
    _request: Request, exc: ChemistryDomainError
) -> JSONResponse:
    detail: dict[str, object] = {"code": exc.code, "message": exc.message}
    if exc.candidates is not None:
        detail["candidates"] = exc.candidates
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(FormulaParseError)
async def formula_error_handler(
    _request: Request, exc: FormulaParseError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )
