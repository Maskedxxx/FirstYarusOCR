"""
Парсер для извлечения данных из миграционной карты (с sanity-фильтрами)
"""
import re
from typing import Dict, Any, Optional

RU_LABELS = {
    'surname': ['фамилия', 'surname'],
    'name': ['имя', 'name'],
    'patronymic': ['отчество', 'patronymic'],
    'birth_date': ['дата рождения', 'date of birth'],
    'citizenship': ['гражданство', 'citizenship', 'страна'],
    'passport_number': ['паспорт', 'passport'],
    'entry_date': ['дата въезда', 'entry', 'въезд', 'entry date'],
    'departure_date': ['дата выезда', 'departure', 'выезд', 'departure date'],
    'purpose_of_visit': ['цель визита', 'purpose of travel', 'цель', 'purpose'],
    'entry_point': ['пункт въезда', 'entry point'],
}

class MigrationCardParser:
    def parse_migration_card_data(self, text: str) -> Dict[str, Any]:
        cleaned_text = self._clean_text(text)
        # Оставляем все строки (включая пустые) для лучшего контекста
        all_lines = cleaned_text.split('\n')
        # Но используем только non-empty для остальной логики
        lines = [l for l in all_lines if l.strip()]
        skip_top = 0
        for idx, l in enumerate(lines):
            if any(x in l.lower() for x in ["образец", "sample", "migration card", "миграционной карты"]):
                skip_top = idx + 1
        lines = lines[skip_top:]
        surname = self._grab_after_label(lines, RU_LABELS['surname'])
        name = self._grab_after_label(lines, RU_LABELS['name'])
        patronymic = self._grab_after_label(lines, RU_LABELS['patronymic'])
        
        # Если не нашли ФИО по лейблам, пытаемся найти по паттернам
        if not (surname or name):
            surname, name, patronymic = self._extract_fio(all_lines)
        
        result = {
            "surname": surname,
            "name": name,
            "patronymic": patronymic,
            "full_name": f"{surname or ''} {name or ''} {patronymic or ''}".strip() if (surname or name or patronymic) else None,
            "birth_date": self._grab_date_after_label(lines, RU_LABELS['birth_date']),
            "citizenship": self._find_citizenship(lines),
            "passport_number": self._grab_after_label(lines, RU_LABELS['passport_number']),
            "entry_date": self._grab_date_after_label(lines, RU_LABELS['entry_date']),
            "departure_date": self._grab_date_after_label(lines, RU_LABELS['departure_date']),
            "purpose_of_visit": self._grab_simple_after_label(lines, RU_LABELS['purpose_of_visit']),
            "entry_point": self._grab_after_label(lines, RU_LABELS['entry_point']),
            "series_number": self._extract_series_number(cleaned_text),
            "stay_period": self._extract_stay_period(cleaned_text)
        }
        return result

    def _clean_text(self, text: str) -> str:
        text = text.replace('\r', '').replace('\0', '').replace('\t', ' ')
        text = re.sub(r'[ ]+', ' ', text)
        return text.strip()

    def _grab_after_label(self, lines, label_list) -> Optional[str]:
        # Ищет значение строго после одного из лейблов
        for idx, line in enumerate(lines):
            lline = line.lower()
            for label in label_list:
                if label in lline:
                    after = line.split(label, 1)[-1].strip(' :.-_')
                    val = after if after else (lines[idx + 1].strip() if idx + 1 < len(lines) else None)
                    if val and 2 < len(val) < 50:
                        val = re.sub('|'.join(re.escape(l) for l in label_list), '', val, flags=re.IGNORECASE)
                        val = re.sub(r'["\'\[\]\|\(\)]','', val).strip()
                        # Извлекаем только буквы для имен
                        if 'name' in ' '.join(label_list).lower() or 'surname' in ' '.join(label_list).lower():
                            # Для имени/фамилии берем только русские буквы и буквы латиницы
                            val = re.sub(r'[^А-ЯЁа-яёA-Za-z\s]', '', val).strip()
                        # если значение не содержит много слов и выглядит разумно
                        if len(val.split()) <= 3 and not any(x in val.lower() for x in ["карта", "card", "sample"]):
                            return val
                    return None
        return None

    def _grab_simple_after_label(self, lines, label_list) -> Optional[str]:
        # Для purpose — возвращает только короткое первое осмысленное слово
        purpose_map = {
            # Туризм
            'tourism': 'Туризм', 'tourism,': 'Туризм', 'турнизм': 'Туризм',
            # Работа
            'employment': 'Работа', 'employment,': 'Работа', 'employ': 'Работа',
            # Транзит
            'transit': 'Транзит', 'transit,': 'Транзит', 'транзит': 'Транзит',
            # Авиа
            'авиа': 'Авиа', 'avia': 'Авиа', 'aviation': 'Авиа',
            # Служебный
            'служебный': 'Служебный', 'service': 'Служебный', 'official': 'Служебный',
            # Частный
            'частный': 'Частный', 'private': 'Частный',
            # Коммерческий
            'коммерческий': 'Коммерческий', 'business': 'Коммерческий', 'commercial': 'Коммерческий',
            # Образование
            'образование': 'Образование', 'education': 'Образование', 'educational': 'Образование'
        }
        
        # Также ищем паттерны в тексте всей страницы
        full_text = ' '.join(lines).lower()
        for key, value in purpose_map.items():
            if key in full_text:
                return value
        
        # Поиск по лейблам
        for idx, line in enumerate(lines):
            lline = line.lower()
            for label in label_list:
                if label in lline:
                    after = line.split(label, 1)[-1]
                    # Проверяем известные цели визита
                    for key, value in purpose_map.items():
                        if key in lline:
                            return value
                    # берем первое разумное слово
                    for part in after.split():
                        clean_part = re.sub(r'[^\w]', '', part).lower()
                        if 3 < len(clean_part) < 25 and clean_part.isalpha():
                            # Проверяем, не является ли это известной целью
                            for key, value in purpose_map.items():
                                if key in clean_part:
                                    return value
                            return clean_part.capitalize()
        return None

    def _grab_date_after_label(self, lines, label_list) -> Optional[str]:
        for idx, line in enumerate(lines):
            lline = line.lower()
            for label in label_list:
                if label in lline:
                    after = line.split(label, 1)[-1]
                    d = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', after)
                    if d:
                        val = d.group(1)
                        # sanity фильтр
                        try:
                            day, mth, year = val.replace('-', '.').replace('/', '.').split('.')
                            day, mth, year = int(day), int(mth), int(year)
                            if 1<=day<=31 and 1<=mth<=12 and 1900<=(year if year>99 else 2000+year)<=2035:
                                return f"{day:02}.{mth:02}.{year if year>99 else (2000+year):04}"
                        except: pass
        # Если не нашли по лейблу, ищем любую валидную дату в тексте
        for line in lines:
            d = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', line)
            if d:
                val = d.group(1)
                try:
                    day, mth, year = val.replace('-', '.').replace('/', '.').split('.')
                    day, mth, year = int(day), int(mth), int(year)
                    if 1<=day<=31 and 1<=mth<=12 and 1900<=(year if year>99 else 2000+year)<=2035:
                        return f"{day:02}.{mth:02}.{year if year>99 else (2000+year):04}"
                except: pass
        return None

    def _find_citizenship(self, lines) -> Optional[str]:
        # Строго по строке с лейблом или короткое слово/страна
        patterns = ['гражданство', 'citizenship', 'страна', 'belarus', 'россия', 'russia']
        for line in lines:
            for p in patterns:
                if p in line.lower():
                    # возвращаем короткое значение
                    words = [w for w in re.split(r'[, ]+', line) if 2 < len(w) < 30]
                    for w in words:
                        w_lower = w.lower()
                        if 'belar' in w_lower or 'белар' in w_lower:
                            return 'Беларусь'
                        elif 'russ' in w_lower or 'росс' in w_lower:
                            return 'Россия'
        # Поиск без явного лейбла - ищем по ключевым словам
        for line in lines:
            if any(x in line.lower() for x in ['belarussian', 'belarus', 'беларусь']):
                return 'Беларусь'
            if any(x in line.lower() for x in ['russian federation', 'russia', 'российская федерация']):
                return 'Россия'
        return None

    def _extract_series_number(self, text: str) -> Optional[str]:
        # Ищем паттерн миграционной карты: M или MC + цифры
        pattern = r'[MМК]C?\s*(\d{3})\s*(\d{6})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"MC {match.group(1)} {match.group(2)}"
        
        # Альтернативный паттерн: просто 9 цифр подряд
        pattern = r'(\d{3})\s*(\d{6})'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        return None

    def _extract_stay_period(self, text: str) -> Optional[str]:
        period_pat = r'(\d+)\s*(?:дн|дней|days)'
        m = re.search(period_pat, text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} дней"
        return None

    def _extract_fio(self, lines):
        # Список стоп-слов (расширенный)
        ignore = {
            'Беларусь', 'Россия', 'Belarus', 'Russian', 'Federation', 'Карта', 'карта', 
            'Sample', 'Образец', 'номер', 'гражданство', 'passport', 'паспорт', 'Распублика', 
            'Russian Federation', 'Фамилия', 'Имя', 'Отчество', 'Граждане', 'Номер', 'Дата',
            'День', 'Месяц', 'Год', 'Year', 'Month', 'Day', 'Месвы', 'Ратуупате', 'Пали', 
            'Поле', 'Граждане', 'Гражданство', 'ОБРАЗЕЦ', 'ЗАПОЛНЕННОЙ', 'МИГРАЦИОННОЙ', 
            'КАРТЫ', 'Republic', 'Federation', 'Belarus', 'Russian', 'ТЕТЕ'
        }
        
        # Исключаем явно подозрительные слова (слишком длинные или содержат цифры/спецсимволы)
        suspicious_patterns = ['наименова', 'физическ', 'juridica', 'host', 'person', 'company', 'цель', 'визита', 'образец', 'sample', 'миграционной', 'карты']
        
        # Дополнительный список стоп-слов для исключения из ФИО
        fio_stop_words = ['Вывздер', 'Республика', 'Российская', 'Федерация', 'РоссийскаяФедерация', 
                          'Беларусь', 'Russian', 'Federation', 'Republic', 'Belarus']
        
        # Шаблон кириллического слова с большой буквы (минимум 5 букв - более строгий)
        # Разрешаем как строчные, так и заглавные буквы после первой
        word_re = re.compile(r'^[А-ЯЁ][А-ЯЁа-яё]{4,}$')
        
        # Собираем массив всех слов всех строк подряд
        words = []
        for line in lines:
            ws = [w.strip('"\'\[\]|,.:;-()') for w in line.split()]
            words.extend(ws)

        # Фильтруем слова более строго
        candidates = [w for w in words if word_re.match(w) and w not in ignore]
        # Исключаем подозрительные слова
        candidates = [w for w in candidates if not any(pat in w.lower() for pat in suspicious_patterns)]
        
        # --- ПРИОРИТЕТ 1: Ищем строки с метками "Family name" или "фамилия" ---
        for idx, line in enumerate(lines):
            # Расширяем поиск меток: ищем любые варианты написания
            if any(x in line.lower() for x in ['family name', 'surname', 'famly name', 'ramiy ame', 'ananwar', 'famiy name']):
                # Берем слова из следующей непустой строки (idx+1 может быть пустой, пропускаем пустые)
                for check_idx in range(idx + 1, min(idx + 8, len(lines))):
                    check_line = lines[check_idx].strip()
                    if not check_line:
                        continue  # Пропускаем пустые строки
                    ws = [w.strip('"\'\[\]|,.:;-()') for w in check_line.split()]
                    clean_ws = [w for w in ws if word_re.match(w) and w not in ignore]
                    clean_ws = [w for w in clean_ws if not any(pat in w.lower() for pat in suspicious_patterns)]
                    # Исключаем стоп-слова для ФИО
                    clean_ws = [w for w in clean_ws if w not in fio_stop_words]
                    # Если это ФИО, должно быть одно слово (фамилия) или несколько коротких слов
                    # Ужесточаем требования: длина 5-10 букв, не слишком длинные слова
                    if len(clean_ws) >= 1 and all(5 <= len(w) <= 10 for w in clean_ws):
                        # Не возвращаем слова, содержащие повторяющиеся буквы (артефакты OCR)
                        final_ws = [w for w in clean_ws if len(set(w.lower())) > 4]
                        if final_ws:
                            if len(final_ws) >= 3:
                                return final_ws[0], final_ws[1], final_ws[2]
                            elif len(final_ws) == 2:
                                return final_ws[0], final_ws[1], None
                            else:
                                # Только фамилия
                                return final_ws[0], None, None
        
        # --- ПРИОРИТЕТ 2: Поиск кириллических имен (только длинные слова) ---
        for i in range(len(candidates) - 1):
            block = candidates[i:i+3]
            # Проверяем, что слова выглядят как имена (не содержат повторяющихся подозрительных паттернов)
            # Требуем минимум 5 букв для каждого слова
            if len(block) >= 2 and all(len(w) >= 5 and w[0].isupper() for w in block[:2]):
                if len(block) >= 3:
                    return block[0], block[1], block[2]
                else:
                    return block[0], block[1], None

        # --- ПРИОРИТЕТ 3: Поиск «кластера» в каждой строке отдельно ---
        for line in lines:
            ws = [w.strip('"\'\[\]|,.:;-()') for w in line.split()]
            clean_ws = [w for w in ws if word_re.match(w) and w not in ignore]
            clean_ws = [w for w in clean_ws if not any(pat in w.lower() for pat in suspicious_patterns)]
            if len(clean_ws) >= 2 and all(len(w) >= 5 for w in clean_ws[:2]):
                # Берём первые два (или три) слова подряд
                if len(clean_ws) >= 3:
                    return clean_ws[0], clean_ws[1], clean_ws[2]
                else:
                    return clean_ws[0], clean_ws[1], None
        
        # Не найдено ничего подходящего
        return None, None, None

