import os,sys,gc,datetime
from functools import wraps
from flask import Flask, render_template, session, redirect, url_for, session, flash, request
from flask_session import Session
from wtforms.validators import DataRequired
from config import *
import ldap
import ldap.modlist as modlist
from forms import *
import views
from models import authenticate


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
# app.config['PERMANENT_SESSION_LIFETIME'] =  datetime.timedelta(minutes=30)

# @app.before_first_request  # runs before FIRST request (only once)
# def make_session_permanent():
# 	session.permanent = True
# 	app.permanent_session_lifetime = datetime.timedelta(minutes=30)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect("/login")

    return wrap

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect("/login")


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
	form, alldata, filterhost, filter, filtered = views.list_view()
	return render_template('list.html', form=form,
	       					data=alldata, filterhost=filterhost,
							filter=filter,filtered=filtered, request=request)
	#form,data = views.list_view()
	#return render_template("debug.html", data=data,form=form)

@app.route('/policyinfo/<cn>', methods=['GET','POST'])
@login_required
def policyinfo(cn):
	form, editform, dn, cn, description, cmdlist, hostlist, optionlist, userlist, runas = views.policyinfo_view(cn)
	return render_template('view.html', dn=dn, form=form,
							cn=cn, description=description,
							cmdlist=cmdlist, hostlist=hostlist, request=request,
							optionlist=optionlist, userlist=userlist, runas=runas)


@app.route('/edit/<cn>', methods=['GET','POST'])
@login_required
def policyinfo_edit(cn):
	form, editform, dn, cn, description, cmdlist, hostlist, optionlist, userlist, runas = views.policyinfo_view(cn)
	return render_template('edit.html', dn=dn, form=form,
							cn=cn, description=description, editform=editform,
							cmdlist=cmdlist, hostlist=hostlist, request=request,
							optionlist=optionlist, userlist=userlist, runas=runas)


@app.route('/add', methods=['GET','POST'])
@login_required
def policyinfo_add():
	form = filterform()
	editform = edit_form()
	if request.method == "POST":
		attrs = {}
		attrs['objectclass'] = ['top'.encode('utf-8'), 'sudorole'.encode('utf-8')]

		desctxt = editform.desc.data
		dnpre = desctxt.replace(" ","_")
		dn = "cn="+dnpre+","+ldap_sudo_base

		attrs['description'] = desctxt.encode('utf-8')

		try:
			userslist = request.form.getlist('users[]')
			users_dupesgone = [*set(userslist)]
			users_dupesgone = [i for i in users_dupesgone if i]
			users = [x.strip().encode('utf-8') for x in users_dupesgone]
			attrs['sudoUser'] = users
		except:
			pass

		try:
			hostslist = request.form.getlist('hosts[]')
			hosts_dupesgone = [*set(hostslist)]
			hosts_dupesgone = [i for i in hosts_dupesgone if i]
			hosts = [x.strip().encode('utf-8') for x in hosts_dupesgone]
			attrs['sudoHost'] = hosts
		except:
			pass

		try:
			cmdslist = request.form.getlist('cmds[]')
			cmds_dupesgone = [*set(cmdslist)]
			cmds_dupesgone = [i for i in cmds_dupesgone if i]
			cmds = [x.strip().encode('utf-8') for x in cmds_dupesgone]
			attrs['sudoCommand'] = cmds
		except:
			pass

		try:
			optionslist = request.form.getlist('options[]')
			options_dupesgone = [*set(optionslist)]
			options_dupesgone = [i for i in options_dupesgone if i]
			options = [x.strip().encode('utf-8') for x in options_dupesgone]
			attrs['sudoOption'] = options
		except:
			pass

		try:
			runaslist = request.form.getlist('runas[]')
			runas_dupesgone = [*set(runaslist)]
			runas_dupesgone = [i for i in runas_dupesgone if i]
			runas = [x.strip().encode('utf-8') for x in runas_dupesgone]
			attrs['sudoRunAs'] = runas
		except:
			pass

		try:
			l = views.openLdap()
			ldif = modlist.addModlist(attrs)
			l.add_s(dn,ldif)
			# return redirect(f"/policyinfo/{dnpre}")
			redirect_url = '/policyinfo/' + dnpre
			return render_template('loading.html', redirect_url=redirect_url, wait_time=wait_time)
		except Exception as e:
			redirect_url = 'error&error=' + str(e)
			return render_template("error.html", redirect_url=redirect_url, wait_time=wait_time)
	return render_template('add.html', form=form, editform=editform)


