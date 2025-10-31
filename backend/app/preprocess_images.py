"""
Модуль для предобработки изображений перед OCR
"""
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from io import BytesIO

# Попытка импорта cv2, если не доступен - используем только PIL
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Увеличение контрастности изображения
    
    Args:
        image: PIL Image
        factor: Коэффициент усиления контраста (1.0 - без изменений, >1.0 - усиление)
    
    Returns:
        Обработанное изображение
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def enhance_sharpness(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Повышение резкости изображения
    
    Args:
        image: PIL Image
        factor: Коэффициент резкости
    
    Returns:
        Обработанное изображение
    """
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def enhance_brightness(image: Image.Image, factor: float = 1.2) -> Image.Image:
    """
    Корректировка яркости
    
    Args:
        image: PIL Image
        factor: Коэффициент яркости
    
    Returns:
        Обработанное изображение
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def apply_grayscale(image: Image.Image) -> Image.Image:
    """
    Конвертация в оттенки серого
    
    Args:
        image: PIL Image
    
    Returns:
        Grayscale изображение
    """
    if image.mode != 'L':
        return image.convert('L')
    return image


def binarize_adaptive(image: Image.Image) -> Image.Image:
    """
    Адаптивная бинаризация (черно-белое)
    
    Args:
        image: PIL Image
    
    Returns:
        Бинаризованное изображение
    """
    if not HAS_CV2:
        # Используем простую бинаризацию через PIL
        return image.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
    
    # Конвертируем PIL в numpy array
    img_array = np.array(image.convert('L'))
    
    # Применяем адаптивную пороговую обработку
    binary = cv2.adaptiveThreshold(
        img_array, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Конвертируем обратно в PIL
    return Image.fromarray(binary)


def binarize_otsu(image: Image.Image) -> Image.Image:
    """
    Бинаризация методом Otsu
    
    Args:
        image: PIL Image
    
    Returns:
        Бинаризованное изображение
    """
    if not HAS_CV2:
        # Простая пороговая обработка через PIL
        gray = image.convert('L')
        threshold = gray.size[0] * gray.size[1] // 2  # Примерная оценка порога
        return gray.point(lambda x: 0 if x < 128 else 255, '1')
    
    img_array = np.array(image.convert('L'))
    
    # Порог Otsu
    threshold, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return Image.fromarray(binary)


def denoise(image: Image.Image) -> Image.Image:
    """
    Удаление шума с изображения
    
    Args:
        image: PIL Image
    
    Returns:
        Очищенное от шума изображение
    """
    if not HAS_CV2:
        # Простое сглаживание через PIL
        return image.filter(ImageFilter.MedianFilter(size=3))
    
    img_array = np.array(image)
    
    # Снижение шума
    denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
    
    return Image.fromarray(denoised)


def deskew(image: Image.Image) -> Image.Image:
    """
    Автоматическая коррекция наклона (выравнивание)
    
    Args:
        image: PIL Image
    
    Returns:
        Выровненное изображение
    """
    if not HAS_CV2:
        # Без коррекции наклона, просто возвращаем изображение
        return image
    
    img_array = np.array(image.convert('L'))
    
    # Определение угла наклона через contours
    coords = np.column_stack(np.where(img_array > 0))
    if len(coords) == 0:
        return image
    
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Поворот изображения
    (h, w) = img_array.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img_array, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return Image.fromarray(rotated)


def compose_basic_preprocessing(image: Image.Image) -> Image.Image:
    """
    Базовая композиция методов предобработки
    
    Args:
        image: PIL Image
    
    Returns:
        Обработанное изображение
    """
    # Конвертация в RGB если нужно
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    
    # Увеличение размера если изображение маленькое
    width, height = image.size
    if width < 800 or height < 600:
        scale_factor = max(800 / width, 600 / height)
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Улучшение контраста
    image = enhance_contrast(image, factor=1.5)
    
    # Повышение резкости
    image = enhance_sharpness(image, factor=1.3)
    
    return image


def compose_aggressive_preprocessing(image: Image.Image) -> Image.Image:
    """
    Агрессивная предобработка для сложных документов
    
    Args:
        image: PIL Image
    
    Returns:
        Обработанное изображение
    """
    # Базовая обработка
    image = compose_basic_preprocessing(image)
    
    # Оттенки серого
    image = apply_grayscale(image)
    
    # Адаптивная бинаризация
    image = binarize_adaptive(image)
    
    return image


def compose_advanced_preprocessing(image: Image.Image) -> Image.Image:
    """
    Продвинутая предобработка с коррекцией наклона
    
    Args:
        image: PIL Image
    
    Returns:
        Обработанное изображение
    """
    # Конвертация в RGB если нужно
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    
    # Увеличение размера
    width, height = image.size
    if width < 800 or height < 600:
        scale_factor = max(800 / width, 600 / height)
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Удаление шума
    image = denoise(image)
    
    # Улучшение контраста
    image = enhance_contrast(image, factor=1.8)
    
    # Повышение резкости
    image = enhance_sharpness(image, factor=1.5)
    
    # Коррекция яркости
    image = enhance_brightness(image, factor=1.1)
    
    return image

