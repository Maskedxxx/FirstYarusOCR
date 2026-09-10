# Образ демо FirstYarusOCR: Tesseract (rus/eng) + Qwen3-VL-2B на GPU Spark (GB10, CUDA 13).
# Отличия от docker/Dockerfile проекта: torch из cu130-индекса PyTorch (проверен на Spark), transformers
# закреплён релизом вместо git-master, версии — через deploy/constraints.txt. Контекст сборки — корень репо.
FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface API_PORT=80 LOG_RETENTION_DAYS=30
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN mkdir -p /app/logs
COPY backend/requirements.txt deploy/constraints.txt ./
# один вызов pip: cu130-индекс даёт torch/torchvision под CUDA 13, constraints закрепляют версии
RUN pip install --timeout=600 -c constraints.txt --extra-index-url https://download.pytorch.org/whl/cu130 -r requirements.txt
COPY . .
EXPOSE 80
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
