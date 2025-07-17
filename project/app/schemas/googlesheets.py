# app/schemas/googlesheets.py

from pydantic import BaseModel, Field

# Парамеры для отрисовки инструкции
class AccessRequestMeta(BaseModel):
    service_account_email: str
    instructions: str = Field(None)

# Запрос на добавление новой таблицы
class ValidateSpreadsheet(BaseModel):
    url: str

# Запрос на добавление новой таблицы
class ValidateSpreadsheetResult(BaseModel):
    url: str
    title: str
    sheets: list[str]


class ConfigSpreadsheet(BaseModel):
    spreadsheet_url: str
    worksheet: str

class ConfigSpreadsheetDB(BaseModel):
    id: int
    spreadsheet_url: str
    worksheet: str
    service_account_email: str