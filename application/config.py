import os
import ldap
from pathlib import Path


title = "Linux Team Sudo Admin Portal"

ldap_uri = os.environ.get('LDAPURI')
ldap_server = os.environ.get('LDAPSERVER')
ldap_user = os.environ.get('LDAPUSERDN')
if os.path.exists('/app/secret/LDAPPASSWORD'):
    ldappass = Path('/app/secret/LDAPPASSWORD').read_text()
    ldap_pass = ldappass.replace('\n','')
else:
    ldap_pass = os.environ.get('LDAPPASSWORD')
ldap_base = os.environ.get('LDAPBASEDN')
ldap_sudo_base = os.environ.get('LDAPSUDOBASE')

if 'LDAPGROUPFILTER' in os.environ:
    if os.environ.get('LDAPGROUPFILTER').lower() == 'true':
        ldap_group_filter_enabled = True
        ldap_group_name = os.environ.get('LDAPGROUPNAME')
    else:
        ldap_group_filter_enabled = False
        ldap_group_name = ''
else:
    ldap_group_filter_enabled = False
    ldap_group_name = ''

if 'LDAPPORT' in os.environ:
    ldap_uri = ldap_uri + ':' + os.environ.get('LDAPPORT')

if 'LDAPRDN' in os.environ:
    ldap_rdn = os.environ.get('LDAPRDN')
else:
    ldap_rdn = 'cn'

if 'LDAPAUTH' in os.environ:
    ldap_auth = os.environ.get('LDAPAUTH').lower()
else:
    ldap_auth = 'other'

if 'LDAPDOMAIN' in os.environ:
    domain = os.environ.get('LDAPDOMAIN').lower()
else:
    domain = ldap_base.replace('dc=','').replace(',','.')

retrieveAttributes = None
searchScope = ldap.SCOPE_SUBTREE
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

if ldap_auth == 'ad' or ldap_auth == 'activedirectory' or ldap_auth == 'active directory':
    ldap_is_ad = True
else:
    ldap_is_ad = False

if 'LDAPGROUPMEMBERATTR' in os.environ:
    group_member_attr = os.environ.get('LDAPGROUPMEMBERATTR').lower()
else:
    group_member_attr = 'member'
