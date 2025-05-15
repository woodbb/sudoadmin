# Introduction 
When we moved all of our user linux servers to SSSD, we decided to also move sudo policy there as well.  The issue we had was that there was no good way for our admins to manage the sudoObjects created in our LDAP server (Active Directory), so this web application was written to provide a simple, graphical way for them to create and manage these objects.

Included in this repo are scripts to run docker or podman to spin up a test environment to try the applicaton out yourself.  These will spin up an openldap that will preload a set of user data (the example assumes you will use dc=example,dc=com as your base DN).

# Getting Started

First clone the repository:  

git clone https://github.com/woodbb/sudoadmin

Then you can run podman-start.sh or docker-start.sh, depending on your runtime engine of choice.  You will be prompted for a password, this will be the password you log into the web interface with.  Once the images start, head to http://localhost:8000 and login as admin/<your chosen password>

You can also run this on kubernetes (we do), with a PV created for your flask_sessions (so you can scale the number of pods running the web application out past 1).  You will need to pass in the following environmental variables in your deployment:

LDAPURI

LDAPUSERDN

LDAPPASSWORD

LDAPBASEDN

LDAPSUDOBASE

LDAPPORT

LDAPDOMAIN

LDAPRDN

LDAPAUTH

LDAPGROUPFILTER

LDAPGROUPNAME



To use with SSSD, an example sssd.conf is provided.  You will also need to add "sss" to the sudoers line (before files).

If you find this helpful, you can always buy me a coffee as a thank you :)

https://buymeacoffee.com/woodb
