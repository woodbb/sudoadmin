#!/bin/bash
# user defined variables
#

# local development working environment
app_image=woodb/sudoadmin
#app_image=woodnas.local:5005/sudoadmin:latest
ldapserver=ldapserver
ldapport=1389
# LDAP inside-container listens on 389; host may map a different port (e.g. 1389)
ldap_container_port=389
ldapprotocol=ldap://
ldapou=dc=example,dc=com
ldapsudoou=ou=sudo,dc=example,dc=com
ldapuser=admin
ldapuserdn="cn=admin,dc=example,dc=com"
# Use the container port for LDAPURI so containers connect to the correct port
ldapuri=$ldapprotocol$ldapserver:$ldap_container_port
ldaprdn=cn
# ldapauth=ad
domain=example.com
# how many seconds to wait for replication to occur, 0 or unset to not wait.
# wait_time=15
wait_time=0

LDAP_DISABLE_SSL=true

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

# Create a user network so container names resolve reliably
network_name=sudopodnet
docker network create "$network_name" 2>/dev/null || true

docker run  -dt --rm --name ldapserver --hostname ldapserver \
  --network "$network_name" \
  -e LDAP_ORGANISATION="Example Org" \
  -e LDAP_DOMAIN="$domain" \
  -e LDAP_BASE_DN="$ldapou" \
  -e LDAP_ADMIN_PASSWORD="$ldappassword" \
  -e LDAP_SEED_INTERNAL_LDIF_PATH="/ldifs" \
  -e LDAP_SEED_INTERNAL_SCHEMA_PATH="/schemas" \
  -e LDAP_RFC2307BIS_SCHEMA="true" \
  -e LDAP_REMOVE_CONFIG_AFTER_SETUP="false" \
  -v $PWD/schemas:/schemas \
  -v $PWD/ldifs:/ldifs \
  -p $ldapport:389 \
   osixia/openldap

docker run -dt --rm --name sudoadmin \
  --network "$network_name" \
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
--env REPLICATION_WAIT_TIME=$wait_time \
--env LDAP_DISABLE_SSL=$LDAP_DISABLE_SSL \
--env FLASK_APP=app \
-v $PWD/application:/app/ \
--env FLASK_ENV=development \
-p 8000:8000 \
$app_image
