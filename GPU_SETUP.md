# GPU Setup для FirstYarusOCR

## Требования

### Системные требования
- NVIDIA GPU с поддержкой CUDA
- Docker с поддержкой NVIDIA Container Toolkit
- Минимум 8GB RAM
- Минимум 10GB свободного места на диске

### Установка NVIDIA Container Toolkit

#### Ubuntu/Debian
```bash
# Установка Docker (если не установлен)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Перезапуск Docker
sudo systemctl restart docker
```

#### macOS
⚠️ **Внимание**: macOS не поддерживает NVIDIA GPU в Docker.
Для macOS контейнер будет работать в CPU режиме (значительно медленнее).

## Проверка GPU

Проверьте что GPU доступен:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Должен вывестись список доступных GPU.

## Запуск

### С GPU (Linux)
```bash
docker-compose up --build
```

Docker Compose автоматически использует GPU благодаря настройке в `docker-compose.yml`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Без GPU (macOS или системы без NVIDIA GPU)

Отредактируйте `docker-compose.yml` и закомментируйте секцию `deploy`:
```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

Затем запустите:
```bash
docker-compose up --build
```

⚠️ **Внимание**: В CPU режиме обработка одного паспорта Qwen3-VL займет ~30-60 секунд вместо ~2-5 секунд на GPU.

## Мониторинг использования GPU

Во время работы контейнера можно мониторить GPU:
```bash
watch -n 1 nvidia-smi
```

## Объём и производительность

### Размер Docker образа
- С Tesseract + Qwen3-VL: ~4-5GB
- Модель Qwen3-VL: ~2GB (кешируется в volume)

### Первый запуск
При первом запуске модель Qwen3-VL будет загружена из HuggingFace (~2GB).
Это займет 5-10 минут в зависимости от скорости интернета.

### Время обработки (примерно)
- **Tesseract** (passport, inn, snils, migration_card): 10-30 секунды
- **Qwen3-VL** (passport_qwen) на GPU: 2-5 секунд
- **Qwen3-VL** (passport_qwen) на CPU: 30-60 секунд

## Логи

### Логи приложения
```bash
# Просмотр в реальном времени
docker-compose logs -f ocr-api

# Последние 100 строк
docker-compose logs --tail=100 ocr-api
```

### Логи обработки файлов
Все обработанные файлы сохраняются в `./logs/`:
```
logs/
└── 20251209_143052_passport_photo_a1b2c3d4/
    ├── input_image.jpg
    ├── result.json
    └── metadata.json
```

Логи автоматически удаляются через 30 дней.

## Troubleshooting

### Ошибка: "could not select device driver"
```bash
# Проверьте что NVIDIA Container Toolkit установлен
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Ошибка: "CUDA out of memory"
Уменьшите размер батча или используйте GPU с большим объёмом памяти (минимум 6GB VRAM).

### Модель загружается долго
При первом запуске модель скачивается с HuggingFace. Используйте быстрое интернет-соединение.

### Контейнер не видит GPU
```bash
# Проверьте что GPU виден в Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Проверьте логи контейнера
docker logs firstyarus-ocr-api
```

В логах должно быть:
```
Qwen3-VL: Использование устройства - cuda
```

## Использование API

### Tesseract OCR (старый)
```bash
curl -X POST "http://localhost:8004/api/ocr/upload-image?document_type=passport" \
  -F "file=@passport.jpg"
```

### Qwen3-VL OCR (новый, мультиязычный)
```bash
curl -X POST "http://localhost:8004/api/ocr/upload-image?document_type=passport_qwen" \
  -F "file=@passport.jpg"
```

## Доступные типы документов

- `passport` - Паспорт РФ (Tesseract)
- `passport_qwen` - Паспорт мультиязычный (Qwen3-VL) ⭐ **Новое!**
- `migration_card` - Миграционная карта (Tesseract)
- `inn` - ИНН (Tesseract)
- `snils` - СНИЛС (Tesseract)

## Swagger документация

После запуска доступна по адресу:
```
http://localhost:8004/docs
```
