import logging
import ldap3
import ldap3.core.exceptions
from config import ldap_is_ad, ldap_rdn, ldap_base, ldap_group_filter_enabled, ldap_group_name

log = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when a user fails to authenticate or is not authorized."""


def authenticate(ldap_uri, domain, username, password):
    """Authenticate a user against LDAP/AD and verify group membership.

    Returns True on success. Raises AuthenticationError on failure.
    The caller is responsible for setting session state.
    """
    if ldap_is_ad:
        user = f"{username}@{domain}"
    else:
        user = ldap_rdn + '=' + username + ',' + ','.join(
            f"dc={dc}" for dc in domain.split('.')
        )

    server = ldap3.Server(ldap_uri, get_info=ldap3.ALL)
    connection = ldap3.Connection(server, user=user, password=password)

    try:
        if not connection.bind():
            raise AuthenticationError(f"Invalid credentials for user {username}")

        if ldap_group_filter_enabled:
            _verify_group_membership(connection, username)

        return True
    finally:
        try:
            connection.unbind()
        except Exception:
            pass


def _verify_group_membership(connection, username):
    """Raise AuthenticationError if the user is not in an allowed group."""
    connection.search(
        search_base=ldap_base,
        search_filter=f'(samaccountname={username})',
        search_scope='SUBTREE',
        attributes=['distinguishedName'],
    )
    if not connection.entries:
        raise AuthenticationError(
            f"Could not find user information for {username} in AD"
        )
    userdn = connection.entries[0].distinguishedName.values[0]

    if not ldap_group_name:
        return

    for group in (g.strip() for g in ldap_group_name.split(',')):
        if _user_in_group(connection, userdn, group):
            return

    raise AuthenticationError("You are not in an AD group allowed to log in")


def _user_in_group(connection, userdn, group):
    """Return True if userdn is a (recursive) member of the named group."""
    connection.search(
        search_base=ldap_base,
        search_filter=f'(&(cn={group})(objectClass=group))',
        search_scope='SUBTREE',
        attributes=['distinguishedName'],
    )
    for entry in connection.entries:
        for dn in entry.distinguishedName.values:
            connection.search(
                search_base=dn,
                search_filter='(objectclass=group)',
                search_scope='SUBTREE',
                attributes=['member'],
            )
            for group_entry in connection.entries:
                if userdn in group_entry.member.values:
                    return True
    return False
