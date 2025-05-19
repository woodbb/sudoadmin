import ldap
from flask import Flask, session, flash, redirect
from config import *
import os

def authenticate(ldap_uri, domain, username, password):
    validated = False
    try:
        l = ldap.initialize(ldap_uri)


        if ldap_auth == 'ad':
            user = f"{username}@{domain}"

        elif username != ldap_user.split(',')[0].split('=')[1]:

                l.simple_bind_s(ldap_user,ldap_pass)
                ldap_result_id = l.search(ldap_base, searchScope, f'({ldap_rdn}={username})', retrieveAttributes)
                result_set = []
                while 1:
                    result_type, result_data = l.result(ldap_result_id, 0)
                    if (result_data == []):
                        break
                    else:
                        if result_type == ldap.RES_SEARCH_ENTRY:
                            result_set.append(result_data)

                if len(result_set) > 0:
                    for x in result_set:
                            user = x[0][0]
        else:
            user = ldap_rdn + '=' + username + ',' + ",".join(["dc=" + dc for dc in domain.split(".")])


    except:
        flash(f"Could not find user information for user {username} in AD!")
        return redirect("/login")
    
    try:
        l.simple_bind_s(user,password)
    except:
        flash(f"Invalid credentials for user {username}")
        return redirect("/login")

    if ldap_group_filter_enabled:
        validated = False

        ldap_result_id = l.search(ldap_sudo_base, searchScope, f'(cn={ldap_group_name})', retrieveAttributes)
        result_set = []
        while 1:
            result_type, result_data = l.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
            
                if len(result_set) > 0:
                    for x in result_set:
                        for member in x[0][1][f'{group_member_attr}']:
                            if member == user:
                                validated = True
                                    
        # raise ValueError(f"{username}: Not in allowed LDAP group!")
        if not validated:
            flash("You are not in an AD group allowed to log in!")
            return redirect("/login")


    session["logged_in"] = True
