from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.ocr_endpoints import router as ocr_router

# Создание экземпляра FastAPI
app = FastAPI(
    title="OCR API",
    description="API для распознавания текста с помощью pytesseract",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутера
app.include_router(ocr_router, prefix="/api")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "OCR API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )