import os,sys
from flask import Flask, render_template, session, redirect, url_for, session, flash
from wtforms.validators import DataRequired
from config import *
import ldap
import ldap.modlist as modlist
from forms import *

def decodelist(list):
	newlist = []
	for item in list:
		newlist.append(item.decode('utf8'))
	return newlist

def openLdap():
	try:
		l = ldap.initialize(ldap_uri)
		l.simple_bind_s(ldap_user,ldap_pass)
	except ldap.LDAPError as e:
		print(e)

	return l

def searchldap(l,ldapfilter):
	ldap_result_id = l.search(ldap_sudo_base, searchScope, ldapfilter, retrieveAttributes)
	result_set = []
	while 1:
		result_type, result_data = l.result(ldap_result_id, 0)
		if (result_data == []):
			break
		else:
			if result_type == ldap.RES_SEARCH_ENTRY:
				result_set.append(result_data)
	return result_set

def list_view():
	alldata = []
	data = {}
	filter = ''
	filtered = False
	filterhost = ''
	form = filterform()

	if form.validate_on_submit():
		filterhost = form.filterhost.data
		ldapfilter = "(&(objectclass=sudorole)(|(sudohost=ALL)(sudohost=*" + filterhost + "*)))"
		filtered = True
		filter = f'sudoHost={filterhost}'
	else:
		ldapfilter = "objectclass=sudorole"

	l = openLdap()
	result_set = searchldap(l,ldapfilter)
	#return form,result_set
	if len(result_set) > 0:
		for x in result_set:
			try:
				data = {}
				data["description"] = x[0][1]["description"][0].decode('utf8')
				data["dn"] = x[0][0]
				data["cn"] = x[0][1]["cn"][0].decode('utf8')

				hostlist = []
				hostcounter = 0
				for host in x[0][1]["sudoHost"]:
					if hostcounter < 2:
						hostlist.append(host.decode('utf8'))
					if hostcounter == 3:
						hostlist.append('...')
					hostcounter += 1
				data["hosts"] = hostlist

				userlist = []
				usercounter = 0
				for user in x[0][1]["sudoUser"]:
					if usercounter < 2:
						userlist.append(user.decode('utf8'))
					if usercounter == 3:
						userlist.append('...')
					usercounter += 1
				data["users"] = userlist

				alldata.append(data)

			except:
				pass


	sortedalldata = sorted(alldata, key=lambda d: d['description'])

	return (form, sortedalldata, filterhost, filter, filtered)

def policyinfo_view(cn):
	form = filterform()
	editform = edit_form()

	l = openLdap()
	ldapfilter = f"cn={cn}"

	description = ''
	dn = ''
	cmdlist = []
	hostlist = []
	optionlist = []
	userlist = []
	runaslist = []
	s = "sudoCommand"

	result = searchldap(l,ldapfilter)
	if len(result) > 0:
		description = result[0][0][1]["description"][0].decode('utf-8')
		dn = result[0][0][0]
		#cn = result[0][1]["cn"][0].decode('utf8')

		attrs = result[0][0][1]

		if attrs.get('sudoCommand') != None:
			cmdlist = decodelist(result[0][0][1]["sudoCommand"])
		else:
			cmdlist = []

		if attrs.get('sudoHost') != None:
			hostlist = decodelist(result[0][0][1]["sudoHost"])
		else:
			hostlist = []
		
		if attrs.get('sudoOption') != None:
			optionlist = decodelist(result[0][0][1]["sudoOption"])
		else:
			optionlist = []

		if attrs.get('sudoUser') != None:
			userlist = decodelist(result[0][0][1]["sudoUser"])
		else:
			userlist = []
	
		if attrs.get('sudoRunAs') != None:
			runaslist = decodelist(result[0][0][1]["sudoRunAs"])
		else:
			runaslist = []

	return (form, editform, dn, cn, description, cmdlist, hostlist, optionlist, userlist, runaslist)

def edit_policy(cn):
	editform = edit_form()

	l = openLdap()
	ldapfilter = f"cn={cn}"

	if editform.validate_on_submit():
		result = searchldap(l,ldapfilter)
		dn = result[0][0][0]
		mod = []

		userslist = editform.users.data
		users = [*set(userslist)]
		m = (ldap.MOD_REPLACE,'sudoUser',users )
		mod.append( m )

		hostslist = editform.hosts.data
		hosts = [*set(hostslist)]
		m = (ldap.MOD_REPLACE,'sudoHost',hosts )
		mod.append( m )

		cmdslist = editform.cmds.data
		cmds = [*set(cmdslist)]
		m = (ldap.MOD_REPLACE,'sudoCommand',cmds )
		mod.append( m )

		optionslist = editform.options.data
		options = [*set(optionslist)]
		m = (ldap.MOD_REPLACE,'sudoOption',options )
		mod.append( m )

		runaslist = editform.runas.data
		runas = [*set(runaslist)]
		m = (ldap.MOD_REPLACE,'sudoRunAs',runas )
		mod.append( m )

		try:
			l.modify_s(dn, mod)
			return redirect(f"/policyinfo/{cn}")
		except:
			return redirect("/error", code=404)
