# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface

# Устанавливаем системные зависимости для Tesseract OCR, OpenCV и Git
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    git \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаём директории для логов и кеша моделей
RUN mkdir -p /app/logs /app/.cache/huggingface

# Копируем файлы зависимостей
COPY backend/requirements.txt .

# Устанавливаем Python зависимости
# Увеличиваем timeout и устанавливаем transformers из git (как в colab)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout=600 -r requirements.txt && \
    pip install --no-cache-dir --timeout=600 "git+https://github.com/huggingface/transformers.git"

# Копируем код приложения
COPY . .

# Команда запуска
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
