# Introduction 
When we moved all of our user linux servers to SSSD, we decided to also move sudo policy there as well.  The issue we had was that there was no good way for our admins to manage the sudoObjects created in our LDAP server (Active Directory), so this web application was written to provide a simple, graphical way for them to create and manage these objects.

Included in this repo are scripts to run docker or podman to spin up a test environment to try the applicaton out yourself.  These will spin up an openldap that will preload a set of user data (the example assumes you will use dc=example,dc=com as your base DN).

# Getting Started

First clone the repository:  

git clone https://github.com/woodbb/sudoadmin

Then you can run podman-start.sh or docker-start.sh, depending on your runtime engine of choice.  You can take the defaults, but you will be prompted for a password - this will be the password you log into the web interface with.  Once the images start, head to http://localhost:8000 and login as 

Username: admin

Password: whatever you entered when the image was started

You can also run this on kubernetes (we do), with a PV created for your flask_sessions (so you can scale the number of pods running the web application out past 1).  

You will need to pass in the following environmental variables to the running container or pod:

LDAPURI: URI of the LDAP server, eg: ldaps://ldap.example.com

LDAPUSERDN: DN of the admin user that will be used to perform queries when other users log in to the ldap server. This account will also be used when looking up and editing LDAP policy, so it will need to have permission to create, edit and delete sudoRole objects in the defined OU for these objects(LDAPSUDOBASE).

LDAPPASSWORD: Password of the admin user above.

LDAPBASEDN: Base DN of the LDAP server that user and group lookups will search through.

LDAPSUDOBASE: Base DN of the OU where sudo objects will be read and written to.

LDAPPORT: Port number the ldap server is listening on.

LDAPGROUPFILTER: (optional) Set to the name of the group of the group the user must be a member of in order to be allowed access to the web interface.

REPLICATION_WAIT_TIME:  (optional, defaults to 0 seconds) If you ldap replication ring takes more than 0 seconds, you can set the time to wait before reloading the page.   This was added because we have a load balancer in front of our LDAP servers and sometimes edits were not reflected on a ldap edit, then read (when another server was talked to).

If using Active Directory:

LDAPAUTH:  (optional) Set to the string "ad" if using Active Directory.  User's loggin in will have @$LDAPDOMAIN appended to the username entered on the login form.  If not passed in, the 

LDAPDOMAIN: (optional) This value will be appended to the username (ie: someuser@example.com) and that value will be used to authenticate against AD.

LDAPRDN: (optional) Set as "sAMAccountName" if using Active Directory (defaults to uid).

* note: the startup scripts (podman-start.sh and docker-start.sh) will mount the app directory inside the container to the local applications directory (for local development).  You can skip this mount if you don't need this.

* note2:  you might want to adjust the platform flag in the docker/podman start scripts, if what is there doesn't work for you (works on my macbook)

If you use AD, you will need to extend the schema with file in the "schemas" directory to support the sudoRole objectclass.  This was not created by me - we extended our AD schema with this file.

To use with SSSD, an example sssd.conf is provided.  You will also need to add "sss" to the sudoers line in your nsswitch.conf.

If you find this helpful, you can always buy me a coffee as a thank you :)

https://buymeacoffee.com/woodb
