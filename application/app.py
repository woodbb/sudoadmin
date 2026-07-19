import os
import logging
import datetime
from functools import wraps
from flask import Flask, render_template, session, redirect, flash, request
from flask_session import Session
from config import ldap_uri, domain
import ldap
import ldap.filter
import ldap.modlist as modlist
from forms import filterform, edit_form
import views
from models import authenticate, AuthenticationError


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)

_secret = os.environ.get('SECRET_KEY')
if not _secret:
    # raise RuntimeError("SECRET_KEY environment variable must be set")
    _secret = 'default_secret_key'
app.config['SECRET_KEY'] = _secret
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        flash("You need to login first")
        return redirect("/login")
    return wrap


def parse_form_list(form_data, key):
    """Deduplicate and encode a multi-value form field, filtering blank entries."""
    items = set(form_data.getlist(key))
    return [i.strip().encode('utf-8') for i in items if i.strip()]


# Ordered mapping of HTML form field names to LDAP sudo attributes
SUDO_FIELDS = [
    ('users[]',   'sudoUser'),
    ('hosts[]',   'sudoHost'),
    ('cmds[]',    'sudoCommand'),
    ('options[]', 'sudoOption'),
    ('runas[]',   'sudoRunAs'),
]


def _policy_context(cn):
    """Build the shared template context for policy view/edit routes."""
    ctx = views.policyinfo_view(cn)
    ctx['form'] = filterform()
    ctx['editform'] = edit_form()
    ctx['request'] = request
    return ctx


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    return redirect("/login")


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', views.DEFAULT_PAGE_SIZE, type=int)
    filterhost_arg = request.args.get('filterhost', '')
    form, alldata, filterhost, active_filter, filtered, pagination = views.list_view(
        page=page, per_page=per_page, filterhost_arg=filterhost_arg)
    return render_template('list.html', form=form, data=alldata,
                           filterhost=filterhost, filter=active_filter,
                           filtered=filtered, pagination=pagination, request=request)


@app.route('/policyinfo/<cn>', methods=['GET'])
@login_required
def policyinfo(cn):
    return render_template('view.html', **_policy_context(cn))


@app.route('/edit/<cn>', methods=['GET'])
@login_required
def policyinfo_edit(cn):
    return render_template('edit.html', **_policy_context(cn))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def policyinfo_add():
    form = filterform()
    editform = edit_form()
    if request.method == 'POST':
        desctxt = editform.desc.data
        dnpre = desctxt.replace(' ', '_')
        dn = f"cn={dnpre},ou=sudo,dc=example,dc=com"

        attrs = {
            'objectclass': [b'top', b'sudorole'],
            'description': desctxt.encode('utf-8'),
        }
        for form_key, ldap_attr in SUDO_FIELDS:
            values = parse_form_list(request.form, form_key)
            if values:
                attrs[ldap_attr] = values

        try:
            l = views.openLdap()
            try:
                l.add_s(dn, modlist.addModlist(attrs))
                log.info("Policy created: %s by %s", dn, session.get('username', 'unknown'))
                return render_template('loading.html', redirect_url=f'/policyinfo/{dnpre}')
            finally:
                l.unbind_s()
        except Exception as e:
            log.error("Failed to create policy %s: %s", dn, e)
            return render_template('error.html', redirect_url=f'error&error={e}')
    return render_template('add.html', form=form, editform=editform)


@app.route('/edit_policy/<cn>', methods=['GET', 'POST'])
@login_required
def policyinfo_do_edit(cn):
    editform = edit_form()

    if request.method == 'POST':
        safe_cn = ldap.filter.escape_filter_chars(cn)
        l = views.openLdap()
        try:
            result = views.searchldap(l, f"cn={safe_cn}")
            dn = result[0][0]
            mod = [(ldap.MOD_REPLACE, 'description', editform.desc.data.encode('utf-8'))]
            for form_key, ldap_attr in SUDO_FIELDS:
                mod.append((ldap.MOD_REPLACE, ldap_attr, parse_form_list(request.form, form_key)))
            try:
                l.modify_s(dn, mod)
                log.info("Policy modified: %s by %s", dn, session.get('username', 'unknown'))
                return render_template('loading.html', redirect_url=f'/policyinfo/{cn}')
            except ldap.LDAPError as e:
                log.error("Failed to modify policy %s: %s", dn, e)
                return redirect("/error", code=404)
        finally:
            l.unbind_s()

    return redirect(f"/edit/{cn}")


@app.route('/delete/<cn>', methods=['GET'])
@login_required
def delete(cn):
    safe_cn = ldap.filter.escape_filter_chars(cn)
    l = views.openLdap()
    try:
        result = views.searchldap(l, f"cn={safe_cn}")
        dn = result[0][0]
        l.delete_s(dn)
        log.info("Policy deleted: %s by %s", dn, session.get('username', 'unknown'))
    except ldap.LDAPError as e:
        log.error("Failed to delete policy cn=%s: %s", cn, e)
    finally:
        l.unbind_s()
    return render_template('loading.html', redirect_url='/')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('debug.html'), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = filterform()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            authenticate(ldap_uri, domain, username, password)
            session['logged_in'] = True
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes=30)
            log.info("Successful login: %s", username)
            return redirect("/")
        except AuthenticationError as err:
            log.warning("Failed login for %s: %s", username, err)
            error = str(err)

    return render_template('login.html', error=error, form=form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
