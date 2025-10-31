from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from enum import Enum

from backend.app.schemas import OCRResponse
from backend.app.views import ocr_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


class DocumentType(str, Enum):
    """Поддерживаемые типы документов"""
    PASSPORT = "passport"
    MIGRATION_CARD = "migration_card"
    INN = "inn"
    SNILS = "snils"


@router.post(
    "/upload-image",
    response_model=OCRResponse,
    summary="Загрузка и обработка изображения документа",
    description="""
    Эндпоинт для загрузки и обработки изображений документов с помощью OCR.
    
    ## Поддерживаемые типы документов
    
    ### 1. passport - Паспорт гражданина РФ
    **Извлекаемые поля:**
    - `series_number` - Серия и номер паспорта
    - `issue_date` - Дата выдачи (ДД.ММ.ГГГГ)
    - `issue_authority` - Орган, выдавший паспорт
    - `birth_date` - Дата рождения (ДД.ММ.ГГГГ)
    - `birth_place` - Место рождения
    - `full_name` - ФИО (Фамилия Имя Отчество)
    - `gender` - Пол (МУЖ/ЖЕН)
    - `mrz_line1`, `mrz_line2`, `mrz_line3` - Машиночитаемая зона
    
    ### 2. migration_card - Миграционная карта
    **Извлекаемые поля:**
    - `surname`, `name`, `patronymic` - ФИО по отдельности
    - `full_name` - Полное ФИО
    - `birth_date` - Дата рождения (ДД.ММ.ГГГГ)
    - `citizenship` - Гражданство
    - `passport_number` - Номер паспорта
    - `entry_date` - Дата въезда (ДД.ММ.ГГГГ)
    - `departure_date` - Дата выезда (ДД.ММ.ГГГГ)
    - `purpose_of_visit` - Цель визита (Туризм, Работа, Транзит и др.)
    - `entry_point` - Пункт въезда
    - `series_number` - Серия и номер карты
    - `stay_period` - Срок пребывания
    
    ### 3. inn - Свидетельство ИНН
    **Извлекаемые поля:**
    - `inn_number` - Номер ИНН (10 или 12 цифр)
    - `full_name` - ФИО (Фамилия Имя Отчество)
    - `birth_date` - Дата рождения (ДД.ММ.ГГГГ)
    - `issue_date` - Дата выдачи (ДД.ММ.ГГГГ)
    
    ### 4. snils - СНИЛС
    **Извлекаемые поля:**
    - `snils_number` - Номер СНИЛС (XXX-XXX-XXX XX)
    - `full_name` - ФИО (Фамилия Имя Отчество)
    - `birth_date` - Дата рождения (ДД.ММ.ГГГГ)
    - `birth_place` - Место рождения
    - `gender` - Пол (МУЖ/ЖЕН)
    - `registration_date` - Дата регистрации (ДД.ММ.ГГГГ)
    
    ## Дополнительно
    - **Форматы изображений:** JPEG, PNG, BMP, TIFF, WEBP
    - **Автоматический подбор параметров:** Система автоматически тестирует различные режимы предобработки и выбирает лучший результат
    - **Валидация данных:** Даты проверяются на корректность, ФИО фильтруются от служебных слов
    """
)
async def upload_and_process_image(
    file: UploadFile = File(..., description="Изображение документа для обработки"),
    document_type: DocumentType = Query(
        ...,
        description="Тип документа для обработки (обязательный параметр)"
    )
):
    """
    Загрузка и обработка изображения документа с автоматическим подбором лучших параметров
    
    Args:
        file: Загружаемый файл изображения
        document_type: Тип документа (passport, migration_card, inn, snils)
        
    Returns:
        OCRResponse с результатами OCR и распарсенными данными
    """
    try:
        # Проверка типа файла
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Файл должен быть изображением"
            )
        
        # Чтение содержимого файла
        file_content = await file.read()
        
        # Обработка изображения с автоматическим выбором лучших параметров
        ocr_result = ocr_service.process_image(
            file_content, 
            document_type=document_type.value
        )
        
        return OCRResponse(**ocr_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}"
        )

