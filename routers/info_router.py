from fastapi import APIRouter

router = APIRouter()

# API giới thiệu về dự án
@router.get("/about")
def about():
    return {
        "project": "AI Chemistry",
        "purpose": "Hỗ trợ dạy và học cấu trúc Lewis, VSEPR và mô hình 3D.",
        "supported": [
            "Lewis Structure",
            "VSEPR",
            "3D Structure",
            "Basic Properties"
        ]
    }

# API trả về thông tin phiên bản Backend
@router.get("/version")
def version():
    return {
        "name": "AI Chemistry API",
        "version": "1.0.0",
        "author": "Ton Hanh Hien",
        "python": "3.14",
        "framework": "FastAPI"
    }

# API chào người dùng
@router.get("/hello")
def hello(name: str):
    return {
        "message": f"Xin chào {name}!"
    }