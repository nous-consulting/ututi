import logging
from random import Random
import string
from datetime import datetime

from routes.util import redirect_to
from formencode import Schema, validators, Invalid, All, htmlfill
from webhelpers import paginate

from pylons import request, response, c, url, session
from pylons.decorators import validate
from pylons.controllers.util import redirect_to, abort
from pylons.i18n import _
from pylons.templating import render_mako_def

from sqlalchemy.orm.exc import NoResultFound

from ututi.lib.base import BaseController, render
import ututi.lib.helpers as h
from ututi.lib.emails import email_confirmation_request, email_password_reset

from ututi.model import meta, User, Email, PendingInvitation, LocationTag

log = logging.getLogger(__name__)

class UniqueEmail(validators.FancyValidator):

    messages = {
        'empty': _(u"Enter a valid email."),
        'non_unique': _(u"The email already exists."),
        }

    def validate_python(self, value, state):
        if value == '':
            raise Invalid(self.message("empty", state), value, state)
        elif meta.Session.query(Email).filter_by(email=value.strip().lower()).count() > 0:
            raise Invalid(self.message("non_unique", state), value, state)


class PasswordRecoveryForm(Schema):
    allow_extra_fields = False
    email = All(
         validators.String(not_empty=True, strip=True),
         validators.Email()
         )


class PasswordResetForm(Schema):
    allow_extra_fields = True

    msg = {'empty': _(u"Please enter your password to register."),
           'tooShort': _(u"The password must be at least 5 symbols long.")}
    new_password = validators.String(
        min=5, not_empty=True, strip=True, messages=msg)
    repeat_password = validators.String(
        min=5, not_empty=True, strip=True, messages=msg)
    msg = {'invalid': _(u"Passwords do not match."),
           'invalidNoMatch': _(u"Passwords do not match."),
           'empty': _(u"Please enter your password to register.")}
    chained_validators = [validators.FieldsMatch('new_password',
                                                 'repeat_password',
                                                 messages=msg)]


class RegistrationForm(Schema):

    allow_extra_fields = True

    msg = {'missing': _(u"You must agree to the terms of use.")}
    agree = validators.StringBool(messages=msg)

    msg = {'empty': _(u"Please enter your name to register.")}
    fullname = validators.String(not_empty=True, strip=True, messages=msg)

    msg = {'non_unique': _(u"This email has already been used to register.")}
    email = All(validators.Email(not_empty=True, strip=True),
                UniqueEmail(messages=msg, strip=True))

    msg = {'empty': _(u"Please enter your password to register."),
           'tooShort': _(u"The password must be at least 5 symbols long.")}
    new_password = validators.String(
         min=5, not_empty=True, strip=True, messages=msg)
    repeat_password = validators.String(
         min=5, not_empty=True, strip=True, messages=msg)

    msg = {'invalid': _(u"Passwords do not match."),
           'invalidNoMatch': _(u"Passwords do not match."),
           'empty': _(u"Please enter your password to register.")}
    chained_validators = [validators.FieldsMatch('new_password',
                                                 'repeat_password',
                                                 messages=msg)]


def sign_in_user(email):
    session['login'] = email
    session.save()


