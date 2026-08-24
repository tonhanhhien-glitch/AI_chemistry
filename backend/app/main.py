from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router

app = FastAPI(
    title="VSEPR-AI",
    version="0.1.0",
    description="AI-powered Lewis Structure & VSEPR Analysis"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "name": "VSEPR-AI",
        "status": "running"
    }