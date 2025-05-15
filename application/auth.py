from flask import Flask
from flask_ldap3_login import LDAP3LoginManager, AuthenticationResponseStatus
from config import *

config = dict()

config['LDAP_HOST'] = ldap_server
config['LDAP_BIND_USER_DN'] = ldap_user
config['LDAP_BIND_USER_PASSWORD'] = ldap_pass
config['LDAP_BASE_DN'] = ldap_base

config['LDAP_GROUP_DN'] = ''

# The attribute for your user schema on LDAP
config['LDAP_USER_RDN_ATTR'] = ldap_rdn

# The Attribute you want users to authenticate to LDAP with.
if ldap_rdn == 'sAMAccountName':
    config['LDAP_USER_LOGIN_ATTR'] = 'cn'
else:
    config['LDAP_USER_LOGIN_ATTR'] = 'uid'

config['LDAP_GROUP_OBJECT_FILTER'] = '(objectclass=*)'



# Setup a LDAP3 Login Manager.
ldap_manager = LDAP3LoginManager()

# Init the manager with the config
ldap_manager.init_config(config)


@auth.verify_password
def verify_password(username, password):
    # Check if the credentials are correct
    response = ldap_manager.authenticate(username, password)
    if response.status == AuthenticationResponseStatus.success:
        return username
    else:
       print(response.status)
