import ldap3
from flask import Flask, session, flash, redirect
from config import *
import os

def authenticate(ldap_uri, domain, username, password):
    validated = False
    server = ldap3.Server(ldap_uri, get_info=ldap3.ALL)

    if ldap_auth == 'ad':
        user = f"{username}@{domain}"
    else:

        lookup_user_connection = ldap3.Connection(server, user=ldap_user, password=ldap_pass)
        # lookup_user_connection.bind()

        lookup_user_connection.search(
            search_base = ldap_base,
            search_scope = 'SUBTREE',
            search_filter = f'({ldap_rdn}={username})',
            attributes = ['distinguishedName']
        )
        try:
            user = lookup_user_connection.entries[0].distinguishedName.values
        except:
            flash(f"Could not find user information for user {username} in AD!")
            return redirect("/login")

    connection = ldap3.Connection(server, user=user, password=password)

    if not connection.bind():
        flash(f"Invalid credentials for user {username}")
        return redirect("/login")

    if ldap_group_filter_enabled:
        if ldap_auth == 'ad':
            connection.search(
                search_base = ldap_base,
                search_filter = f'(samaccountname={username})',
                search_scope='SUBTREE',
                attributes = ['distinguishedName']
            )
            try:
                userdnpre = connection.entries[0].distinguishedName.values
                userdn = userdnpre[0]
            except:
                flash(f"Could not find user information for user {username} in AD!")
                return redirect("/login")
        else:
            userdn = user

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
                                if userdn == member:
                                    validated = True

            # raise ValueError(f"{username}: Not in allowed LDAP group!")
            if not validated:
                flash("You are not in an AD group allowed to log in!")
                return redirect("/login")


    session["logged_in"] = True
