"""
Парсер для извлечения данных СНИЛС
"""
import re
from typing import Dict, Any, Optional


class SNILSParser:
    """Парсер для извлечения СНИЛС из текста"""
    
    def parse_snils_data(self, text: str) -> Dict[str, Any]:
        """
        Парсинг данных СНИЛС из текста
        
        Args:
            text: Текст, извлеченный из изображения
            
        Returns:
            Dict с данными СНИЛС
        """
        # Очистка текста от лишних символов
        cleaned_text = self._clean_text(text)
        
        # Извлечение данных
        snils_data = {
            "snils_number": self._extract_snils_number(cleaned_text),
            "full_name": self._extract_full_name(cleaned_text),
            "birth_date": self._extract_birth_date(cleaned_text),
            "gender": self._extract_gender(cleaned_text)
        }
        
        return snils_data
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        # Замена множественных пробелов на одинарные
        text = re.sub(r'\s+', ' ', text)
        # Удаление лишних переносов строк
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _extract_snils_number(self, text: str) -> Optional[str]:
        """Извлечение номера СНИЛС"""
        # СНИЛС имеет формат: XXX-XXX-XXX XX
        
        # Поиск паттерна в формате XXX-XXX-XXX XX (с пробелом или без)
        pattern = r'(\d{3}\s*-\s*\d{3}\s*-\s*\d{3}[\s-]?\d{2})'
        match = re.search(pattern, text)
        if match:
            # Форматируем в стандартный формат
            number = re.sub(r'[^\d]', '', match.group(1))
            if len(number) == 11:
                return f"{number[:3]}-{number[3:6]}-{number[6:9]} {number[9:11]}"
        
        # Поиск 11-значного числа без дефисов
        pattern = r'\b(\d{11})\b'
        match = re.search(pattern, text)
        if match:
            # Форматируем в стандартный формат XXX-XXX-XXX XX
            number = match.group(1)
            if len(number) == 11:
                return f"{number[:3]}-{number[3:6]}-{number[6:9]} {number[9:11]}"
        
        return None
    
    def _extract_full_name(self, text: str) -> Optional[str]:
        """Извлечение полного имени"""
        # Поиск имени в верхнем регистре, ищем паттерн ФИО
        # Формат может быть: ФИО — ИВАНОВ ИВАН ИВАНОВИЧ
        pattern = r'ФИО[^\n]*?([А-ЯЁ]{2,}[^\n]*)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Извлекаем только русские слова в заглавных буквах
            name_part = match.group(1)
            name_words = re.findall(r'[А-ЯЁ]{2,}', name_part)
            if name_words:
                return ' '.join(name_words[:3])  # Максимум 3 слова
        
        # Если не найден паттерн ФИО, ищем 2-3 слова подряд
        pattern = r'([А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}(?:\s+[А-ЯЁ]{2,})?)'
        matches = re.findall(pattern, text)
        
        if matches:
            # Ищем наиболее подходящее имя (исключаем служебные строки)
            for match in matches:
                if not any(word in match for word in ['СНИЛС', 'ПЕНСИОННЫЙ', 'ФОНД', 'СТРАХОВОЙ', 'СВИДЕТЕЛЬСТВО', 'ФЕДЕРАЦИЯ']):
                    return match.strip()
        
        return None
    
    def _extract_birth_date(self, text: str) -> Optional[str]:
        """Извлечение даты рождения"""
        # Поиск даты рождения в форматах DD.MM.YYYY или "1января 1990"
        # Формат DD.MM.YYYY
        pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
        matches = re.findall(pattern, text)
        if matches:
            # Проверяем, что дата разумная (год между 1900 и 2010)
            for date in matches:
                year = int(date.split('.')[2])
                if 1900 <= year <= 2010:
                    return date
        
        # Формат "1января 1990" или подобный
        months = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
            'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
            'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
        }
        for month_name, month_num in months.items():
            pattern = r'(\d{1,2})' + re.escape(month_name) + r'\s*(\d{4})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                day = match.group(1).zfill(2)
                year = match.group(2)
                if 1900 <= int(year) <= 2010:
                    return f"{day}.{month_num}.{year}"
        
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Извлечение пола"""
        if 'МУЖ' in text or 'муж' in text.lower():
            return 'МУЖ'
        elif 'ЖЕН' in text or 'жен' in text.lower():
            return 'ЖЕН'
        return None

