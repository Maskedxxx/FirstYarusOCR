from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.ocr_endpoints import router as ocr_router
from backend.app.utils.logger import ProcessLogger

# Создание экземпляра FastAPI
app = FastAPI(
    title="OCR API",
    description="API для распознавания текста с помощью Tesseract и Qwen3-VL",
    version="1.1.0"
)

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация директории для логов при старте приложения
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    ProcessLogger.initialize_log_directory()
    logger.info("✓ Логирование инициализировано")

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