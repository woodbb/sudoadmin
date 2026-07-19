import logging
import ldap
import ldap.filter
from config import ldap_uri, ldap_user, ldap_pass, ldap_sudo_base, retrieveAttributes, searchScope
from forms import filterform

log = logging.getLogger(__name__)


def decodelist(items):
    return [item.decode('utf8') for item in items]


def decode_attr(attrs, key):
    """Decode a bytes LDAP attribute to a list of strings, returning [] if absent."""
    return decodelist(attrs[key]) if key in attrs else []


def truncated_decode(raw_list, limit=2):
    """Decode up to `limit` bytes entries, appending '...' if more exist."""
    decoded = [item.decode('utf8') for item in raw_list[:limit]]
    if len(raw_list) > limit:
        decoded.append('...')
    return decoded


def openLdap():
    l = ldap.initialize(ldap_uri)
    try:
        l.simple_bind_s(ldap_user, ldap_pass)
    except ldap.LDAPError as e:
        log.error("LDAP bind failed: %s", e)
        raise
    return l


def searchldap(l, ldapfilter):
    """Execute a synchronous LDAP search and return a list of (dn, attrs) tuples."""
    results = l.search_s(ldap_sudo_base, searchScope, ldapfilter, retrieveAttributes)
    return [(dn, attrs) for dn, attrs in results if dn is not None]


PAGE_SIZE_CHOICES = (20, 50, 100)
DEFAULT_PAGE_SIZE = PAGE_SIZE_CHOICES[0]


def list_view(page=1, per_page=DEFAULT_PAGE_SIZE, filterhost_arg=''):
    alldata = []
    active_filter = ''
    filtered = False
    filterhost = ''
    form = filterform()

    if form.validate_on_submit() and form.filterhost.data and form.filterhost.data.strip():
        filterhost = ldap.filter.escape_filter_chars(form.filterhost.data.strip())
        ldapfilter = f"(&(objectclass=sudorole)(|(sudohost=ALL)(sudohost=*{filterhost}*)))"
        filtered = True
        active_filter = f'sudoHost={filterhost}'
    elif filterhost_arg and filterhost_arg.strip():
        filterhost = ldap.filter.escape_filter_chars(filterhost_arg.strip())
        ldapfilter = f"(&(objectclass=sudorole)(|(sudohost=ALL)(sudohost=*{filterhost}*)))"
        filtered = True
        active_filter = f'sudoHost={filterhost}'
    else:
        ldapfilter = 'objectclass=sudorole'

    l = openLdap()
    try:
        result_set = searchldap(l, ldapfilter)
        for dn, attrs in result_set:
            try:
                alldata.append({
                    'description': attrs['description'][0].decode('utf8'),
                    'dn': dn,
                    'cn': attrs['cn'][0].decode('utf8'),
                    'hosts': truncated_decode(attrs.get('sudoHost', [])),
                    'users': truncated_decode(attrs.get('sudoUser', [])),
                })
            except Exception as e:
                log.warning("Skipping malformed LDAP entry %s: %s", dn, e)
    finally:
        l.unbind_s()

    sortedalldata = sorted(alldata, key=lambda d: d['description'])

    if per_page not in PAGE_SIZE_CHOICES:
        per_page = DEFAULT_PAGE_SIZE

    total_items = len(sortedalldata)
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    pagedata = sortedalldata[start:end]

    pagination = {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'page_size_choices': PAGE_SIZE_CHOICES,
    }

    return (form, pagedata, filterhost, active_filter, filtered, pagination)


def policyinfo_view(cn):
    """Fetch a single sudo policy by cn. Returns a dict of policy attributes."""
    safe_cn = ldap.filter.escape_filter_chars(cn)
    l = openLdap()
    try:
        result = searchldap(l, f"cn={safe_cn}")
        if not result:
            return {'dn': '', 'cn': cn, 'description': '',
                    'cmdlist': [], 'hostlist': [], 'optionlist': [],
                    'userlist': [], 'runas': []}
        dn, attrs = result[0]
        return {
            'dn':          dn,
            'cn':          cn,
            'description': attrs.get('description', [b''])[0].decode('utf-8'),
            'cmdlist':     decode_attr(attrs, 'sudoCommand'),
            'hostlist':    decode_attr(attrs, 'sudoHost'),
            'optionlist':  decode_attr(attrs, 'sudoOption'),
            'userlist':    decode_attr(attrs, 'sudoUser'),
            'runas':       decode_attr(attrs, 'sudoRunAs'),
        }
    finally:
        l.unbind_s()
