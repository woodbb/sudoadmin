#!/bin/bash
# user defined variables
#

# local development working environment
app_image=woodb/sudoadmin
#app_image=woodnas.local:5005/sudoadmin:latest
ldapserver=ldapserver
ldapport=1389
ldapprotocol=ldap://
ldapou=dc=example,dc=com
ldapsudoou=ou=sudo,dc=example,dc=com
ldapuser=admin
ldapuserdn="cn=admin,dc=example,dc=com"
ldapuri=$ldapprotocol$ldapserver:$ldapport
ldaprdn=cn
# ldapauth=ad
domain=example.com

echo "The application image that will be used is: $app_image"
echo "The ldap host that will be used is: $ldapserver"
echo "The ldap port that will be used is: $ldapport"
echo "The ldap URI that will be used is: $ldapuri"
echo "The ldap base OU that will be used is: $ldapou"
echo "The ldap sudo policy OU that will be used is: $ldapsudoou"
echo "The ldap bind user will be: $ldapuser"

read -r -p "Do you wish to override these values? (n) " choice
#if [[ $choice =~ ^(n| ) ]] || [[ -z $choice ]]; then
if [[ $choice =~ ^(y| ) ]]; then

    # Ask user running script for ldap username
    echo "What is the ldap server hostname: "
    read ldapserver

    # Ask user running script for ldap username
    echo "What is the ldap server port: "
    read ldapport

    # Ask user running script for ldap username
    echo "What is the ldap server protocol: "
    read ldapprotocol

    # Ask user running script for ldap base OU
    echo "What is the ldap base OU: "
    read ldapou

    # Ask user running script for ldap sudo OU
    echo "What is the ldap policy OU: "
    read ldapsudoou


    # Ask user running script for ldap username
    echo "What is the ldap bind username: "
    read ldapusername

    echo "What is the ldap user DN: "
    read ldapuserdn
fi

# Ask user running script for ldap password
prompt="What is the ldap bind password: "
while IFS= read -p "$prompt" -r -s -n 1 char
do
    if [[ $char == $'\0' ]]
    then
        break
    fi
    prompt='*'
    ldappassword+="$char"
done
echo

docker run -dt --rm --name ldapserver \
  --env LDAP_PORT_NUMBER=1389 \
  --platform linux/amd64 \
  --env LDAP_ROOT="$ldapou" \
  --env LDAP_ADMIN_USERNAME=$ldapuser \
  --env LDAP_ADMIN_PASSWORD=$ldappassword\
  -v $PWD/schemas:/schemas \
  -v $PWD/ldifs:/ldifs \
  -p 1389:1389 \
  bitnami/openldap:latest

docker run -dt --rm --name sudoadmin \
--env LDAPSERVER=$ldapserver \
--env PORT=$ldapport \
--env LDAPURI=$ldapuri \
--env LDAPUSERNAME=$ldapuser \
--env LDAPPASSWORD=$ldappassword \
--env LDAPBASEDN=$ldapou \
--env LDAPSUDOBASE=$ldapsudoou \
--env LDAPUSERDN=$ldapuserdn \
--env LDAPRDN=$ldaprdn \
--env LDAPDOMAIN=$domain \
--env FLASK_APP=app \
-v $PWD/application:/app/ \
--env FLASK_ENV=development \
--link ldapserver:ldapserver \
-p 8000:8000 \
$app_image
