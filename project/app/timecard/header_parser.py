class UserHeader:
    fio: str
    login: str | None

    def __init__(self, fio, login):
        super().__init__()
        self.fio = fio
        self.login = login

    def __repr__(self):
        return f'UserHeader(fio={self.fio}, login={self.login})'


def serialize_name_login(full_name, login):
    return f"{full_name} ({login})"


def deserialize_name_login(serialized_string) -> UserHeader:
    open_bracket_pos = serialized_string.rfind('(')
    close_bracket_pos = serialized_string.rfind(')')

    if open_bracket_pos == -1 or close_bracket_pos == -1 or open_bracket_pos > close_bracket_pos:
        return UserHeader(fio=serialized_string.strip(), login=None)

    login_part = serialized_string[open_bracket_pos + 1:close_bracket_pos]
    full_name_part = serialized_string[:open_bracket_pos].strip()

    return UserHeader(fio=full_name_part.strip(), login=login_part.strip())