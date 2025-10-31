"""
Парсеры для извлечения данных из различных документов
"""
from .passport_parser import PassportParser
from .migration_card_parser import MigrationCardParser
from .inn_parser import INNParser
from .snils_parser import SNILSParser

__all__ = [
    'PassportParser',
    'MigrationCardParser',
    'INNParser',
    'SNILSParser'
]
