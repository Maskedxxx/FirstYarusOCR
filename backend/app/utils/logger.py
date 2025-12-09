"""
Система логирования для OCR запросов
"""
import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock


class ProcessLogger:
    """Логирование процесса обработки OCR с сохранением файлов и результатов"""

    # Базовая директория для логов
    BASE_LOG_DIR = Path("/app/logs")

    # Период хранения логов (в днях)
    LOG_RETENTION_DAYS = 30

    # Lock для thread-safe операций
    _lock = Lock()

    def __init__(self, request_id: str, original_filename: str):
        """
        Инициализация логгера для конкретного запроса

        Args:
            request_id: Уникальный ID запроса
            original_filename: Оригинальное имя файла
        """
        self.request_id = request_id
        self.original_filename = original_filename
        self.timestamp = datetime.now()

        # Формируем имя папки: YYYYMMDD_HHMMSS_filename_uuid
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        clean_filename = self._sanitize_filename(original_filename)
        folder_name = f"{timestamp_str}_{clean_filename}_{request_id[:8]}"

        # Полный путь к папке логов
        self.log_dir = self.BASE_LOG_DIR / folder_name

        # Создаём директорию
        self._create_log_directory()

        # Очищаем старые логи
        self._cleanup_old_logs()

    def _sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        # Убираем расширение и оставляем только базовое имя
        name = Path(filename).stem
        # Заменяем недопустимые символы
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        sanitized = ''.join(c if c in allowed_chars else '_' for c in name)
        # Ограничиваем длину
        return sanitized[:50] if sanitized else "unnamed"

    def _create_log_directory(self):
        """Создание директории для логов"""
        with self._lock:
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def save_input_file(self, file_content: bytes, file_extension: str = None):
        """
        Сохранение исходного файла

        Args:
            file_content: Содержимое файла в байтах
            file_extension: Расширение файла (если не указано, берётся из original_filename)
        """
        if file_extension is None:
            file_extension = Path(self.original_filename).suffix or '.jpg'

        if not file_extension.startswith('.'):
            file_extension = f'.{file_extension}'

        input_path = self.log_dir / f"input_image{file_extension}"

        with self._lock:
            with open(input_path, 'wb') as f:
                f.write(file_content)

    def save_result(self, result_data: Dict[str, Any]):
        """
        Сохранение результата обработки

        Args:
            result_data: Данные результата (будут сохранены в JSON)
        """
        result_path = self.log_dir / "result.json"

        with self._lock:
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

    def save_metadata(self,
                      document_type: str,
                      model_used: str,
                      processing_time: float,
                      file_size: int,
                      success: bool = True,
                      error: Optional[str] = None):
        """
        Сохранение метаданных обработки

        Args:
            document_type: Тип документа
            model_used: Использованная модель (tesseract, qwen3vl)
            processing_time: Время обработки в секундах
            file_size: Размер файла в байтах
            success: Успешность обработки
            error: Сообщение об ошибке (если есть)
        """
        metadata = {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "original_filename": self.original_filename,
            "document_type": document_type,
            "model_used": model_used,
            "processing_time_seconds": round(processing_time, 3),
            "file_size_bytes": file_size,
            "success": success,
            "error": error
        }

        metadata_path = self.log_dir / "metadata.json"

        with self._lock:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

    def log_complete_request(self,
                            file_content: bytes,
                            result_data: Dict[str, Any],
                            document_type: str,
                            model_used: str,
                            processing_time: float,
                            success: bool = True,
                            error: Optional[str] = None):
        """
        Полное логирование запроса (all-in-one метод)

        Args:
            file_content: Содержимое файла в байтах
            result_data: Данные результата
            document_type: Тип документа
            model_used: Использованная модель
            processing_time: Время обработки в секундах
            success: Успешность обработки
            error: Сообщение об ошибке (если есть)
        """
        # Сохраняем входной файл
        self.save_input_file(file_content)

        # Сохраняем результат
        self.save_result(result_data)

        # Сохраняем метаданные
        self.save_metadata(
            document_type=document_type,
            model_used=model_used,
            processing_time=processing_time,
            file_size=len(file_content),
            success=success,
            error=error
        )

    @classmethod
    def _cleanup_old_logs(cls):
        """Удаление логов старше LOG_RETENTION_DAYS дней"""
        if not cls.BASE_LOG_DIR.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=cls.LOG_RETENTION_DAYS)

        with cls._lock:
            for log_folder in cls.BASE_LOG_DIR.iterdir():
                if not log_folder.is_dir():
                    continue

                # Пытаемся извлечь дату из имени папки (формат: YYYYMMDD_HHMMSS_...)
                try:
                    date_str = log_folder.name[:8]  # YYYYMMDD
                    folder_date = datetime.strptime(date_str, "%Y%m%d")

                    if folder_date < cutoff_date:
                        shutil.rmtree(log_folder)
                except (ValueError, IndexError):
                    # Если не удалось распарсить дату, пропускаем
                    continue

    @classmethod
    def initialize_log_directory(cls):
        """Инициализация базовой директории для логов (вызывается при старте приложения)"""
        cls.BASE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls._cleanup_old_logs()
