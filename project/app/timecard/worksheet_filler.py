import logging

import gspread

from app.timecard.header_parser import UserHeader, deserialize_name_login, serialize_name_login


class WorkScheduleFiller:
    def __init__(self, sheet: gspread.Worksheet):
        """
        Инициализирует заполнитель рабочего расписания

        :param sheet: Объект листа Google Sheets (gspread Worksheet)
        :param date_start_row: Начальная строка поиска дат (по умолчанию 177)
        :param date_end_row: Конечная строка поиска дат (по умолчанию 500)
        :param max_user_groups: Максимальное количество групп пользователей для поиска (по умолчанию 50)
        """
        self.sheet: gspread.Worksheet = sheet

    def fill_schedule(self, user_col: int, date_row: int, plan_arrival, plan_departure):
        """
        Заполняет расписание для указанного пользователя и даты

        :param user_col: Позиция первой ячейки группы ячеек пользователя
        :param date_row: Строка с датой для пользователя
        :param plan_arrival: Время прихода по плану (например "09:00")
        :param plan_departure: Время ухода по плану (например "18:00")
        """


        # Запись данных
        self._update_cells(user_col, date_row, plan_arrival, plan_departure)

    def update_header(self, user_col: int, fio: str, login: str):
        self.sheet.update_cell(1, user_col, serialize_name_login(fio, login))

    def users(self) -> dict[UserHeader, int]:
        """Находит начальный столбец для указанного ФИО"""
        # Получаем значения только нужных ячеек в первой строке
        # Диапазон: столбцы B (2) до последнего расчетного (self.last_fio_col)
        col_values = self.sheet.row_values(1)

        # Перебираем блоки с шагом 5
        users = dict[UserHeader, int]()
        for block_index in range(1, len(col_values), 5):
                users[deserialize_name_login(col_values[block_index])] = block_index + 1
        return users

    def find_date_row(self, date_str) -> int:
        """Находит строку с указанной датой"""
        # Получаем все даты из столбца A в указанном диапазоне
        dates = self.sheet.col_values(1)

        # Перебираем полученные значения
        for idx, value in enumerate(dates):
            if value == date_str:
                return 1 + idx

        raise ValueError(f"Дата '{date_str}' не найдена")

    def _update_cells(self, start_col: int, row: int, arrival, departure):
        """Обновляет ячейки с данными"""
        # Приход-План - первый столбец блока (B/G/L и т.д.)
        # Уход-План - третий столбец блока (D/I/N и т.д.)
        arrival_col = start_col
        departure_col = start_col + 2

        # Обновляем ячейки
        self.sheet.update_cell(row, arrival_col, arrival)
        self.sheet.update_cell(row, departure_col, departure)