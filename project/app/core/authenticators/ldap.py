import logging
import ssl

from fastapi.security import OAuth2PasswordRequestForm
from ldap3 import Tls, Server, Connection, ALL
from ldap3.core.exceptions import LDAPException

from app.core.config import settings


def ldap_search(credentials: OAuth2PasswordRequestForm) -> (str, str, list[str]):
    try:
        # поиск пользователя в AD для того чтобы получить DN
        tls_configuration = Tls(validate=ssl.CERT_REQUIRED) if settings.LDAP_USE_SSL else None
        server = Server(
            settings.LDAP_SERVER,
            port=settings.LDAP_PORT,
            use_ssl=settings.LDAP_USE_SSL,
            tls=tls_configuration,
            get_info=ALL
        )

        # Поиск пользователя в LDAP
        search_conn = Connection(
            server,
            user=settings.LDAP_BIND_DN,
            password=settings.LDAP_BIND_PASSWORD,
            auto_bind=True
        )

        search_filter = settings.LDAP_USER_SEARCH_FILTER.format(username=credentials.username)
        search_conn.search(
            search_base=settings.LDAP_USER_SEARCH_BASE,
            search_filter=search_filter,
            attributes=settings.LDAP_USER_ATTRIBUTES
        )

        if not search_conn.entries:
            logging.error("LDAP AUTH: No entries found")
            return None, None, None

        user_entry = search_conn.entries[0]
        user_dn = user_entry.entry_dn

        # Аутентификация пользователя
        auth_conn = Connection(server, user=user_dn, password=credentials.password)
        if not auth_conn.bind():
            logging.error("LDAP AUTH: Binding failed")
            return None, None, None
        # Извлечение данных пользователя
        login = getattr(user_entry, settings.LDAP_LOGIN_ATTRIBUTE, None).value
        fio = getattr(user_entry, settings.LDAP_FIO_ATTRIBUTE, None).value
        if not login:
            logging.error("LDAP AUTH: Email attribute not found")
            return None, None, None


        logging.error(f"LDAP AUTH: Login is '{login}'")

        if 'memberOf' in user_entry:
            group_dns = user_entry['memberOf'].value
        else:
            group_dns = []

        return login, fio, group_dns
    except LDAPException as e:
        print(f"LDAP error: {e}")
        logging.error(f"LDAP AUTH: {e}")
        return None, None, None
    finally:
        if 'search_conn' in locals() and search_conn.bound:
            search_conn.unbind()