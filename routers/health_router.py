from fastapi import APIRouter

router = APIRouter()

# API đầu tiên
@router.get("/")
def root():
    return {
        "message": "AI Chemistry Backend is running!"
    }

@router.get("/health")
def health():
    return {
        "status": "OK",
        "version": "1.0.0",
        "backend": "AI Chemistry"
    }

# API kiểm tra kết nối
@router.get("/ping")
def ping():
    return {
        "message": "pong"
    }