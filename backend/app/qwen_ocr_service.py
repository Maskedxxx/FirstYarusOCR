"""
OCR сервис на основе Qwen3-VL-2B-Instruct для распознавания паспортов
"""
import json
import logging
from typing import Dict
import torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
import io

logger = logging.getLogger(__name__)


# Шаблон результата - ключи только на латинице
RESULT_TEMPLATE = {
    "LastName": "",
    "FirstName": "",
    "MiddleName": "",
    "DateOfBirth": "",
    "PlaceOfBirth": "",
    "PassportSeries": "",
    "PassportNumber": "",
    "IssueDate": "",
    "ExpirationDate": "",
    "IssuedBy": "",
    "DepartmentCode": "",
    "RegistrationAddress": ""
}


# Промпт для модели
OCR_PROMPT = """
You are an expert OCR and information extraction assistant for passports and identity documents.

The image contains a passport or ID document. The text can be in multiple languages
(for example Russian, English, Kazakh, Arabic, other European or Asian languages).

Your tasks:
1. Carefully read all printed and handwritten text on the document.
2. Extract the holder's data and map it into the following JSON fields
   with keys in English (Latin letters) ONLY:

   - "LastName"            : family name / surname
   - "FirstName"           : given name
   - "MiddleName"          : middle name / patronymic (if it does not exist, use an empty string "")
   - "DateOfBirth"         : date of birth in the format as written on the document
   - "PlaceOfBirth"        : place of birth (city/region/country as written)
   - "PassportSeries"      : passport series (if applicable, otherwise "")
   - "PassportNumber"      : passport number
   - "IssueDate"           : date when the passport was issued
   - "ExpirationDate"      : date when the passport expires (if not present on the document, use "")
   - "IssuedBy"            : issuing authority (who issued the passport)
   - "DepartmentCode"      : internal department code (if present, else "")
   - "RegistrationAddress" : address of registration/residence (if present, else "")

3. If some field is not clearly present on the document, or you are not sure,
   set its value to an empty string "".

4. IMPORTANT:
   - Return ONLY ONE JSON object.
   - Use exactly and only the keys listed above.
   - Do NOT add any explanations, comments, natural language text or markdown.
   - The JSON MUST be syntactically valid.
"""


class QwenOCRService:
    """Сервис OCR на основе Qwen3-VL для мультиязычных паспортов"""

    # ID модели на HuggingFace
    MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"

    def __init__(self):
        """Инициализация модели и процессора"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Qwen3-VL: Использование устройства - {self.device}")

        # Загрузка модели
        logger.info(f"Qwen3-VL: Загрузка модели {self.MODEL_ID}...")
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            self.MODEL_ID,
            torch_dtype="auto",
            device_map="auto",  # Автоматическое распределение по GPU/CPU
        )

        # Загрузка процессора
        self.processor = AutoProcessor.from_pretrained(self.MODEL_ID)

        logger.info("Qwen3-VL: Модель успешно загружена")

    def safe_parse_json(self, text: str) -> Dict:
        """
        Безопасный парсинг JSON из ответа модели

        Args:
            text: Текст ответа модели

        Returns:
            Словарь с распарсенными данными или пустой шаблон
        """
        text = text.strip()

        # Попытка прямого парсинга
        try:
            return json.loads(text)
        except Exception:
            pass

        # Попытка вырезать JSON между первой '{' и последней '}'
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            candidate = text[start:end]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Если не получилось - возвращаем пустой шаблон
        return RESULT_TEMPLATE.copy()

    def extract_passport_from_image(self, image_data: bytes) -> Dict:
        """
        Извлечение данных паспорта из изображения

        Args:
            image_data: Байты изображения

        Returns:
            Словарь с полями паспорта согласно RESULT_TEMPLATE
        """
        # Открываем изображение
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Формируем сообщения для модели
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": OCR_PROMPT},
                ],
            }
        ]

        # Подготовка входа для модели
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )

        # Перемещаем на нужное устройство
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Генерация (жадная стратегия для стабильности)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
        )

        # Обрезаем префикс промпта
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]

        # Декодирование
        output_texts = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )

        raw_text = output_texts[0]

        # Парсинг JSON
        parsed = self.safe_parse_json(raw_text)

        # Гарантируем наличие всех ключей из шаблона
        result = RESULT_TEMPLATE.copy()
        for key in result.keys():
            val = parsed.get(key, "")
            if val is None:
                val = ""
            result[key] = str(val)

        return result


# Создание экземпляра сервиса (singleton)
qwen_ocr_service = QwenOCRService()
