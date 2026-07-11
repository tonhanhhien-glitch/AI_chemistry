from fastapi import FastAPI

from routers.formula_router import router as formula_router
from routers.health_router import router as health_router
from routers.info_router import router as info_router

# Tạo ứng dụng FastAPI
app = FastAPI(
    title="AI Chemistry API",
    version="1.0.0",
    description="Backend hỗ trợ dạy và học cấu trúc Lewis, VSEPR và mô hình 3D."
)

app.include_router(formula_router)
app.include_router(health_router)
app.include_router(info_router)