@app.route('/edit_policy/<cn>', methods=['GET','POST'])
@login_required
def policyinfo_do_edit(cn):
	editform = edit_form()

	l = views.openLdap()
	ldapfilter = f"cn={cn}"

	if request.method == "POST":
		result = views.searchldap(l,ldapfilter)
		dn = result[0][0][0]
		mod = []

		desctxt = editform.desc.data
		desc = desctxt.encode('utf-8')
		m = (ldap.MOD_REPLACE,'description',desc )
		mod.append( m )

		try:
			userslist = request.form.getlist('users[]')
			users_dupesgone = [*set(userslist)]
			users_dupesgone = [i for i in users_dupesgone if i]
			users = [x.strip().encode('utf-8') for x in users_dupesgone]
			m = (ldap.MOD_REPLACE,'sudoUser',users )
			mod.append( m )
		except:
			pass

		try:
			hostslist = request.form.getlist('hosts[]')
			hosts_dupesgone = [*set(hostslist)]
			hosts_dupesgone = [i for i in hosts_dupesgone if i]
			hosts = [x.strip().encode('utf-8') for x in hosts_dupesgone]
			m = (ldap.MOD_REPLACE,'sudoHost',hosts )
			mod.append( m )
		except:
			pass

		try:
			cmdslist = request.form.getlist('cmds[]')
			cmds_dupesgone = [*set(cmdslist)]
			cmds_dupesgone = [i for i in cmds_dupesgone if i]
			cmds = [x.strip().encode('utf-8') for x in cmds_dupesgone]
			m = (ldap.MOD_REPLACE,'sudoCommand',cmds )
			mod.append( m )
		except:
			pass

		try:
			optionslist = request.form.getlist('options[]')
			options_dupesgone = [*set(optionslist)]
			options_dupesgone = [i for i in options_dupesgone if i]
			options = [x.strip().encode('utf-8') for x in options_dupesgone]
			m = (ldap.MOD_REPLACE,'sudoOption',options )
			mod.append( m )
		except:
			pass

		try:
			runaslist = request.form.getlist('runas[]')
			runas_dupesgone = [*set(runaslist)]
			runas_dupesgone = [i for i in runas_dupesgone if i]
			runas = [x.strip().encode('utf-8') for x in runas_dupesgone]
			m = (ldap.MOD_REPLACE,'sudoRunAs',runas )
			mod.append( m )
		except:
			pass

		try:
			l.modify_s(dn, mod)
			# return redirect(f"/policyinfo/{cn}")
			redirect_url = '/policyinfo/' + cn
			return render_template('loading.html', redirect_url=redirect_url, wait_time=wait_time)
		except:
			return redirect("/error", code=404)

@app.route('/delete/<cn>', methods=['GET'])
@login_required
def delete(cn):
	l = views.openLdap()
	ldapfilter = f"cn={cn}"
	result = views.searchldap(l,ldapfilter)
	dn = result[0][0][0]
	l.delete_s(dn)
	#return redirect("/")
	return render_template('loading.html', redirect_url='/', wait_time=wait_time)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('debug.html'), 404

@app.route("/login", methods=['POST', 'GET'])
def login():
	form = filterform()
	context = {}
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		try:
			authenticate(ldap_uri, domain, username, password)
			session.permanent = True
			app.permanent_session_lifetime = datetime.timedelta(minutes=30)
			return redirect("/")
		except ValueError as err:
			context["error"] = err.message

	return render_template("login.html", **context, form=form)

if __name__ == '__main__':
	# app.jinja_env.auto_reload = True
	# app.config['TEMPLATES_AUTO_RELOAD'] = True
	app.run(host='0.0.0.0', port=8000)
