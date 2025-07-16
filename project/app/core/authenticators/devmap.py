import logging

from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings


def devmap_search(credentials: OAuth2PasswordRequestForm) -> (str, str, list[str]):
    usermap = {
        "admin": {
            "password": "admin",
            "fio": "Admin Admin",
            "email": "admin@localhost.com",
            "groups": [settings.LDAP_ADMIN_GROUP,
                       "CN=group3,OU=groups,DC=example,DC=com"],
        },
        "group1": {
            "fio": "Group 1",
            "password": "group1",
            "email": "group1@localhost.com",
            "groups": ["CN=group1,OU=groups,DC=example,DC=com"],
        },
        "group2": {
            "fio": "Group 2",
            "password": "group2",
            "email": "group2@localhost.com",
            "groups": ["CN=group2,OU=groups,DC=example,DC=com"],
        }
    }
    if credentials.username not in usermap:
        logging.info("DEVMAP AUTH: No entries found")
        return None, None, None

    user = usermap[credentials.username]
    if credentials.password != user["password"]:
        logging.info("DEVMAP AUTH: Invalid password")
        return None, None, None

    return user["email"], user["fio"], user["groups"]