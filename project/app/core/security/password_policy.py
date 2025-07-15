from password_strength import PasswordPolicy

policy = PasswordPolicy.from_names(
    length=7,  # min length: 8
    uppercase=1,  # need min. 2 uppercase letters
    numbers=1,  # need min. 2 digits
    special=1,  # need min. 2 special characters
    nonletters=1,  # need min. 2 non-letter characters (digits, specials, anything)
)

def check_password(password: str) -> bool:
    return len(policy.test(password)) == 0