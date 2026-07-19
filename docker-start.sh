#!/bin/bash
# user defined variables
#

# local development working environment
app_image=woodb/sudoadmin
#app_image=woodnas.local:5005/sudoadmin:latest
ldapserver=ldapserver
ldap_host_port=1389
ldap_container_port=389
# Backwards compatibility: ldapport used elsewhere in script
ldapport=$ldap_host_port
ldapprotocol=ldap://
ldapou=dc=example,dc=com
ldapsudoou=ou=sudo,dc=example,dc=com
ldapuser=admin
ldapuserdn="cn=admin,dc=example,dc=com"
ldapuri=$ldapprotocol$ldapserver:$ldap_container_port
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

# Ensure a user-defined network so container names resolve without --link
network_name=sudopodnet
docker network create $network_name 2>/dev/null || true

# Start ldapserver (do not --rm so logs remain if it crashes)
docker run -dt --name ldapserver --hostname ldapserver \
  --network $network_name \
  --env LDAP_PORT_NUMBER=$ldap_container_port \
  --env LDAP_ROOT="$ldapou" \
  --env LDAP_ADMIN_USERNAME=$ldapuser \
  --env LDAP_ADMIN_PASSWORD=$ldappassword \
  -v $PWD/schemas:/schemas \
  -v $PWD/ldifs:/ldifs \
  -p $ldap_host_port:$ldap_container_port \
  cleanstart/openldap

# Wait briefly for ldapserver to appear running, else show logs and exit
sleep 3
if [ -z "$(docker ps --filter name=ldapserver --filter status=running -q)" ]; then
  echo "ldapserver failed to start; showing recent logs:"
  docker logs --tail 200 ldapserver || true
  echo "Exiting. Fix ldapserver startup and re-run docker-start.sh"
  exit 1
fi


docker run -dt --rm --name sudoadmin \
  --network $network_name \
  --env LDAPSERVER=$ldapserver \
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
  -p 8000:8000 \
  $app_image
