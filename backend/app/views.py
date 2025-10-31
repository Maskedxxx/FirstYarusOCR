import pytesseract
from PIL import Image
import io
from typing import Dict, Any, Optional

from backend.app.parsers import PassportParser, MigrationCardParser, INNParser, SNILSParser
from backend.app.preprocess_images import (
    compose_basic_preprocessing, 
    compose_aggressive_preprocessing, 
    compose_advanced_preprocessing
)


class OCRService:
    """Простой сервис для обработки изображений с помощью pytesseract"""
    
    def __init__(self):
        self.language = "rus+eng"
        self.passport_parser = PassportParser()
        self.migration_card_parser = MigrationCardParser()
        self.inn_parser = INNParser()
        self.snils_parser = SNILSParser()
    
    def process_image(self, image_data: bytes, document_type: str) -> Dict[str, Any]:
        """
        Обработка изображения с помощью pytesseract с автоматическим выбором лучшего режима
        
        Args:
            image_data: Байты изображения
            document_type: Тип документа (passport, migration_card, inn, snils)
            
        Returns:
            Dict с результатами OCR с лучшими параметрами
        """
        # Расширенный набор PSM режимов для тестирования
        preprocessing_modes = ['none', 'basic', 'aggressive', 'advanced']
        psm_modes = [6, 11, 12, 3, 4, 13]  # Добавлены дополнительные PSM режимы
        
        best_result = None
        best_score = -1
        best_config = None
        
        # Перебор всех комбинаций
        for preproc in preprocessing_modes:
            for psm in psm_modes:
                try:
                    result = self._process_single_config(image_data, document_type, preproc, psm)
                    
                    # Оценка качества результата по количеству найденных полей
                    parsed_fields = [v for v in result.get('parsed_data', {}).values() if v]
                    score = len(parsed_fields)
                    score += result.get('word_count', 0) * 0.01  # Небольшой бонус за количество слов
                    
                    # Дополнительная оценка качества
                    if document_type == 'passport':
                        # Для паспорта приоритет важным полям
                        if result.get('parsed_data', {}).get('full_name'):
                            score += 3
                        if result.get('parsed_data', {}).get('series_number'):
                            score += 2
                    elif document_type == 'inn':
                        if result.get('parsed_data', {}).get('inn_number'):
                            score += 5
                    elif document_type == 'snils':
                        if result.get('parsed_data', {}).get('snils_number'):
                            score += 5
                    elif document_type == 'migration_card':
                        if result.get('parsed_data', {}).get('surname'):
                            score += 3
                        if result.get('parsed_data', {}).get('purpose_of_visit'):
                            score += 2
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_config = {'preprocessing': preproc, 'psm': psm, 'score': score}
                except Exception as e:
                    # Логируем ошибку для отладки
                    import logging
                    logging.error(f"Error processing with {preproc}/{psm}: {str(e)}")
                    continue
        
        # Добавляем информацию о лучшей конфигурации к результату
        if best_result:
            best_result['_best_config'] = best_config
        
        return best_result if best_result else {
            "success": False,
            "extracted_text": "",
            "character_count": 0,
            "word_count": 0,
            "document_type": document_type,
            "parsed_data": {},
            "error": "Не удалось обработать изображение ни одним из методов"
        }
    
    def _process_single_config(self, image_data: bytes, document_type: str, preprocessing_mode: str, psm_mode: int) -> Dict[str, Any]:
        """Внутренний метод для обработки одной конфигурации"""
        # Открытие изображения
        image = Image.open(io.BytesIO(image_data))
        
        # Конвертация в RGB если необходимо
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Применение предобработки в зависимости от режима
        if preprocessing_mode == 'basic':
            image = compose_basic_preprocessing(image)
        elif preprocessing_mode == 'aggressive':
            image = compose_aggressive_preprocessing(image)
        elif preprocessing_mode == 'advanced':
            image = compose_advanced_preprocessing(image)
        # 'none' - без предобработки
        
        # Извлечение текста с учетом PSM режима
        config = f'--psm {psm_mode}'
        extracted_text = pytesseract.image_to_string(image, lang=self.language, config=config)
        
        # Парсинг данных в зависимости от типа документа
        parsed_data = {}
        if document_type == 'passport':
            parsed_data = self.passport_parser.parse_passport_data(extracted_text)
        elif document_type == 'migration_card':
            parsed_data = self.migration_card_parser.parse_migration_card_data(extracted_text)
        elif document_type == 'inn':
            parsed_data = self.inn_parser.parse_inn_data(extracted_text)
        elif document_type == 'snils':
            parsed_data = self.snils_parser.parse_snils_data(extracted_text)
        
        # Подсчет статистики
        character_count = len(extracted_text.strip())
        word_count = len(extracted_text.strip().split()) if extracted_text.strip() else 0
        
        return {
            "success": True,
            "extracted_text": extracted_text.strip(),
            "character_count": character_count,
            "word_count": word_count,
            "document_type": document_type,
            "parsed_data": parsed_data,
            "error": None
        }

# Создание экземпляра сервиса
ocr_service = OCRService()
