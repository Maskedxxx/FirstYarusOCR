from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PassportData(BaseModel):
    """Данные паспорта РФ"""
    series_number: Optional[str] = Field(None, description="Серия и номер паспорта (ХХХХ ХХХХХХ)")
    issue_date: Optional[str] = Field(None, description="Дата выдачи паспорта (ДД.ММ.ГГГГ)")
    issue_authority: Optional[str] = Field(None, description="Орган, выдавший паспорт")
    birth_date: Optional[str] = Field(None, description="Дата рождения (ДД.ММ.ГГГГ)")
    birth_place: Optional[str] = Field(None, description="Место рождения")
    full_name: Optional[str] = Field(None, description="ФИО (Фамилия Имя Отчество)")
    gender: Optional[str] = Field(None, description="Пол (МУЖ/ЖЕН)")
    mrz_line1: Optional[str] = Field(None, description="Первая строка машиночитаемой зоны")
    mrz_line2: Optional[str] = Field(None, description="Вторая строка машиночитаемой зоны")
    mrz_line3: Optional[str] = Field(None, description="Третья строка машиночитаемой зоны")


class MigrationCardData(BaseModel):
    """Данные миграционной карты"""
    surname: Optional[str] = Field(None, description="Фамилия")
    name: Optional[str] = Field(None, description="Имя")
    patronymic: Optional[str] = Field(None, description="Отчество")
    full_name: Optional[str] = Field(None, description="Полное ФИО")
    birth_date: Optional[str] = Field(None, description="Дата рождения (ДД.ММ.ГГГГ)")
    citizenship: Optional[str] = Field(None, description="Гражданство")
    passport_number: Optional[str] = Field(None, description="Номер паспорта")
    entry_date: Optional[str] = Field(None, description="Дата въезда (ДД.ММ.ГГГГ)")
    departure_date: Optional[str] = Field(None, description="Дата выезда (ДД.ММ.ГГГГ)")
    purpose_of_visit: Optional[str] = Field(None, description="Цель визита (Туризм, Работа, Транзит и др.)")
    entry_point: Optional[str] = Field(None, description="Пункт въезда")
    series_number: Optional[str] = Field(None, description="Серия и номер карты (MC ХХХ ХХХХХХ)")
    stay_period: Optional[str] = Field(None, description="Срок пребывания")


class INNData(BaseModel):
    """Данные ИНН"""
    inn_number: Optional[str] = Field(None, description="Номер ИНН (10 или 12 цифр)")
    full_name: Optional[str] = Field(None, description="ФИО (Фамилия Имя Отчество)")
    birth_date: Optional[str] = Field(None, description="Дата рождения (ДД.ММ.ГГГГ)")
    issue_date: Optional[str] = Field(None, description="Дата выдачи (ДД.ММ.ГГГГ)")


class SNILSData(BaseModel):
    """Данные СНИЛС"""
    snils_number: Optional[str] = Field(None, description="Номер СНИЛС (XXX-XXX-XXX XX)")
    full_name: Optional[str] = Field(None, description="ФИО (Фамилия Имя Отчество)")
    birth_date: Optional[str] = Field(None, description="Дата рождения (ДД.ММ.ГГГГ)")
    birth_place: Optional[str] = Field(None, description="Место рождения")
    gender: Optional[str] = Field(None, description="Пол (МУЖ/ЖЕН)")
    registration_date: Optional[str] = Field(None, description="Дата регистрации (ДД.ММ.ГГГГ)")


class OCRResponse(BaseModel):
    """Ответ OCR API"""
    success: bool = Field(..., description="Статус выполнения операции")
    extracted_text: str = Field(..., description="Полный текст, распознанный OCR")
    character_count: int = Field(..., description="Количество символов в тексте")
    word_count: int = Field(..., description="Количество слов в тексте")
    document_type: str = Field(..., description="Тип обработанного документа")
    parsed_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="""
        Структурированные данные документа. Поля зависят от типа документа:
        
        **passport**: series_number, issue_date, issue_authority, birth_date, birth_place, full_name, gender, mrz_line1-3
        
        **migration_card**: surname, name, patronymic, full_name, birth_date, citizenship, passport_number, 
        entry_date, departure_date, purpose_of_visit, entry_point, series_number, stay_period
        
        **inn**: inn_number, full_name, birth_date, issue_date
        
        **snils**: snils_number, full_name, birth_date, birth_place, gender, registration_date
        """
    )
    error: Optional[str] = Field(None, description="Сообщение об ошибке (если есть)")
