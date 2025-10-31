"""
Парсер для извлечения данных из паспорта
"""
import re
from typing import Dict, Any, Optional


class PassportParser:
    """Парсер для извлечения данных из текста паспорта"""
    
    def parse_passport_data(self, text: str) -> Dict[str, Any]:
        """
        Парсинг данных паспорта из текста
        
        Args:
            text: Текст, извлеченный из изображения паспорта
            
        Returns:
            Dict с структурированными данными паспорта
        """
        # Очистка текста от лишних символов
        cleaned_text = self._clean_text(text)
        
        # Извлечение данных
        passport_data = {
            "series_number": self._extract_series_number(cleaned_text),
            "issue_date": self._extract_issue_date(cleaned_text),
            "issue_authority": self._extract_issue_authority(cleaned_text),
            "birth_date": self._extract_birth_date(cleaned_text),
            "birth_place": self._extract_birth_place(cleaned_text),
            "full_name": self._extract_full_name(cleaned_text),
            "gender": self._extract_gender(cleaned_text),
            "mrz_line1": self._extract_mrz_line1(cleaned_text),
            "mrz_line2": self._extract_mrz_line2(cleaned_text),
            "mrz_line3": self._extract_mrz_line3(cleaned_text)
        }
        
        return passport_data
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних символов"""
        # Замена множественных пробелов на одинарные
        text = re.sub(r'\s+', ' ', text)
        # Удаление лишних переносов строк
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _extract_series_number(self, text: str) -> Optional[str]:
        """Извлечение серии и номера паспорта"""
        # Поиск паттерна серии и номера (4 цифры + 6 цифр)
        pattern = r'(\d{4})\s*(\d{6})'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Поиск альтернативного формата (6 цифр подряд)
        pattern = r'(\d{6})'
        matches = re.findall(pattern, text)
        if matches:
            # Берем первое найденное 6-значное число
            return matches[0]
        
        return None
    
    def _extract_issue_date(self, text: str) -> Optional[str]:
        """Извлечение даты выдачи паспорта"""
        # Поиск даты в формате DD.MM.YYYY
        pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]  # Первая найденная дата
        return None
    
    def _extract_issue_authority(self, text: str) -> Optional[str]:
        """Извлечение органа, выдавшего паспорт"""
        # Поиск ГУ МВД или других органов
        pattern = r'(ГУ МВД[^\n]*)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        
        # Поиск альтернативного формата "УПРАВЛЕНИЕМ ВНУТРЕННИХ ДЕЛ"
        pattern = r'(УПРАВЛЕНИЕМ ВНУТРЕННИХ ДЕЛ[^\n]*)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _extract_birth_date(self, text: str) -> Optional[str]:
        """Извлечение даты рождения"""
        # Поиск даты рождения в формате DD.MM.YYYY
        pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
        matches = re.findall(pattern, text)
        if len(matches) > 1:
            return matches[1]  # Вторая найденная дата (обычно дата рождения)
        elif len(matches) == 1:
            # Если только одна дата, проверяем контекст
            # Ищем дату после имени
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if re.search(r'[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}', line):
                    # Ищем дату в следующих строках
                    for j in range(i + 1, min(i + 3, len(lines))):
                        if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', lines[j]):
                            return re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', lines[j]).group(0)
            
            # Если не нашли по контексту, ищем дату после имени на отдельных строках
            for i, line in enumerate(lines):
                line = line.strip()
                if re.match(r'^[А-ЯЁ]{2,}$', line) and len(line) > 3:
                    # Проверяем следующие строки на наличие даты
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', lines[j]):
                            return re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', lines[j]).group(0)
            
            # Ищем дату после имени с символом №
            # КОНСТАНТИН АЛЕКСАНДРОВИЧ №. 22.11.1969
            pattern = r'[А-ЯЁ]{2,}\s+[А-ЯЁ]{2,}\s*№\.\s*(\d{1,2}\.\d{1,2}\.\d{4})'
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_birth_place(self, text: str) -> Optional[str]:
        """Извлечение места рождения"""
        lines = text.split('\n')
        
        # Паттерны для поиска места рождения
        place_patterns = [
            r'ГОР\.?\s*([А-ЯЁ]+)',
            r'ГОРОД\s+([А-ЯЁ]+)',
            r'eter\s+([А-ЯЁ\s]+)',
        ]
        
        # Сначала ищем по явным паттернам
        for pattern in place_patterns:
            match = re.search(pattern, text)
            if match:
                place = match.group(1).strip()
                if len(place) > 2:
                    return place if not pattern.startswith(r'ГОР\.') else f"ГОР.{place}"
        
        # Поиск места рождения после даты рождения
        for i, line in enumerate(lines):
            if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', line):
                # Ищем следующие строки с местом рождения
                for j in range(i + 1, min(i + 4, len(lines))):
                    place = lines[j].strip()
                    # Должно быть минимум 3 символа, без цифр года
                    if place and not re.search(r'\d{4}', place) and len(place) > 3:
                        # Исключаем служебные строки
                        excluded_words = ['ГУ', 'МВД', 'РОССИИ', 'ОБЛАСТИ', 'РАЙОНУ', 'ВОПРОСАМ', 
                                        'УПРАВЛЕНИЕМ', 'ВНУТРЕННИХ', 'ОТДЕЛОМ', 'ОКРУГА']
                        if not any(word in place.upper() for word in excluded_words):
                            # Извлекаем только значимые слова
                            clean_place = ' '.join([w for w in place.split() if len(w) > 2])
                            if clean_place:
                                return clean_place
        
        return None
    
    def _extract_full_name(self, text: str) -> Optional[str]:
        """Извлечение полного имени"""
        # Список стоп-слов
        stop_words = {
            'ГУ', 'МВД', 'РОССИИ', 'ОБЛАСТИ', 'ГОРОД', 'ИРКУТСКОЙ', 'РАЙОНУ', 
            'ВОПРОСАМ', 'ПРИБРЕЖНАЯ', 'ROMY', 'УПРАВЛЕНИЕМ', 'ВНУТРЕННИХ', 'ДЕЛ',
            'ФЕДЕРАЦИЯ', 'МЕСУТСКОЙ', 'РАВ', 'САОМАМОУ', 'МУЖ', 'ЖЕН', 'ПАСПОРТ',
            'ОТДЕЛОМ', 'ОКТЯБРЬСКОГО', 'ОКРУГА', 'ГОРОДА', 'АРХАНГЕЛЬСКА', 'АРХАНГЕЛЬСК'
        }
        
        lines = text.split('\n')
        
        # ПРИОРИТЕТ 1: Поиск последовательности кириллических слов (фамилия -> имя -> отчество)
        # Ищем паттерн, где фамилия может быть ВЫШЕ имени и отчества
        potential_names = []
        for i, line in enumerate(lines):
            line = line.strip()
            # Извлекаем все кириллические слова из строки длиной 4-20 символов
            words_in_line = re.findall(r'[А-ЯЁ]{4,20}', line)
            
            for word in words_in_line:
                if word not in stop_words:
                    # Это потенциальная фамилия
                    surname = word
                    name = None
                    patronymic = None
                    
                    # Ищем имя и отчество в следующих строках
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_words = re.findall(r'[А-ЯЁ]{4,20}', lines[j].strip())
                        for nw in next_words:
                            if nw not in stop_words and nw != surname:
                                if name is None:
                                    name = nw
                                elif patronymic is None:
                                    patronymic = nw
                                    break
                        if patronymic:
                            break
                    
                    # Если нашли хотя бы фамилию и имя
                    if surname and name:
                        potential_names.append((surname, name, patronymic, i))
        
        # Возвращаем первое найденное ФИО с минимальным индексом строки
        if potential_names:
            potential_names.sort(key=lambda x: x[3])
            surname, name, patronymic, _ = potential_names[0]
            if patronymic:
                return f"{surname} {name} {patronymic}"
            else:
                return f"{surname} {name}"
        
        # Поиск имени в верхнем регистре (ФАМИЛИЯ ИМЯ ОТЧЕСТВО) в одной строке
        for line in lines:
            line = line.strip()
            # Проверяем, что строка содержит только заглавные буквы и пробелы
            if re.match(r'^[А-ЯЁ\s=]+$', line) and len(line) > 5:
                # Исключаем служебные строки
                words = line.split()
                clean_words = [word.replace('=', '').replace('№', '').replace('.', '') 
                              for word in words if len(word) > 1 and word not in stop_words]
                if len(clean_words) >= 2 and all(3 <= len(w) <= 20 for w in clean_words):
                    return ' '.join(clean_words)
        
        # Поиск паттерна ПЕТР = АЙРАТОВИЧ
        pattern = r'([А-ЯЁ]{2,})\s*=\s*([А-ЯЁ]{2,})'
        match = re.search(pattern, text)
        if match and match.group(1) not in stop_words and match.group(2) not in stop_words:
            return f"{match.group(1)} {match.group(2)}"
        
        # Ищем паттерн с символом № перед датой
        # КОНСТАНТИН АЛЕКСАНДРОВИЧ №. 22.11.1969
        pattern = r'([А-ЯЁ]{2,})\s+([А-ЯЁ]{2,})\s*№\.\s*\d{1,2}\.\d{1,2}\.\d{4}'
        match = re.search(pattern, text)
        if match and match.group(1) not in stop_words and match.group(2) not in stop_words:
            return f"{match.group(1)} {match.group(2)}"
        
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Извлечение пола"""
        if 'МУЖ' in text:
            return 'МУЖ'
        elif 'ЖЕН' in text:
            return 'ЖЕН'
        return None
    
    def _extract_mrz_line1(self, text: str) -> Optional[str]:
        """Извлечение первой строки MRZ"""
        # Поиск строки, начинающейся с P<RUS
        pattern = r'P<RUS[^\n]*'
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
        return None
    
    def _extract_mrz_line2(self, text: str) -> Optional[str]:
        """Извлечение второй строки MRZ"""
        # Поиск строки с серией и номером паспорта
        pattern = r'\d{4}\d{6}[^\n]*'
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
        return None
    
    def _extract_mrz_line3(self, text: str) -> Optional[str]:
        """Извлечение третьей строки MRZ"""
        # Поиск строки с датами и контрольными цифрами
        pattern = r'\d{6}[^\n]*'
        matches = re.findall(pattern, text)
        if len(matches) > 1:
            return matches[1].strip()
        return None