class HomeController(BaseController):

    def _universities(self, sort_popularity=True):
        unis = meta.Session.query(LocationTag).filter(LocationTag.parent == None).all()
        if sort_popularity:
            unis.sort(key=lambda obj: obj.rating, reverse=True)
        else:
            unis.sort(key=lambda obj: obj.title)
        return unis

    def index(self):
        if c.user is not None:
            redirect_to(controller='profile', action='home')
        else:
            sort = request.params.get('sort', 'popular')
            unis = self._universities(sort == 'popular')
            c.unis = paginate.Page(
                unis,
                page=int(request.params.get('page', 1)),
                items_per_page = 16,
                item_count = len(unis),
                **{'sort': sort}
                )
            if request.params.has_key('js'):
                return render_mako_def('/anonymous_index.mako','universities', unis=c.unis)
            c.teaser = not (request.params.has_key('page') or request.params.has_key('sort'))
            return render('/anonymous_index.mako')

    def banners(self):
        return render('/portlets/banners/%s.mako' % c.lang)

    def about(self):
        return render('/about/%s.mako' % c.lang)

    def terms(self):
        return render('/terms/%s.mako' % c.lang)

    def login(self):
        email = request.POST.get('login')
        password = request.POST.get('password')
        destination = request.params.get('came_from',
                                   url(controller='profile',
                                      action='home'))

        c.header = _('Permission denied!')
        c.message = _('Only registered users can perform this action. Please log in, or register an account on our system.')

        if password is not None:
            user = None
            user = User.authenticate(email, password.encode('utf-8'))
            c.header = _('Wrong username or password!')
            c.message = _('You seem to have entered your username and password wrong, please try again!')

            if user is not None:
                sign_in_user(email)
                redirect_to(str(destination))

        return render('/login.mako')

    def logout(self):
        if 'login' in session:
            del session['login']
        session.save()
        redirect_to(controller='home', action='index')

    @validate(schema=RegistrationForm(), form='register')
    def register(self, hash=None):
        if hasattr(self, 'form_result'):
            fullname = self.form_result['fullname']
            password = self.form_result['new_password']
            email = self.form_result['email'].lower()

            user = User(fullname, password)
            user.emails = [Email(email)]
            user.accepted_terms = datetime.today()
            #all newly registered users are marked when they agree to the terms of use

            meta.Session.add(user)
            meta.Session.commit()
            email_confirmation_request(user, email)

            sign_in_user(email)
            hash = self.form_result.get('hash', None)
            if hash is not None:
                invitation = PendingInvitation.get(hash)
                if invitation is not None and invitation.email == email:
                    invitation.group.add_member(user)
                    meta.Session.delete(invitation)
                    meta.Session.commit()
                    redirect_to(controller='group', action='home', id=invitation.group.group_id)
                elif invitation is None:
                    c.header = _('Invalid invitation!')
                    c.message = _('The invitation link you have followed was either already used or invalid.')
                    return render('/login.mako')
                else:
                    c.email = invitation.email
                    c.header = _('Invalid email!')
                    c.message = _('You can only use the email this invitation was sent for to register.')
                    return render('/login.mako')
            else:
                redirect_to(controller='profile', action='welcome')
        else:
            if hash is not None:
                c.hash = hash
                invitation = PendingInvitation.get(hash)
                if invitation is not None:
                    c.email = invitation.email
                    c.message_class = 'please-register'
                    c.header = _('Please register!')
                    c.message = _('Only registered users can become members of a group, please register first.')
                else:
                    c.header = _('Invalid invitation!')
                    c.message = _('The invitation link you have followed was either already used or invalid.')
                return render('/login.mako')

            return render('anonymous_index.mako')

    def _pswrecovery_form(self):
        return render('home/recoveryform.mako')

    @validate(PasswordRecoveryForm, form='_pswrecovery_form')
    def pswrecovery(self):
        if hasattr(self, 'form_result'):
            email = self.form_result.get('email', None)
            user = User.get(email)
            if user is not None:
                if not user.recovery_key:
                    user.recovery_key = ''.join(Random().sample(string.ascii_lowercase, 8))
                email_password_reset(user, email)
                meta.Session.commit()
                h.flash(_('Password recovery email sent. Please check You inbox.'))
            else:
                h.flash(_('User account not found.'))

        return htmlfill.render(self._pswrecovery_form())

    def _pswreset_form(self):
        return render('home/password_resetform.mako')

    @validate(PasswordResetForm, form='_pswreset_form')
    def recovery(self, key=None):
        try:
            if hasattr(self, 'form_result'):
                key = self.form_result.get('recovery_key', '')
                defaults = {'recovery_key': key}
                user = meta.Session.query(User).filter(User.recovery_key == key).one()
                user.update_password(self.form_result.get('new_password'))
                user.recovery_key = None
                #password reset is actually a confirmation of the email
                user.emails[0].confirmed = True
                meta.Session.commit()
                h.flash(_('Your password has been updated. Welcome back!'))
                sign_in_user(user.emails[0].email)
                redirect_to(controller='profile', action='index')
            else:
                defaults={'recovery_key': key}
                #user = meta.Session.query(User).filter(User.recovery_key == c.key).one()

            return htmlfill.render(self._pswreset_form(), defaults=defaults)
        except NoResultFound:
            abort(404)
