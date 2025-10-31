"""
Парсер для извлечения данных ИНН
"""
import re
from typing import Dict, Any, Optional


class INNParser:
    """Парсер для извлечения ИНН из текста"""
    
    def parse_inn_data(self, text: str) -> Dict[str, Any]:
        """
        Парсинг данных ИНН из текста
        
        Args:
            text: Текст, извлеченный из изображения
            
        Returns:
            Dict с данными ИНН
        """
        # Очистка текста от лишних символов
        cleaned_text = self._clean_text(text)
        
        # Извлечение данных
        inn_data = {
            "inn_number": self._extract_inn_number(cleaned_text),
            "full_name": self._extract_full_name(cleaned_text),
            "birth_date": self._extract_birth_date(cleaned_text),
            "issue_date": self._extract_issue_date(cleaned_text)
        }
        
        return inn_data
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        # Замена множественных пробелов на одинарные
        text = re.sub(r'\s+', ' ', text)
        # Удаление лишних переносов строк
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _extract_inn_number(self, text: str) -> Optional[str]:
        """Извлечение номера ИНН"""
        # ИНН физического лица: 12 цифр
        # ИНН юридического лица: 10 цифр
        
        # Поиск паттерна с квадратными скобками [6319103818013] (может быть 10, 12 или 13 цифр)
        pattern = r'\[(\d{10,13})\](?!\s*\])'
        match = re.search(pattern, text)
        if match:
            number = match.group(1)
            # Возвращаем первые 12 цифр для 13-значного, или первые 10 для 11-значного
            if len(number) == 13:
                return number[:12]  # Возвращаем как 12-значный
            elif len(number) == 11:
                return number[:10]  # Возвращаем как 10-значный
            return number
        
        # Поиск паттерна "ИНН" с последующими цифрами
        pattern = r'ИНН\s*:?\s*(\d{10}|\d{12})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Поиск 12-значного числа (ИНН физического лица)
        pattern = r'\b(\d{12})\b'
        match = re.search(pattern, text)
        if match:
            # Проверяем, что это не дата
            if not re.search(r'\d{4}', match.group(1)[:4]):
                return match.group(1)
        
        # Поиск 10-значного числа (ИНН юридического лица)
        pattern = r'\b(\d{10})\b'
        match = re.search(pattern, text)
        if match:
            # Проверяем, что это не дата
            if not re.search(r'\d{2}\.\d{2}\.\d{4}', text[:match.start()]):
                return match.group(1)
        
        return None
    
    def _extract_full_name(self, text: str) -> Optional[str]:
        """Извлечение полного имени"""
        # Список стоп-слов для исключения
        stop_words = {
            'ИНН', 'ФНС', 'ФЕДЕРАЦИЯ', 'СЛУЖБА', 'НАЛОГОВ', 'РОССИИ', 'УПРАВЛЕНИЕ',
            'ПОСТАНОВКЕ', 'НА', 'УЧЕТ', 'УПРАВЛЕНИЯ', 'ФЕДЕРАЛЬНОЙ', 'НАЛОГОВОЙ',
            'ПОСТАНОВКИ', 'ПОСТАНОВКЕ', 'НОМЕР', 'ДАТА'
        }
        
        # Поиск по метке "ФИО" или "Фамилия"
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if re.search(r'ФИО|Фамилия', line, re.IGNORECASE):
                # Берем следующую непустую строку
                for check_idx in range(idx + 1, min(idx + 5, len(lines))):
                    check_line = lines[check_idx].strip()
                    if not check_line:
                        continue
                    # Извлекаем слова в верхнем регистре
                    words = re.findall(r'[А-ЯЁ]{2,}', check_line)
                    if len(words) >= 2:
                        valid_words = [w for w in words if w not in stop_words and 3 <= len(w) <= 20]
                        if len(valid_words) >= 2:
                            return ' '.join(valid_words[:3])  # Максимум 3 слова
        
        # Поиск имени в верхнем регистре (улучшенный)
        pattern = r'\b([А-ЯЁ]{2,})\s+([А-ЯЁ]{2,}(?:\s+[А-ЯЁ]{2,})?)\b'
        matches = re.findall(pattern, text)
        
        if matches:
            # Ищем наиболее подходящее имя (исключаем служебные строки)
            for match in matches:
                full_match = ' '.join(match)
                # Проверяем, что нет стоп-слов
                if not any(word in full_match for word in stop_words):
                    # Проверяем, что слова разумной длины
                    if all(3 <= len(w) <= 20 for w in match):
                        return full_match.strip()
        
        return None
    
    def _extract_birth_date(self, text: str) -> Optional[str]:
        """Извлечение даты рождения"""
        # Поиск даты рождения в формате DD.MM.YYYY
        pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
        matches = re.findall(pattern, text)
        if matches:
            # Проверяем, что дата разумная (год между 1900 и 2010)
            for date in matches:
                year = int(date.split('.')[2])
                if 1900 <= year <= 2010:
                    return date
        return None
    
    def _extract_issue_date(self, text: str) -> Optional[str]:
        """Извлечение даты выдачи"""
        # Поиск даты выдачи
        patterns = [
            r'(ВЫДАН[^\n]*\d{1,2}\.\d{1,2}\.\d{4})',
            r'(ВЫПОЛНЕН[^\n]*\d{1,2}\.\d{1,2}\.\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Извлекаем дату
                date_match = re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', match.group(0))
                if date_match:
                    return date_match.group(0)
        
        return None

