import ldap3
from flask import Flask, session, flash, redirect
from config import *

def authenticate(ldap_uri, domain, username, password):
    validated = False
    if ldap_is_ad:
        user = f"{username}@{domain}"
    else:
        user = ldap_rdn + '=' + username + ',' + ",".join(["dc=" + dc for dc in domain.split(".")])
    server = ldap3.Server(ldap_uri, get_info=ldap3.ALL)
    connection = ldap3.Connection(server, user=user, password=password)

    if not connection.bind():
        flash(f"Invalid credentials for user {username}")
        return redirect("/login")

    if ldap_group_filter_enabled:
        # get user's DN
        connection.search(
            search_base = ldap_base,
            search_filter = f'(samaccountname={username})',
            search_scope='SUBTREE',
            attributes = ['distinguishedName']
        )
        try:
            userdn = connection.entries[0].distinguishedName.values
        except:
            flash(f"Could not find user information for user {username} in AD!")
            return redirect("/login")

        if ldap_group_name != '':
            grouplist = ldap_group_name.split(',')

            for group in grouplist:
                connection.search(
                        search_base = ldap_base,
                        search_filter = f'(&(cn={group})(objectClass=group))',
                        search_scope='SUBTREE',
                        attributes = ['distinguishedName']
                        )

                groupdnlist = connection.entries

                for item in groupdnlist:
                    for dn in item.distinguishedName.values:
                        connection.search(
                            search_base = dn,
                            search_filter = '(objectclass=group)',
                            search_scope='SUBTREE',
                            attributes = ['member']
                        )

                        for entry in connection.entries:
                            for member in entry.member.values:
                                if userdn[0] == member:
                                    validated = True

            # raise ValueError(f"{username}: Not in allowed LDAP group!")
            if not validated:
                flash("You are not in an AD group allowed to log in!")
                return redirect("/login")


    session["logged_in"] = True
