# Деплой на Hugging Face Inference Endpoints

## Шаг 1: Подготовка Docker образа

### 1.1 Билд образа локально
```bash
cd /Users/mask/Documents/Проеты_2025/FirstYarusOCR
docker build -t firstyarus-ocr-api:latest -f docker/Dockerfile .
```

### 1.2 Логин в Docker Hub
```bash
docker login
# Введите username и password от Docker Hub
```

### 1.3 Tag образа
```bash
# Замените YOUR_DOCKERHUB_USERNAME на ваш username
docker tag firstyarus-ocr-api:latest YOUR_DOCKERHUB_USERNAME/firstyarus-ocr-qwen:latest
```

### 1.4 Push в Docker Hub
```bash
docker push YOUR_DOCKERHUB_USERNAME/firstyarus-ocr-qwen:latest
```

---

## Шаг 2: Создание Inference Endpoint на Hugging Face

### 2.1 Перейдите на Hugging Face
```
https://huggingface.co/inference-endpoints
```

### 2.2 Создайте новый Endpoint
1. Нажмите **"New Endpoint"**
2. Заполните форму:

**Endpoint Configuration:**
- **Name**: `firstyarus-ocr-qwen`
- **Model Repository**: Выберите **"Custom Docker Image"**
- **Container Image URI**: `YOUR_DOCKERHUB_USERNAME/firstyarus-ocr-qwen:latest`

**Instance Configuration:**
- **Cloud Provider**: AWS (или другой доступный)
- **Region**: `us-east-1` (или ближайший)
- **Instance Type**:
  - Для тестов: **NVIDIA T4** (~$0.5/час)
  - Для прода: **NVIDIA L4** или **A10G**

**Advanced Settings:**
- **Container Port**: `80`
- **Health Check Path**: `/health`
- **Environment Variables** (опционально):
  ```
  API_PORT=80
  LOG_RETENTION_DAYS=30
  TRANSFORMERS_CACHE=/app/.cache/huggingface
  ```

### 2.3 Запустите Endpoint
Нажмите **"Create Endpoint"** и дождитесь деплоя (~5-10 минут первый раз).

---

## Шаг 3: Тестирование

### 3.1 Получите URL Endpoint
После деплоя вы получите URL типа:
```
https://xxxxxx.us-east-1.aws.endpoints.huggingface.cloud
```

### 3.2 Проверьте health
```bash
curl https://YOUR_ENDPOINT_URL/health
```

Должен вернуть:
```json
{"status": "healthy"}
```

### 3.3 Протестируйте OCR
```bash
# Tesseract (passport)
curl -X POST "https://YOUR_ENDPOINT_URL/api/ocr/upload-image?document_type=passport" \
  -H "Authorization: Bearer YOUR_HF_TOKEN" \
  -F "file=@/path/to/passport.jpg"

# Qwen3-VL (passport_qwen)
curl -X POST "https://YOUR_ENDPOINT_URL/api/ocr/upload-image?document_type=passport_qwen" \
  -H "Authorization: Bearer YOUR_HF_TOKEN" \
  -F "file=@/path/to/passport.jpg"
```

### 3.4 Swagger документация
```
https://YOUR_ENDPOINT_URL/docs
```

---

## Шаг 4: Мониторинг и логи

### Логи в Hugging Face UI
1. Перейдите в ваш Endpoint
2. Вкладка **"Logs"** покажет stdout контейнера
3. Вы увидите:
   ```
   INFO - Qwen3-VL: Использование устройства - cuda
   INFO - Qwen3-VL: Модель успешно загружена
   INFO - ✓ Логирование инициализировано
   ```

### Метрики
- CPU/GPU usage
- Memory usage
- Request latency
- Request count

---

## Стоимость (приблизительно)

| Instance Type | GPU | VRAM | Цена/час | Рекомендация |
|--------------|-----|------|----------|--------------|
| NVIDIA T4    | 1x  | 16GB | ~$0.50   | Тесты        |
| NVIDIA L4    | 1x  | 24GB | ~$1.00   | Production   |
| NVIDIA A10G  | 1x  | 24GB | ~$1.50   | High Load    |

**Пример теста:**
- 1 час тестов на T4 = **$0.50**
- 10 запросов OCR в час = копейки

---

## Troubleshooting

### Endpoint не стартует
1. Проверьте логи в HF UI
2. Убедитесь что образ публичный в Docker Hub
3. Проверьте что порт 80 указан корректно

### Модель не загружается
- Первый старт займёт ~5-10 минут (загрузка Qwen3-VL)
- Проверьте логи: должно быть "Модель успешно загружена"

### GPU не используется
Проверьте логи, должно быть:
```
Qwen3-VL: Использование устройства - cuda
```

Если видите `cpu` - проверьте что выбран GPU instance.

### Timeout на запросах
- Qwen3-VL на T4: 2-5 сек на запрос
- Если дольше - проверьте что GPU активен

---

## Альтернатива: Docker Space (с UI)

Если хотите веб-интерфейс:

1. Создайте Space на HF
2. Тип: **Docker**
3. Загрузите Dockerfile
4. Включите GPU в настройках Space
5. Space даст публичный URL с UI

---

## Полезные команды

```bash
# Проверить образ локально перед push
docker run -p 8004:80 --gpus all firstyarus-ocr-api:latest

# Логи локального контейнера
docker logs -f CONTAINER_ID

# Удалить образ из Docker Hub (если нужно)
# Через Docker Hub UI -> Repositories -> Settings -> Delete
```

---

## Итоговый чеклист

- [ ] Собрали образ локально
- [ ] Запушили в Docker Hub
- [ ] Создали Inference Endpoint на HF
- [ ] Проверили `/health`
- [ ] Протестировали `/api/ocr/upload-image`
- [ ] Проверили что GPU используется (логи)
- [ ] Проверили время ответа (~2-5 сек)
- [ ] Посмотрели метрики в HF UI

**Готово к production тестам!** 🚀
