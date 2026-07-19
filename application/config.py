import os
import ldap
from pathlib import Path


title = "Linux Team Sudo Admin Portal"

# Validate required environment variables at startup
_required = ['LDAPURI', 'LDAPUSERDN', 'LDAPBASEDN', 'LDAPSUDOBASE']
_missing = [k for k in _required if not os.environ.get(k)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")

ldap_uri       = os.environ['LDAPURI']
ldap_server    = os.environ.get('LDAPSERVER', ldap_uri)
ldap_user      = os.environ['LDAPUSERDN']
ldap_base      = os.environ['LDAPBASEDN']
ldap_sudo_base = os.environ['LDAPSUDOBASE']

# Password: mounted secret file takes precedence over env var
_passfile = Path('/app/secret/LDAPPASSWORD')
ldap_pass = _passfile.read_text().strip() if _passfile.exists() else os.environ.get('LDAPPASSWORD', '')

if 'LDAPPORT' in os.environ:
    ldap_uri = ldap_uri.rstrip('/') + ':' + os.environ['LDAPPORT']

ldap_rdn   = os.environ.get('LDAPRDN', 'sAMAccountName')
ldap_auth  = os.environ.get('LDAPAUTH', 'other').lower()
ldap_is_ad = ldap_auth in ('ad', 'activedirectory', 'active directory')

domain = (os.environ['DOMAIN'].lower() if 'DOMAIN' in os.environ
          else ldap_base.replace('dc=', '').replace(',', '.'))

if os.environ.get('LDAPGROUPFILTER', '').lower() == 'true':
    ldap_group_filter_enabled = True
    ldap_group_name = os.environ.get('LDAPGROUPNAME', '')
else:
    ldap_group_filter_enabled = False
    ldap_group_name = ''

retrieveAttributes = None
searchScope = ldap.SCOPE_SUBTREE
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
