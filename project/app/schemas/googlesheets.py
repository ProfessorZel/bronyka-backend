# app/schemas/googlesheets.py

from pydantic import BaseModel, Field

# Парамеры для отрисовки инструкции
class AccessRequestMeta(BaseModel):
    service_account_email: str
    instructions: str = Field(None)

# Запрос на добавление новой таблицы
class AddSpreadsheetTable(BaseModel):
    url: str

# Запрос на добавление новой таблицы
class SpreadsheetInfo(BaseModel):
    url: str
    title: str
    sheets: list[str]