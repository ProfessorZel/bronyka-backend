import re

import gspread
from fastapi import Depends, HTTPException
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError, SpreadsheetNotFound

from app.core.config import settings


class GoogleSheetsAccessError(Exception):
    """Базовое исключение для ошибок доступа к Google Таблицам"""

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(message)


class GoogleSheetsEditor:
    """Сервис для работы с Google Таблицами"""

    def __init__(self, creds_file: str):
        """
        :param creds_file: Путь к JSON сервисного аккаунта
        """
        try:
            self.creds = Credentials.from_service_account_file(
                creds_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.client = gspread.authorize(self.creds)
            self.email = self.creds.service_account_email
        except Exception as e:
            raise GoogleSheetsAccessError(
                f"Ошибка инициализации сервисного аккаунта: {str(e)}",
                e
            )

    def get_service_account_email(self) -> str:
        """Возвращает email сервисного аккаунта для предоставления доступа"""
        return self.email

    def extract_spreadsheet_id(self, url: str) -> str:
        """Извлекает ID таблицы из URL"""
        patterns = [
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)",
            r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)",
            r"spreadsheets/d/([a-zA-Z0-9-_]+)/edit",
            r"spreadsheets/d/([a-zA-Z0-9-_]+)/",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        if len(url) in (44, 45) and re.match(r'^[a-zA-Z0-9-_]+$', url):
            return url

        raise GoogleSheetsAccessError(
            f"Неверный формат URL или ID таблицы: '{url}'. "
            "Пример правильного формата: https://docs.google.com/spreadsheets/d/ABC123/edit"
        )

    def get_editable_spreadsheet(self, url: str) -> gspread.Spreadsheet:
        """
        Возвращает объект таблицы для редактирования
        В случае ошибки бросает GoogleSheetsAccessError
        """
        try:
            # Извлечение ID таблицы
            spreadsheet_id = self.extract_spreadsheet_id(url)

            # Получение объекта таблицы
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            return spreadsheet

        except SpreadsheetNotFound as e:
            raise GoogleSheetsAccessError(
                f"Таблица с ID '{spreadsheet_id}' не найдена. "
                "Проверьте правильность URL и существование таблицы.",
                e
            ) from e

        except PermissionError as e:
            raise GoogleSheetsAccessError(
                f"Доступ запрещен. Добавьте {self.email} в редакторы таблицы.",
                e
            ) from e

        except APIError as e:
            # Формируем детальное сообщение об ошибке
            status = e.response.status_code if hasattr(e, 'response') else "UNKNOWN"
            message = f"Ошибка Google API ({status}): "

            try:
                error_data = e.response.json().get('error', {})
                message += error_data.get('message', 'Неизвестная ошибка API')
            except:
                message += str(e)

            raise GoogleSheetsAccessError(message, e) from e

        except GoogleSheetsAccessError:
            # Пробрасываем наши кастомные ошибки без изменений
            raise

        except Exception as e:
            raise GoogleSheetsAccessError(
                f"Неожиданная ошибка при доступе к таблице: {str(e)}",
                e
            ) from e


# Правильная реализация Dependency Injection
def get_google_sheets_editor(
        service_account_path: str = "service-account.json"
):
    """
    Dependency factory для создания экземпляра GoogleSheetsEditor
    с кэшированием на уровне приложения
    """
    def _get_cached_editor() -> GoogleSheetsEditor:
        """Создает и кэширует экземпляр редактора"""
        try:
            return GoogleSheetsEditor(creds_file=service_account_path)
        except GoogleSheetsAccessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка инициализации Google Sheets: {str(e)}"
            )

    return _get_cached_editor

configured_get_google_sheets_editor = get_google_sheets_editor(service_account_path=settings.GOOGLE_SERVICE_ACCOUNT_FILE)


# Dependency для получения редактора
async def get_google_editor(
        editor: GoogleSheetsEditor = Depends(configured_get_google_sheets_editor)
) -> GoogleSheetsEditor:
    """FastAPI Dependency для получения редактора таблиц"""
    return editor
